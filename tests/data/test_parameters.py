# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for the `SsspParameters` data class."""
import pytest
from aiida.orm import Group
from aiida_sssp.data import SsspParameters
from aiida_sssp.groups import SsspFamily

SSSP_PARAMETERS = {
    'Ar': {
        'cutoff': 10.,
        'dual': 2
    },
    'He': {
        'cutoff': 20.,
        'dual': 4
    },
    'Ne': {
        'cutoff': 30.,
        'dual': 8
    },
}


def test_construction_fail(clear_db, create_sssp_family):
    """Test the various construction arguments that should raise."""
    family = create_sssp_family()

    with pytest.raises(TypeError) as exception:
        SsspParameters(Group(label='sssp'), {})
    assert '`family` is not a stored instance of `SsspFamily`' in str(exception.value)

    with pytest.raises(TypeError) as exception:
        SsspParameters(SsspFamily(label='sssp'), {})
    assert '`family` is not a stored instance of `SsspFamily`' in str(exception.value)

    with pytest.raises(TypeError) as exception:
        SsspParameters(family, [])
    assert 'Got object of type' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        SsspParameters(family, {'Ar': {}, 'He': {}})
    assert 'parameters misses elements present in family' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        SsspParameters(family, {'Ar': {}, 'He': {}, 'Ne': {}, 'Kr': {}})
    assert 'parameters contains elements not present in family' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff': 1, 'dual': 2}, 'He': {'cutoff': 1, 'dual': 2}, 'Ne': {'dual': 2}}
        SsspParameters(family, parameters)
    assert 'entry for element `Ne` is missing the `cutoff` key' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff': 1, 'dual': 2}, 'He': {'cutoff': 1, 'dual': 2}, 'Ne': {'cutoff': 1}}
        SsspParameters(family, parameters)
    assert 'entry for element `Ne` is missing the `dual` key' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff': 1, 'dual': 2}, 'He': {'cutoff': 1, 'dual': 2}, 'Ne': {'cutoff': 's', 'dual': 2}}
        SsspParameters(family, parameters)
    assert '`cutoff` for element `Ne` is not of type int or float' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff': 1, 'dual': 2}, 'He': {'cutoff': 1, 'dual': 2}, 'Ne': {'cutoff': 1, 'dual': 's'}}
        SsspParameters(family, parameters)
    assert '`dual` for element `Ne` is not of type int or float' in str(exception.value)


def test_construction(clear_db, create_sssp_parameters):
    """Test the successful construction."""
    node = create_sssp_parameters()
    assert isinstance(node, SsspParameters)
    assert node.uuid is not None

    node.store()
    assert node.pk is not None


def test_family_label(clear_db, create_sssp_family, create_sssp_parameters):
    """Test the `SsspParameters.family_label` property."""
    family = create_sssp_family()
    node = create_sssp_parameters(family)

    assert node.family_label == family.label


def test_elements(clear_db, create_sssp_parameters):
    """Test the `SsspParameters.elements` property."""
    node = create_sssp_parameters(parameters=SSSP_PARAMETERS)
    assert sorted(SSSP_PARAMETERS.keys()) == sorted(node.elements)


def test_get_cutoffs(clear_db, create_sssp_parameters):
    """Test the `SsspParameters.get_cutoffs` method."""
    node = create_sssp_parameters(parameters=SSSP_PARAMETERS)

    with pytest.raises(KeyError):
        node.get_cutoffs('Br')

    for element, cutoffs in SSSP_PARAMETERS.items():
        assert node.get_cutoffs(element) == cutoffs
