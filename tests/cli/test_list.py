# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for the command `aiida-sssp install`."""
from aiida_sssp.cli import cmd_list


def test_list(clear_db, run_cli_command, create_sssp_family):
    """Test the `aiida-sssp list` command."""
    result = run_cli_command(cmd_list)
    assert 'SSSP has not yet been installed: use `aiida-sssp install` to install it.' in result.output

    family = create_sssp_family()
    result = run_cli_command(cmd_list)

    assert family.label in result.output
    assert family.description in result.output
