# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for the command `aiida-sssp install`."""
from aiida import orm
from aiida_sssp.cli import cmd_install


def test_install(clear_db, run_cli_command):
    """Test the `aiida-sssp install` command."""
    from aiida_sssp.groups import SsspFamily

    result = run_cli_command(cmd_install)
    assert 'installed `SSSP/' in result.output
    assert orm.QueryBuilder().append(SsspFamily).count() == 1

    result = run_cli_command(cmd_install, raises=SystemExit)
    assert 'is already installed' in result.output


def test_install_fail(clear_db, run_cli_command):
    """Test the `aiida-sssp install` command that should fail."""
    # The efficiency archive currently includes an illegal sub-folder which is not supported yet
    options = ['--protocol', 'efficiency']
    result = run_cli_command(cmd_install, options, raises=SystemExit)
    assert 'contains at least one entry that is not a file' in result.output
