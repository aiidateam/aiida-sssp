# -*- coding: utf-8 -*-
# pylint: disable=unused-argument,pointless-statement
"""Tests for the `SsspFamily` class."""
import copy
import distutils.dir_util
import os
import shutil
import tempfile

import pytest

from aiida import orm
from aiida.common import exceptions

from aiida_sssp.data import SsspParameters
from aiida_sssp.groups import SsspFamily


def test_type_string(clear_db):
    """Verify the `_type_string` class attribute is correctly set to the corresponding entry point name."""
    assert SsspFamily._type_string == 'sssp.family'  # pylint: disable=protected-access


def test_construct(clear_db):
    """Test the construction of `SsspFamily` works."""
    family = SsspFamily(label='SSSP').store()
    assert isinstance(family, SsspFamily)

    description = 'SSSP description'
    family = SsspFamily(label='SSSP/v1.1', description=description).store()
    assert isinstance(family, SsspFamily)
    assert family.description == description


def test_load(clear_db):
    """Test that loading of a `SsspFamily` through `load_group` works."""
    family = SsspFamily(label='SSSP').store()
    assert isinstance(family, SsspFamily)

    loaded = orm.load_group(family.pk)
    assert isinstance(family, SsspFamily)
    assert loaded.uuid == family.uuid
    assert loaded.elements == family.elements


def test_add_nodes(clear_db, get_upf_data):
    """Test the `SsspFamily.add_nodes` method."""
    upf_he = get_upf_data(element='He').store()
    upf_ne = get_upf_data(element='Ne').store()
    upf_ar = get_upf_data(element='Ar').store()
    family = SsspFamily(label='SSSP').store()

    with pytest.raises(TypeError):
        family.add_nodes(orm.Data().store())

    with pytest.raises(TypeError):
        family.add_nodes([orm.Data().store(), orm.Data().store()])

    with pytest.raises(TypeError):
        family.add_nodes([upf_ar, orm.Data().store()])

    assert family.count() == 0

    family.add_nodes(upf_he)
    assert family.count() == 1

    # Check that adding a duplicate element raises, and that no extra nodes have been added.
    with pytest.raises(ValueError):
        family.add_nodes([upf_ar, upf_he, upf_ne])
    assert family.count() == 1

    family.add_nodes([upf_ar, upf_ne])
    assert family.count() == 3


def test_elements(clear_db, get_upf_data):
    """Test the `SsspFamily.elements` property."""
    upf_he = get_upf_data(element='He').store()
    upf_ne = get_upf_data(element='Ne').store()
    upf_ar = get_upf_data(element='Ar').store()
    family = SsspFamily(label='SSSP').store()

    family.add_nodes([upf_he, upf_ne, upf_ar])
    assert family.count() == 3
    assert sorted(family.elements) == ['Ar', 'He', 'Ne']


def test_get_pseudo(clear_db, get_upf_data):
    """Test the `SsspFamily.get_pseudo` property."""
    upf_he = get_upf_data(element='He').store()
    upf_ne = get_upf_data(element='Ne').store()
    upf_ar = get_upf_data(element='Ar').store()
    family = SsspFamily(label='SSSP').store()
    family.add_nodes([upf_he, upf_ne, upf_ar])

    with pytest.raises(ValueError) as exception:
        family.get_pseudo('X')

    assert 'family `{}` does not contain pseudo for element'.format(family.label) in str(exception.value)

    element = 'He'
    upf = family.get_pseudo(element)
    assert isinstance(upf, orm.UpfData)
    assert upf.element == element


def test_validate_parameters(clear_db, create_sssp_family, create_sssp_parameters):
    """Test the `SsspFamily.validate_parameters` class method."""
    family = create_sssp_family()
    parameters = create_sssp_parameters()
    metadata = parameters.get_metadata()

    SsspFamily.validate_parameters(list(family.nodes), parameters)

    # Incorrect filename
    incorrect = copy.deepcopy(metadata['Ar'])
    incorrect['filename'] = 'wrong_file_name'
    parameters.set_attribute('Ar', incorrect)

    with pytest.raises(ValueError) as exception:
        SsspFamily.validate_parameters(list(family.nodes), parameters)

    assert 'inconsistent `filename` for element `Ar`' in str(exception.value)

    # Incorrect md5
    incorrect = copy.deepcopy(metadata['Ar'])
    incorrect['md5'] = '123abc'
    parameters.set_attribute('Ar', incorrect)

    with pytest.raises(ValueError) as exception:
        SsspFamily.validate_parameters(list(family.nodes), parameters)

    assert 'inconsistent `md5` for element `Ar`' in str(exception.value)


