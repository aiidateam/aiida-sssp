# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for the `SsspFamily` class."""
import distutils.dir_util
import os
import shutil
import tempfile

import pytest

from aiida import orm
from aiida_sssp.groups import SsspFamily


def test_type_string(clear_database):
    """Verify the `_type_string` class attribute is correctly set to the corresponding entry point name."""
    assert SsspFamily._type_string == 'sssp.family'  # pylint: disable=protected-access


def test_construct(clear_database):
    """Test the construction of `SsspFamily` works."""
    family = SsspFamily(label='SSSP').store()
    assert isinstance(family, SsspFamily)

    description = 'SSSP description'
    family = SsspFamily(label='SSSP/v1.1', description=description).store()
    assert isinstance(family, SsspFamily)
    assert family.description == description


def test_add_nodes(clear_database, get_upf_data):
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


def test_elements(clear_database, get_upf_data):
    """Test the `SsspFamily.elements` property."""
    upf_he = get_upf_data(element='He').store()
    upf_ne = get_upf_data(element='Ne').store()
    upf_ar = get_upf_data(element='Ar').store()
    family = SsspFamily(label='SSSP').store()

    family.add_nodes([upf_he, upf_ne, upf_ar])
    assert family.count() == 3
    assert sorted(family.elements) == ['Ar', 'He', 'Ne']


def test_get_pseudo(clear_database, get_upf_data):
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


def test_create_from_folder(clear_database, filepath_pseudos):
    """Test the `SsspFamily.create_from_folder` class method."""
    label = 'SSSP'
    family = SsspFamily.create_from_folder(filepath_pseudos, label)

    assert isinstance(family, SsspFamily)
    assert family.is_stored
    assert family.count() == len(os.listdir(filepath_pseudos))
    assert sorted(family.elements) == sorted([filename.rstrip('.upf') for filename in os.listdir(filepath_pseudos)])

    # Files in `dirpath` not ending in `.upf` or `.UPF` should be ignored and so not raise
    with tempfile.TemporaryDirectory() as dirpath:

        # Copy over the actual pseudos and touch a file with a different file extension
        distutils.dir_util.copy_tree(filepath_pseudos, dirpath)
        open(os.path.join(dirpath, 'none_pseudo.txt'), 'a').close()

        label = 'SSSP-clone'
        family = SsspFamily.create_from_folder(dirpath, label)
        assert family.is_stored
        assert family.count() == len(os.listdir(filepath_pseudos))
        assert sorted(family.elements) == sorted([filename.rstrip('.upf') for filename in os.listdir(filepath_pseudos)])

    # Cannot create another family with the same label
    with pytest.raises(ValueError):
        SsspFamily.create_from_folder(filepath_pseudos, label)

    with pytest.raises(TypeError) as exception:
        SsspFamily.create_from_folder(filepath_pseudos, label, description=1)
    assert 'Got object of type' in str(exception.value)


def test_create_from_folder_invalid(clear_database, filepath_pseudos):
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

        # Create a dummy file that does not have a valid UPF format
        with open(filepath, 'w') as handle:
            handle.write('invalid pseudo format')

        with pytest.raises(ValueError) as exception:
            SsspFamily.create_from_folder(dirpath, label)

        assert 'failed to parse' in str(exception.value)
        assert SsspFamily.objects.count() == 0
        assert orm.UpfData.objects.count() == 0
