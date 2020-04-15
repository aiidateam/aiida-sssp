# -*- coding: utf-8 -*-
"""Subclass of `Data` to represent parameters for a specific `SsspFamily`."""
from aiida import orm
from aiida.common.lang import type_check

__all__ = ('SsspParameters',)


class SsspParameters(orm.Data):
    """Subclass of `Data` to represent parameters for a specific `SsspFamily`."""

    KEY_FAMILY_LABEL = 'family_label'

    def __init__(self, family, parameters, **kwargs):
        """Construct a new instance of cutoff parameters for an `SsspFamily`.

        The family has to be a stored instance of `SsspFamily`. The `parameters` should be a dictionary of elements, the
        set of which matches exactly the set of elements in the family. Each element should provide a `cutoff` and a
        `dual`.

        :param family: a stored instance of `SsspFamily` to which the parameters should apply.
        :param parameters: the dictionary with parameters of a given `SsspFamily`
        """
        from aiida_sssp.groups import SsspFamily
        super().__init__(**kwargs)

        if not isinstance(family, SsspFamily) or not family.is_stored:
            raise TypeError('`family` is not a stored instance of `SsspFamily`.')

        type_check(parameters, dict)

        elements_family = set(family.elements)
        elements_cutoff = set(parameters.keys())

        if len(elements_family) > len(elements_cutoff):
            elements_diff = elements_family.difference(elements_cutoff)
            raise ValueError('parameters misses elements present in family: {}'.format(', '.join(elements_diff)))

        if len(elements_family) < len(elements_cutoff):
            elements_diff = elements_cutoff.difference(elements_family)
            raise ValueError('parameters contains elements not present in family: {}'.format(', '.join(elements_diff)))

        for element, values in parameters.items():
            if 'cutoff' not in values:
                raise ValueError('entry for element `{}` is missing the `cutoff` key'.format(element))

            if 'dual' not in values:
                raise ValueError('entry for element `{}` is missing the `dual` key'.format(element))

            if not isinstance(values['cutoff'], (int, float)):
                raise ValueError('`cutoff` for element `{}` is not of type int or float'.format(element))

            if not isinstance(values['dual'], (int, float)):
                raise ValueError('`dual` for element `{}` is not of type int or float'.format(element))

        self.set_attribute_many(parameters)
        self.set_attribute(self.KEY_FAMILY_LABEL, family.label)

    def __repr__(self):
        """Represent the instance for debugging purposes."""
        return '{}<{}>'.format(self.__class__.__name__, self.pk or self.uuid)

    def __str__(self):
        """Represent the instance for human-readable purposes."""
        return self.__repr__()

    @property
    def family_label(self):
        """Return the label of the `SsspFamily` to which this parameters instance is associated.

        :return: the label of the associated `SsspFamily`
        """
        return self.get_attribute(self.KEY_FAMILY_LABEL)

    @property
    def elements(self):
        """Return the set of elements defined for this instance.

        :return: set of elements
        """
        return set(self.attributes_keys()) - {self.KEY_FAMILY_LABEL}

    def get_cutoffs(self, element):
        """Return the recommended cutoffs for the given element.

        :raises KeyError: if the element is not defined for this instance
        """
        try:
            return self.get_attribute(element)
        except AttributeError:
            raise KeyError('element `{}` is not defined for `{}`'.format(element, self))