def test_create_from_folder(clear_db, filepath_pseudos):
    """Test the `SsspFamily.create_from_folder` class method."""
    label = 'SSSP'
    family = SsspFamily.create_from_folder(filepath_pseudos, label)

    assert isinstance(family, SsspFamily)
    assert family.is_stored
    assert family.count() == len(os.listdir(filepath_pseudos))
    assert sorted(family.elements) == sorted([filename.rstrip('.upf') for filename in os.listdir(filepath_pseudos)])

    # Cannot create another family with the same label
    with pytest.raises(ValueError):
        SsspFamily.create_from_folder(filepath_pseudos, label)

    with pytest.raises(TypeError) as exception:
        SsspFamily.create_from_folder(filepath_pseudos, label, description=1)
    assert 'Got object of type' in str(exception.value)


def test_create_from_folder_invalid(clear_db, filepath_pseudos):
    """Test the `SsspFamily.create_from_folder` class method for invalid inputs."""
    label = 'SSSP'

    with tempfile.TemporaryDirectory() as dirpath:

        # Non-existing directory should raise
        with pytest.raises(ValueError) as exception:
            SsspFamily.create_from_folder(os.path.join(dirpath, 'non-existing'), label)

        assert 'is not a directory' in str(exception.value)
        assert SsspFamily.objects.count() == 0
        assert orm.UpfData.objects.count() == 0

        distutils.dir_util.copy_tree(filepath_pseudos, dirpath)

        # Copy an existing pseudo to test that duplicate elements are not allowed
        filename = os.listdir(dirpath)[0]
        filepath = os.path.join(dirpath, filename)
        shutil.copy(filepath, os.path.join(dirpath, filename[:-4] + '2.upf'))

        with pytest.raises(ValueError) as exception:
            SsspFamily.create_from_folder(dirpath, label)

        assert 'contains pseudo potentials with duplicate elements' in str(exception.value)
        assert SsspFamily.objects.count() == 0
        assert orm.UpfData.objects.count() == 0

        # Create an empty folder in the pseudo directory, which is not allowed
        dirpath_sub = os.path.join(dirpath, 'random_sub_folder')
        os.makedirs(dirpath_sub)

        with pytest.raises(ValueError) as exception:
            SsspFamily.create_from_folder(dirpath, label)

        assert 'contains at least one entry that is not a file' in str(exception.value)
        assert SsspFamily.objects.count() == 0
        assert orm.UpfData.objects.count() == 0
        os.rmdir(dirpath_sub)

        # Create a dummy file that does not have a valid UPF format
        with open(filepath, 'w') as handle:
            handle.write('invalid pseudo format')

        with pytest.raises(ValueError) as exception:
            SsspFamily.create_from_folder(dirpath, label)

        assert 'failed to parse' in str(exception.value)
        assert SsspFamily.objects.count() == 0
        assert orm.UpfData.objects.count() == 0


def test_create_from_folder_with_parameters(clear_db, filepath_pseudos, sssp_parameter_filepath):
    """Test the `SsspFamily.create_from_folder` class method when passing a file with pseudo metadata."""
    with pytest.raises(TypeError):
        SsspFamily.create_from_folder(filepath_pseudos, 'SSSP', filepath_parameters={})

    # Test directly from filepath
    family = SsspFamily.create_from_folder(filepath_pseudos, 'SSSP/1.0', filepath_parameters=sssp_parameter_filepath)
    assert isinstance(family, SsspFamily)
    assert family.is_stored

    parameters = family.get_parameters_node()
    assert parameters.family_uuid == family.uuid

    # Test from filelike object
    with open(sssp_parameter_filepath) as handle:
        family = SsspFamily.create_from_folder(filepath_pseudos, 'SSSP/1.1', filepath_parameters=handle)
        assert isinstance(family, SsspFamily)
        assert family.is_stored

        parameters = family.get_parameters_node()
        assert parameters.family_uuid == family.uuid


