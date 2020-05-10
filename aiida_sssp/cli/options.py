# -*- coding: utf-8 -*-
"""Reusable options for CLI commands."""
import click

from aiida.cmdline.params.options import OverridableOption
from aiida.cmdline.params.types import DataParamType, GroupParamType

__all__ = ('SSSP_FAMILY', 'VERSION', 'FUNCTIONAL', 'PROTOCOL')


def default_sssp_family(ctx, param, identifier):  # pylint: disable=unused-argument
    """Determine the default if no value is specified."""
    from aiida.common import exceptions
    from aiida.orm import QueryBuilder
    from aiida_sssp.groups import SsspFamily

    if identifier is not None:
        return identifier

    try:
        return QueryBuilder().append(SsspFamily).first()[0]
    except exceptions.NotExistent:
        raise click.BadParameter('failed to automatically detect an SSSP family: install it with `aiida-sssp install`.')


SSSP_FAMILY = OverridableOption(
    '-F',
    '--sssp-family',
    type=GroupParamType(sub_classes=('aiida.groups:sssp.family',)),
    required=False,
    callback=default_sssp_family,
    help='Select an SSSP family.'
)

STRUCTURE = OverridableOption(
    '-S',
    '--structure',
    type=DataParamType(sub_classes=('aiida.data:structure',)),
    help='Filter for elements of the given structure.'
)

VERSION = OverridableOption(
    '-v', '--version', type=click.STRING, required=False, help='Select the version of the SSSP configuration.'
)

FUNCTIONAL = OverridableOption(
    '-f', '--functional', type=click.STRING, required=False, help='Select the functional of the SSSP configuration.'
)

PROTOCOL = OverridableOption(
    '-p', '--protocol', type=click.STRING, required=False, help='Select the protocol of the SSSP configuration.'
)
