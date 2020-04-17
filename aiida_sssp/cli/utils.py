# -*- coding: utf-8 -*-
"""Command line interface utilities."""
from contextlib import contextmanager
from aiida.cmdline.utils import echo

__all__ = ('attempt', 'create_family_from_archive')


@contextmanager
def attempt(message, exception_types=Exception, include_traceback=False):
    """Context manager to be used to wrap statements in CLI that can throw exceptions.

    :param message: the message to print before yielding
    :param include_traceback: boolean, if True, will also print traceback if an exception is caught
    """
    import sys
    import traceback

    echo.echo_info(message, nl=False)

    try:
        yield
    except exception_types as exception:
        echo.echo_highlight(' [FAILED]', color='error', bold=True)
        message = str(exception)
        if include_traceback:
            message += '\n' + ''.join(traceback.format_exception(*sys.exc_info()))
        echo.echo_critical(message)
    else:
        echo.echo_highlight(' [OK]', color='success', bold=True)


def create_family_from_archive(filepath, label, fmt=None):
    """Construct a new `SsspFamily` instance from a tar.gz archive.

    .. warning:: the archive should not contain any subdirectories, but just the pseudos in UPF format.

    :param filepath: absolute filepath to the .tar.gz archive containing the pseudo potentials.
    :param label: the label for the new family
    :param fmt: the format of the archive, if not specified will attempt to guess based on extension of `filepath`
    :return: newly created `SsspFamily`
    :raises OSError: if the archive could not be unpacked or pseudos in it could not be parsed into a `SsspFamily`
    """
    import shutil
    import tempfile

    from aiida_sssp.groups import SsspFamily

    with tempfile.TemporaryDirectory() as dirpath:

        try:
            shutil.unpack_archive(filepath, dirpath, format=fmt)
        except shutil.ReadError as exception:
            raise OSError('failed to unpack the archive `{}`: {}'.format(filepath, exception))

        try:
            family = SsspFamily.create_from_folder(dirpath, label)
        except ValueError as exception:
            raise OSError('failed to parse pseudos from `{}`: {}'.format(dirpath, exception))

    return family
