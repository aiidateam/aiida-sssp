# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for the `SsspParameters` data class."""
import pytest

from aiida.orm import Group
from aiida.common import exceptions
from aiida_sssp.data import SsspParameters

SSSP_PARAMETERS = {
    'Ar': {
        'cutoff_wfc': 10.,
        'cutoff_rho': 20.,
        'filename': 'Ar.upf',
        'md5': '91d02ab07c1'
    },
    'He': {
        'cutoff_wfc': 20.,
        'cutoff_rho': 80.,
        'filename': 'He.upf',
        'md5': '202f5b754e2'
    },
    'Ne': {
        'cutoff_wfc': 30.,
        'cutoff_rho': 240.,
        'filename': 'Ne.upf',
        'md5': '778fbbd8530'
    },
}


def test_construction_fail(clear_db, create_sssp_family):
    """Test the various construction arguments that should raise."""
    family = create_sssp_family()

    with pytest.raises(TypeError) as exception:
        SsspParameters(Group(label='sssp'), {})
    assert '`family` is not an instance of `SsspFamily`' in str(exception.value)

    with pytest.raises(TypeError) as exception:
        SsspParameters(family, [])
    assert 'Got object of type' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_rho': 2., 'filename': 'Ar.upf', 'md5': '91d02ab07c1'}}
        SsspParameters(family, parameters)
    assert 'entry for element `Ar` is missing the `cutoff_wfc` key' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_wfc': 1., 'filename': 'Ar.upf', 'md5': '91d02ab07c1'}}
        SsspParameters(family, parameters)
    assert 'entry for element `Ar` is missing the `cutoff_rho` key' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_wfc': 1., 'cutoff_rho': 2., 'md5': '91d02ab07c1'}}
        SsspParameters(family, parameters)
    assert 'entry for element `Ar` is missing the `filename` key' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_wfc': 1., 'cutoff_rho': 2., 'filename': 'Ar.upf'}}
        SsspParameters(family, parameters)
    assert 'entry for element `Ar` is missing the `md5` key' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_wfc': 'str', 'cutoff_rho': 2., 'filename': 'Ar.upf', 'md5': '91d02ab07c1'}}
        SsspParameters(family, parameters)
    assert '`cutoff_wfc` for element `Ar` is not of type' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_wfc': 1., 'cutoff_rho': 'str', 'filename': 'Ar.upf', 'md5': '91d02ab07c1'}}
        SsspParameters(family, parameters)
    assert '`cutoff_rho` for element `Ar` is not of type' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_wfc': 1., 'cutoff_rho': 2., 'filename': 1., 'md5': '91d02ab07c1'}}
        SsspParameters(family, parameters)
    assert '`filename` for element `Ar` is not of type' in str(exception.value)

    with pytest.raises(ValueError) as exception:
        parameters = {'Ar': {'cutoff_wfc': 1., 'cutoff_rho': 2., 'filename': 'Ar.upf', 'md5': 1}}
        SsspParameters(family, parameters)
    assert '`md5` for element `Ar` is not of type' in str(exception.value)


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

    alternate_label = 'alternate'
    node.family_label = alternate_label
    assert node.family_label == alternate_label

    node.store()

    with pytest.raises(exceptions.ModificationNotAllowed):
        node.family_label = family.label


def test_elements(clear_db, create_sssp_parameters):
    """Test the `SsspParameters.elements` property."""
    node = create_sssp_parameters(parameters=SSSP_PARAMETERS)
    assert sorted(SSSP_PARAMETERS.keys()) == sorted(node.elements)


def test_get_metadata(clear_db, create_sssp_parameters):
    """Test the `SsspParameters.get_metadata` method."""
    node = create_sssp_parameters(parameters=SSSP_PARAMETERS)

    with pytest.raises(KeyError):
        node.get_metadata('Br')

    for element, cutoffs in SSSP_PARAMETERS.items():
        assert node.get_metadata(element) == cutoffs