def test_get_parameters_node(clear_db, create_sssp_family, create_sssp_parameters):
    """Test the `SsspFamily.get_parameters_node` method."""
    family = create_sssp_family()

    with pytest.raises(exceptions.NotExistent):
        family.get_parameters_node()

    parameters = create_sssp_parameters(uuid=family.uuid).store()

    assert isinstance(family.get_parameters_node(), SsspParameters)
    assert family.get_parameters_node().uuid == parameters.uuid


def test_parameters(clear_db, create_sssp_family, create_sssp_parameters):
    """Test the `SsspFamily.parameters` property."""
    family = create_sssp_family()

    with pytest.raises(exceptions.NotExistent):
        family.parameters

    parameters = create_sssp_parameters(uuid=family.uuid).store()

    assert isinstance(family.parameters, dict)
    assert family.parameters == parameters.attributes


def test_get_parameter(clear_db, create_sssp_family, create_sssp_parameters, sssp_parameter_metadata):
    """Test the `SsspFamily.get_parameter` method."""
    family = create_sssp_family()

    with pytest.raises(exceptions.NotExistent):
        family.get_parameter('Ar', 'cutoff')

    parameters = create_sssp_parameters(uuid=family.uuid).store()

    with pytest.raises(KeyError):
        family.get_parameter('Br', 'cutoff')

    with pytest.raises(KeyError):
        family.get_parameter('Ar', 'parameter')

    element = 'Ar'
    key_cutoff_wfc = 'cutoff_wfc'
    key_cutoff_rho = 'cutoff_rho'

    assert family.get_parameter(element, key_cutoff_wfc) == parameters.get_attribute(element)[key_cutoff_wfc]
    assert family.get_parameter(element, key_cutoff_rho) == parameters.get_attribute(element)[key_cutoff_rho]


def test_get_cutoffs(clear_db, create_sssp_family, create_sssp_parameters, create_structure):
    """Test the `SsspFamily.get_cutoffs` method."""
    family = create_sssp_family()
    parameters = create_sssp_parameters(uuid=family.uuid).store().attributes
    structure = create_structure(site_kind_names=['Ar', 'He', 'Ne'])

    with pytest.raises(ValueError):
        family.get_cutoffs(elements=None, structure=None)

    with pytest.raises(ValueError):
        family.get_cutoffs(elements='Ar', structure=structure)

    with pytest.raises(TypeError):
        family.get_cutoffs(elements=False, structure=None)

    with pytest.raises(TypeError):
        family.get_cutoffs(elements=None, structure='Ar')

    expected = parameters['Ar']
    assert family.get_cutoffs(elements='Ar') == (expected['cutoff_wfc'], expected['cutoff_rho'])
    assert family.get_cutoffs(elements=('Ar',)) == (expected['cutoff_wfc'], expected['cutoff_rho'])

    expected = parameters['He']
    assert family.get_cutoffs(elements=('Ar', 'He')) == (expected['cutoff_wfc'], expected['cutoff_rho'])

    expected = parameters['Ne']
    assert family.get_cutoffs(structure=structure) == (expected['cutoff_wfc'], expected['cutoff_rho'])

    # Try structure with multiple kinds with the same element
    expected = parameters['He']
    structure = create_structure(site_kind_names=['He1', 'He2'])
    assert family.get_cutoffs(structure=structure) == (expected['cutoff_wfc'], expected['cutoff_rho'])


def test_get_pseudos(clear_db, create_sssp_family, create_sssp_parameters, create_structure):
    """Test the `SsspFamily.get_pseudos` method."""
    family = create_sssp_family()

    with pytest.raises(TypeError):
        family.get_pseudos('Ar')

    expected = {
        'Ar': family.get_pseudo('Ar'),
        'He': family.get_pseudo('He'),
        'Ne': family.get_pseudo('Ne'),
    }
    structure = create_structure(site_kind_names=['Ar', 'He', 'Ne'])
    assert family.get_pseudos(structure) == expected

    expected = {
        'Ar1': family.get_pseudo('Ar'),
        'Ar2': family.get_pseudo('Ar'),
    }
    structure = create_structure(site_kind_names=['Ar1', 'Ar2'])
    assert family.get_pseudos(structure) == expected
