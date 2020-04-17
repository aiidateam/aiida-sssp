# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Test the command line interface utilities."""
import distutils.dir_util
import enum
import os
import tarfile
import tempfile

import pytest

from aiida_sssp.cli.utils import attempt, create_family_from_archive


class ArchiveType(enum.IntEnum):
    """Simple enum that determines what type of pseudo archive will be created."""

    VALID = 0
    INVALID_ARCHIVE_FORMAT = 1
    INVALID_ARCHIVE_SUBFOLDER = 2
    INVALID_UPF_FILE = 3


@pytest.fixture
def get_pseudo_archive(filepath_pseudos, request):
    """Create a (potentially invalid) archive with pseudos."""
    archive_type, exception, message = request.param
    suffix = '.tar.gz'

    with tempfile.TemporaryDirectory() as dirpath:

        distutils.dir_util.copy_tree(filepath_pseudos, dirpath)

        if archive_type == ArchiveType.INVALID_ARCHIVE_FORMAT:
            suffix = '.txt'

        if archive_type == ArchiveType.INVALID_ARCHIVE_SUBFOLDER:
            os.makedirs(os.path.join(dirpath, 'subfolder'))

        if archive_type == ArchiveType.INVALID_UPF_FILE:
            open(os.path.join(dirpath, 'corrupt.upf'), 'a').close()

        with tempfile.NamedTemporaryFile(suffix=suffix) as filepath_archive:

            with tarfile.open(filepath_archive.name, 'w:gz') as tar:
                tar.add(dirpath, arcname='.')

            yield filepath_archive.name, exception, message


@pytest.mark.parametrize(
    'get_pseudo_archive', (
        (ArchiveType.VALID, None, None),
        (ArchiveType.INVALID_ARCHIVE_FORMAT, OSError, 'failed to unpack the archive'),
        (ArchiveType.INVALID_ARCHIVE_SUBFOLDER, OSError, 'contains at least one entry that is not a file'),
        (ArchiveType.INVALID_UPF_FILE, OSError, 'failed to parse'),
    ),
    indirect=True
)
def test_create_family_from_archive(clear_db, get_pseudo_archive):
    """Test the `create_family_from_archive` utility function."""
    from aiida_sssp.groups import SsspFamily

    filepath_archive, exception, message = get_pseudo_archive

    label = 'SSSP/0.0/LDA/extreme'

    if exception is not None:
        with pytest.raises(exception) as exception:
            create_family_from_archive(filepath_archive, label)
        assert message in str(exception.value)
    else:
        family = create_family_from_archive(filepath_archive, label)
        assert isinstance(family, SsspFamily)
        assert family.label == label
        assert family.count() != 0


def test_attempt_sucess(capsys):
    """Test the `attempt` utility function."""
    message = 'some message'

    with attempt(message):
        pass

    captured = capsys.readouterr()
    assert captured.out == 'Info: {} [OK]\n'.format(message)
    assert captured.err == ''


def test_attempt_exception(capsys):
    """Test the `attempt` utility function when exception is raised."""
    message = 'some message'
    exception = 'run-time-error'

    with pytest.raises(SystemExit):
        with attempt(message):
            raise RuntimeError(exception)

    captured = capsys.readouterr()
    assert captured.out == 'Info: {} [FAILED]\n'.format(message)
    assert captured.err == 'Critical: {}\n'.format(exception)


def test_attempt_exception_traceback(capsys):
    """Test the `attempt` utility function when exception is raised and `include_traceback=True`."""
    message = 'some message'
    exception = 'run-time-error'

    with pytest.raises(SystemExit):
        with attempt(message, include_traceback=True):
            raise RuntimeError(exception)

    captured = capsys.readouterr()
    assert captured.out == 'Info: {} [FAILED]\n'.format(message)
    assert captured.err.startswith('Critical: {}\n'.format(exception))
    assert 'Traceback' in captured.err
