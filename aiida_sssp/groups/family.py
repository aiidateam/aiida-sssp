# -*- coding: utf-8 -*-
"""Subclass of `Group` designed to represent a family of `UpfData` nodes."""
import os

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm import Group, QueryBuilder
from aiida.plugins import DataFactory

__all__ = ('SsspFamily',)

UpfData = DataFactory('upf')


class SsspFamily(Group):
    """Group to represent a pseudo potential family.

    Each instance can only contain `UpfData` nodes and can only contain one for each element.
    """

    _node_types = (UpfData,)

    def __init__(self, *args, **kwargs):
        """Initialize the instance with an empty pseudo potential cache."""
        super().__init__(*args, **kwargs)
        self._pseudos = {}

    def __repr__(self):
        """Represent the instance for debugging purposes."""
        return '{}<{}>'.format(self.__class__.__name__, self.pk or self.uuid)

    def __str__(self):
        """Represent the instance for human-readable purposes."""
        return '{}<{}>'.format(self.__class__.__name__, self.label)

    @classmethod
    def create_from_folder(cls, dirpath, label, description=None):
        """Create a new `SsspFamily` from the pseudo potentials contained in a directory.

        :param dirpath: absolute path to the folder containing the UPF files.
        :param label: the label to give to the `SsspFamily`, should not already exist
        :param description: optional description to give to the family.
        :return: new instance of `SsspFamily`
        :raises ValueError: if a `SsspFamily` already exists with the given name
        """
        from aiida.common.exceptions import ParsingError

        type_check(description, str, allow_none=True)

        try:
            cls.objects.get(label=label)
        except exceptions.NotExistent:
            family = SsspFamily(label=label)
        else:
            raise ValueError('the SsspFamily `{}` already exists'.format(label))

        pseudos = []

        if not os.path.isdir(dirpath):
            raise ValueError('`{}` is not a directory'.format(dirpath))

        for filename in os.listdir(dirpath):
            filepath = os.path.join(dirpath, filename)

            if not (filename.endswith('.upf') or filename.endswith('.UPF')):
                continue

            try:
                pseudos.append(UpfData(filepath))
            except ParsingError as exception:
                raise ValueError('failed to parse `{}`: {}'.format(filepath, exception))

        if len(pseudos) != len(set(pseudo.element for pseudo in pseudos)):
            raise ValueError('directory `{}` contains pseudo potentials with duplicate elements'.format(dirpath))

        if description is not None:
            family.description = description

        # Only store the `Group` and the `UpfData` nodes now, such that we don't have to worry about the clean up in
        # the case that an exception is raised during creating them.
        family.store()
        family.add_nodes([upf.store() for upf in pseudos])

        return family

    def add_nodes(self, nodes):
        """Add a node or a set of nodes to the family.

        .. note: Each family instance can only contain a single `UpfData` for each element.

        :param nodes: a single `Node` or a list of `Nodes` of type `SsspFamily._node_types`
        :raises TypeError: if nodes are not an instance or list of instance of `SsspFamily._node_types`
        :raises ValueError: if any of the elements of the nodes already exist in this family
        """
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]

        if any([not isinstance(node, self._node_types) for node in nodes]):
            raise TypeError('only nodes of type `{}` can be added'.format(self._node_types))

        pseudos = {}

        # Check for duplicates before adding any pseudo to the internal cache
        for upf in nodes:
            if upf.element in self.elements:
                raise ValueError('element `{}` already present in this family'.format(upf.element))
            pseudos[upf.element] = upf

        self._pseudos.update(pseudos)

        super().add_nodes(nodes)

    @property
    def elements(self):
        """Return the list of elements of the `UpfData` nodes contained in this family.

        :return: list of element symbols
        """
        if self._pseudos is None:
            self._pseudos = {upf.element: upf for upf in self.nodes}

        return list(self._pseudos.keys())

    def get_pseudo(self, element):
        """Return the `UpfData` for the given element.

        :param element: the element for which to return the corresponding `UpfData` node.
        :return: `UpfData` instance if it exists
        :raises ValueError: if the family does not contain a `UpfData` for the given element
        """
        try:
            pseudo = self._pseudos[element]
        except KeyError:
            builder = QueryBuilder().append(
                SsspFamily, filters={'id': self.pk}, tag='group').append(
                self._node_types, filters={'attributes.element': element}, with_group='group')  # yapf:disable

            try:
                pseudo = builder.one()[0]
            except exceptions.MultipleObjectsError:
                raise RuntimeError('family `{}` contains multiple pseudos for `{}`'.format(self.label, element))
            except exceptions.NotExistent:
                raise ValueError('family `{}` does not contain pseudo for element `{}`'.format(self.label, element))
            else:
                self._pseudos[element] = pseudo

        return pseudo
