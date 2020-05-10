# -*- coding: utf-8 -*-
"""Subclass of `Group` designed to represent a family of `UpfData` nodes."""
import os

from aiida.common import exceptions
from aiida.common.lang import type_check
from aiida.orm import Group, QueryBuilder
from aiida.plugins import DataFactory

__all__ = ('SsspFamily',)

UpfData = DataFactory('upf')
SsspParameters = DataFactory('sssp.parameters')
StructureData = DataFactory('structure')


class SsspFamily(Group):
    """Group to represent a pseudo potential family.

    Each instance can only contain `UpfData` nodes and can only contain one for each element.
    """

    _node_types = (UpfData,)
    _pseudos = None
    _parameters_node = None
    _parameters = None

    def __repr__(self):
        """Represent the instance for debugging purposes."""
        return '{}<{}>'.format(self.__class__.__name__, self.pk or self.uuid)

    def __str__(self):
        """Represent the instance for human-readable purposes."""
        return '{}<{}>'.format(self.__class__.__name__, self.label)

    @classmethod
    def validate_parameters(cls, pseudos, parameters):
        """Validate the compatibility of a list of pseudos and the given metadata parameters.

        :param pseudos: list of `UpfData` nodes
        :param parameters: an instance of `SsspParameters`
        :raises ValueError: if the `SsspParameters` are not compatible with the list of pseudos
        """
        type_check(pseudos, list)
        type_check(parameters, SsspParameters)

        metadata = parameters.get_metadata()

        for pseudo in pseudos:

            type_check(pseudo, UpfData)
            element = pseudo.element

            try:
                values = metadata[element]
            except KeyError:
                raise ValueError('{} does not contain the element `{}`'.format(parameters, element))

            if values['filename'] != pseudo.filename:
                args = [parameters, 'filename', element, values['filename'], pseudo.filename]
                raise ValueError('{} inconsistent `{}` for element `{}`: {} != {}'.format(*args))

            if values['md5'] != pseudo.md5sum:
                args = [parameters, 'md5', element, values['md5'], pseudo.md5sum]
                raise ValueError('{} inconsistent `{}` for element `{}`: {} != {}'.format(*args))

    @classmethod
    def parse_pseudos_from_directory(cls, dirpath):
        """Parse the UPF files in the given directory into a list of `UpfData` nodes.

        :param dirpath: absolute path to a directory containing pseudo potentials in UPF format.
        :return: list of `UpfData` nodes
        :raises ValueError: if `dirpath` is not a directory or contains anything other than files with .UPF format
        :raises ValueError: if `dirpath` contains multiple pseudo potentials for the same element
        """
        from aiida.common.exceptions import ParsingError
        pseudos = []

        if not os.path.isdir(dirpath):
            raise ValueError('`{}` is not a directory'.format(dirpath))

        for filename in os.listdir(dirpath):
            filepath = os.path.join(dirpath, filename)

            if not os.path.isfile(filepath):
                raise ValueError('dirpath `{}` contains at least one entry that is not a file'.format(dirpath))

            try:
                pseudos.append(UpfData(filepath))
            except ParsingError as exception:
                raise ValueError('failed to parse `{}`: {}'.format(filepath, exception))

        if len(pseudos) != len(set(pseudo.element for pseudo in pseudos)):
            raise ValueError('directory `{}` contains pseudo potentials with duplicate elements'.format(dirpath))

        return pseudos

    @classmethod
    def create_from_folder(cls, dirpath, label, description=None, filepath_parameters=None):
        """Create a new `SsspFamily` from the pseudo potentials contained in a directory.

        .. note:: the directory pointed to by `dirpath` should only contain UPF files. If it contains any folders or any
            of the files cannot be parsed as valid UPF, the method will raise a `ValueError`.

        :param dirpath: absolute path to the folder containing the UPF files.
        :param label: the label to give to the `SsspFamily`, should not already exist
        :param description: optional description to give to the family.
        :param filepath_parameters: a filelike object or filepath to a file containing metadata for `SsspParameters`.
        :return: new stored instance of `SsspFamily`
        :raises ValueError: if a `SsspFamily` already exists with the given name
        """
        type_check(description, str, allow_none=True)

        try:
            cls.objects.get(label=label)
        except exceptions.NotExistent:
            family = SsspFamily(label=label)
        else:
            raise ValueError('the SsspFamily `{}` already exists'.format(label))

        pseudos = cls.parse_pseudos_from_directory(dirpath)

        if filepath_parameters is not None:
            parameters = SsspParameters.create_from_file(filepath_parameters, family.uuid)
            cls.validate_parameters(pseudos, parameters)
            parameters.store()

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

        self.pseudos.update(pseudos)

        super().add_nodes(nodes)

    @property
    def pseudos(self):
        """Return the dictionary of pseudo potentials of this family indexed on the element symbol.

        :return: dictionary of element symbol mapping `UpfData`
        """
        if self._pseudos is None:
            self._pseudos = {upf.element: upf for upf in self.nodes}

        return self._pseudos

    @property
    def elements(self):
        """Return the list of elements of the `UpfData` nodes contained in this family.

        :return: list of element symbols
        """
        return list(self.pseudos.keys())

    def get_pseudo(self, element):
        """Return the `UpfData` for the given element.

        :param element: the element for which to return the corresponding `UpfData` node.
        :return: `UpfData` instance if it exists
        :raises ValueError: if the family does not contain a `UpfData` for the given element
        """
        try:
            pseudo = self.pseudos[element]
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
                self.pseudos[element] = pseudo

        return pseudo

    def get_pseudos(self, structure):
        """Return the mapping of kind names on `UpfData` for the given structure.

        :param structure: the `StructureData` for which to return the corresponding `UpfData` mapping.
        :return: dictionary of kind name mapping `UpfData`
        :raises ValueError: if the family does not contain a `UpfData` for any of the elements of the given structure.
        """
        type_check(structure, StructureData)
        return {kind.name: self.get_pseudo(kind.symbol) for kind in structure.kinds}

    def get_parameters_node(self):
        """Return the associated `SsspParameters` node if it exists.

        :return: the associated `SsspParameters` node containing information like recommended cutoffs
        :raises: `aiida.common.exceptions.NotExistent` if the family does not have associated parameters
        """
        from aiida_sssp.data import SsspParameters

        if self._parameters_node is None:
            filters = {'attributes.{}'.format(SsspParameters.KEY_FAMILY_UUID): self.uuid}
            builder = QueryBuilder().append(SsspParameters, filters=filters)
            self._parameters_node = builder.one()[0]
            self._parameters = self._parameters_node.attributes

        return self._parameters_node

    @property
    def parameters(self):
        """Return the attributes of the associated `SsspParameters` node if it exists.

        :return: a dictionary with all attributes of the associated `SsspParameters` node
        :raises: `aiida.common.exceptions.NotExistent` if the family does not have associated parameters
        """
        if self._parameters is None:
            self.get_parameters_node()

        return self._parameters

    def get_parameter(self, element, parameter):
        """Return a specific parameter for a given element.

        :param element: the element
        :param parameter: the key of the parameter
        :raises: `aiida.common.exceptions.NotExistent` if the family does not have associated parameters
        """
        try:
            element = self.parameters[element]
        except KeyError:
            raise KeyError('family `{}` does not contain the element `{}`'.format(self.label, element))

        try:
            return element[parameter]
        except KeyError:
            raise KeyError('parameter `{}` is not available for element `{}`'.format(parameter, element))

    def get_cutoffs(self, elements=None, structure=None):
        """Return the tuple of recommended cuoff and dual for either the given elements or `StructureData`.

        .. note:: at least one and only one of arguments `elements` or `structure` should be passed.

        :param elements: single or tuple of elements
        :param structure: a `StructureData` node
        :return: tuple of recommended wavefunction and density cutoff
        :raises: `aiida.common.exceptions.NotExistent` if the family does not have associated parameters
        """
        if (elements is None and structure is None) or (elements is not None and structure is not None):
            raise ValueError('at least one and only one of `elements` or `structure` should be defined')

        type_check(elements, (tuple, str), allow_none=True)
        type_check(structure, StructureData, allow_none=True)

        if structure is not None:
            symbols = structure.get_symbols_set()
        elif isinstance(elements, tuple):
            symbols = elements
        else:
            symbols = (elements,)

        cutoffs_wfc = []
        cutoffs_rho = []

        for element in symbols:
            values = self.parameters[element]
            cutoffs_wfc.append(values['cutoff_wfc'])
            cutoffs_rho.append(values['cutoff_rho'])

        return (max(cutoffs_wfc), max(cutoffs_rho))
