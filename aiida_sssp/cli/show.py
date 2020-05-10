# -*- coding: utf-8 -*-
"""Commands to show details of particular `SsspFamily` instances."""
import click

from aiida.common import exceptions
from aiida.cmdline.params import options as options_core
from aiida.cmdline.params import types
from aiida.cmdline.utils import decorators, echo

from .root import cmd_root
from . import options


@cmd_root.command('show')
@click.argument('sssp_family', type=types.GroupParamType(sub_classes=('aiida.groups:sssp.family',)))
@options.STRUCTURE()
@options_core.RAW()
@decorators.with_dbenv()
def cmd_show(sssp_family, structure, raw):
    """Show details of a particular SSSP_FAMILY."""
    from tabulate import tabulate

    rows = []

    if structure:
        iterator = sssp_family.get_pseudos(structure).values()
    else:
        iterator = sssp_family.nodes

    try:
        sssp_family.get_parameters_node()
    except exceptions.NotExistent:
        echo.echo_critical('{} does not have an associated `SsspParameters` node'.format(sssp_family))

    for upf in iterator:
        rows.append([upf.element, upf.filename] + list(sssp_family.get_cutoffs(elements=(upf.element,))))

    headers = ['Element', 'Pseudo', 'Cutoff wfc', 'Cutoff rho']

    if raw:
        echo.echo(tabulate(sorted(rows), tablefmt='plain'))
    else:
        echo.echo(tabulate(sorted(rows), headers=headers))
