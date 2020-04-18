# -*- coding: utf-8 -*-
"""Commands to list instances of `SsspFamily`."""
from aiida.cmdline.utils import decorators, echo

from aiida_sssp.groups import SsspFamily
from .root import cmd_root


@cmd_root.command('list')
@decorators.with_dbenv()
def cmd_list():
    """List all installed versions of the SSSP."""
    from tabulate import tabulate
    from aiida.orm import QueryBuilder

    rows = []
    headers = ['Label', 'Description', '# Pseudos']

    for [group] in QueryBuilder().append(SsspFamily).iterall():
        rows.append((group.label, group.description, group.count()))

    if rows:
        echo.echo(tabulate(rows, headers=headers))
    else:
        echo.echo_info('SSSP has not yet been installed: use `aiida-sssp install` to install it.')
