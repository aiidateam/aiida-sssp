# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for the command `aiida-sssp install`."""
from aiida import orm
from aiida_sssp.cli import cmd_install


def test_install(clear_db, run_cli_command):
    """Test the `aiida-sssp install` command."""
    from aiida_sssp import __version__
    from aiida_sssp.data import SsspParameters
    from aiida_sssp.groups import SsspFamily

    result = run_cli_command(cmd_install)
    assert 'installed `SSSP/' in result.output
    assert orm.QueryBuilder().append(SsspFamily).count() == 1

    family = orm.QueryBuilder().append(SsspFamily).one()[0]
    assert 'SSSP v1.1 PBE efficiency installed with aiida-sssp v{}'.format(__version__) in family.description
    assert 'Pseudo metadata md5: 0d5d6c2c840383c7c4fc3a99b5dc3001' in family.description
    assert 'Archive pseudos md5: 4803ce9fd1d84c777f87173cd4a2de33' in family.description

    parameters = family.get_parameters_node()
    assert isinstance(parameters, SsspParameters)
    assert parameters.family_uuid == family.uuid

    result = run_cli_command(cmd_install, raises=SystemExit)
    assert 'is already installed' in result.output
