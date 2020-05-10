# -*- coding: utf-8 -*-
"""Commands to install an `SsspFamily`."""
import os

import click

from aiida.cmdline.utils import decorators, echo
from .root import cmd_root
from .utils import attempt, create_family_from_archive
from . import options

URL_BASE = 'https://archive.materialscloud.org/file/2018.0001/v4/'
URL_MAPPING = {
    ('1.0', 'PBE', 'efficiency'): 'SSSP_1.0_PBE_efficiency',
    ('1.0', 'PBE', 'precision'): 'SSSP_1.0_PBE_precision',
    ('1.1', 'PBE', 'efficiency'): 'SSSP_1.1_PBE_efficiency',
    ('1.1', 'PBE', 'precision'): 'SSSP_1.1_PBE_precision',
    ('1.1', 'PBEsol', 'efficiency'): 'SSSP_1.1_PBEsol_efficiency',
    ('1.1', 'PBEsol', 'precision'): 'SSSP_1.1_PBEsol_precision',
}


@cmd_root.command('install')
@options.VERSION(type=click.Choice(['1.0', '1.1']), default='1.1')
@options.FUNCTIONAL(type=click.Choice(['PBE', 'PBEsol']), default='PBE')
@options.PROTOCOL(type=click.Choice(['efficiency', 'precision']), default='efficiency')
@click.option('-t', '--traceback', is_flag=True, help='Include the stacktrace if an exception is encountered.')
@decorators.with_dbenv()
def cmd_install(version, functional, protocol, traceback):
    """Install a configuration of the SSSP."""
    # pylint: disable=too-many-locals
    import requests
    import tempfile

    from aiida.common import exceptions
    from aiida.common.files import md5_file
    from aiida.orm import QueryBuilder

    from aiida_sssp import __version__
    from aiida_sssp.groups import SsspFamily

    label = '{}/{}/{}/{}'.format('SSSP', version, functional, protocol)
    description = 'SSSP v{} {} {} installed with aiida-sssp v{}'.format(version, functional, protocol, __version__)

    try:
        QueryBuilder().append(SsspFamily, filters={'label': label}).limit(1).one()
    except exceptions.NotExistent:
        pass
    else:
        echo.echo_critical('SSSP {} {} {} is already installed: {}'.format(version, functional, protocol, label))

    try:
        url_base = os.path.join(URL_BASE, URL_MAPPING[(version, functional, protocol)])
    except KeyError:
        echo.echo_critical('No SSSP available for {} {} {}'.format(version, functional, protocol))

    with tempfile.TemporaryDirectory() as dirpath:

        url_archive = url_base + '.tar.gz'
        url_metadata = url_base + '.json'

        filepath_archive = os.path.join(dirpath, 'archive.tar.gz')
        filepath_metadata = os.path.join(dirpath, 'metadata.json')

        with attempt('downloading selected pseudo potentials archive... ', include_traceback=traceback):
            response = requests.get(url_archive)
            response.raise_for_status()
            with open(filepath_archive, 'wb') as handle:
                handle.write(response.content)
                handle.flush()
                description += '\nArchive pseudos md5: {}'.format(md5_file(filepath_archive))

        with attempt('downloading selected pseudo potentials metadata... ', include_traceback=traceback):
            response = requests.get(url_metadata)
            response.raise_for_status()
            with open(filepath_metadata, 'wb') as handle:
                handle.write(response.content)
                handle.flush()
                description += '\nPseudo metadata md5: {}'.format(md5_file(filepath_metadata))

        with attempt('unpacking archive and parsing pseudos... ', include_traceback=traceback):
            family = create_family_from_archive(label, filepath_archive, filepath_metadata)

        family.description = description
        echo.echo_success('installed `{}` containing {} pseudo potentials'.format(label, family.count()))
