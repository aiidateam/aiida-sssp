# -*- coding: utf-8 -*-
"""Commands to install an `SsspFamily`."""
import os
import click

from aiida.cmdline.utils import decorators, echo
from .root import cmd_root
from .utils import attempt, create_family_from_archive

URL_BASE = 'https://archive.materialscloud.org/file/2018.0001'
URL_MAPPING = {
    ('1.1', 'PBE', 'efficiency'): ('v3/SSSP_efficiency_pseudos.tar.gz',),
    ('1.1', 'PBE', 'precision'): ('v3/SSSP_precision_pseudos.tar.gz',)
}  # yapf:disable


@cmd_root.command('install')
@click.option(
    '-v', '--version', type=click.Choice(['1.1']), default='1.1', help='Select the version of the SSSP install.'
)
@click.option(
    '-f', '--functional', type=click.Choice(['PBE']), default='PBE', help='Select the functional of the SSSP install.'
)
@click.option(
    '-p',
    '--protocol',
    type=click.Choice(['efficiency', 'precision']),
    default='precision',
    help='Select the protocol of the SSSP install.'
)
@click.option('-t', '--traceback', is_flag=True, help='Include the stacktrace if an exception is encountered.')
@decorators.with_dbenv()
def cmd_install(version, functional, protocol, traceback):
    """Install a version of the SSSP."""
    import requests
    from tempfile import NamedTemporaryFile
    from aiida.common import exceptions
    from aiida.orm import QueryBuilder
    from aiida_sssp.groups import SsspFamily

    label = '{}/{}/{}/{}'.format('SSSP', version, functional, protocol)
    description = 'SSSP v{} {} {} installed through `aiida-sssp`'.format(version, functional, protocol)

    try:
        QueryBuilder().append(SsspFamily, filters={'label': label}).limit(1).one()
    except exceptions.NotExistent:
        pass
    else:
        echo.echo_critical('SSSP {} {} {} is already installed: {}'.format(version, functional, protocol, label))

    try:
        url_pseudos = os.path.join(URL_BASE, URL_MAPPING[(version, functional, protocol)][0])
    except KeyError:
        echo.echo_critical('No SSSP available for {} {} {}'.format(version, functional, protocol))

    with NamedTemporaryFile(suffix='.tar.gz') as archive:

        with attempt('downloading selected pseudo potentials... ', include_traceback=traceback):
            response = requests.get(url_pseudos)
            response.raise_for_status()
            archive.write(response.content)

        with attempt('unpacking archive and parsing pseudos... ', include_traceback=traceback):
            family = create_family_from_archive(archive.name, label)

        family.description = description
        echo.echo_success('installed `{}` containing {} pseudo potentials'.format(label, family.count()))
