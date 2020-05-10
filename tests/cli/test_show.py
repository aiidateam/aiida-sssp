# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Tests for the command `aiida-sssp show`."""
from aiida_sssp.cli import cmd_show


def test_show(clear_db, run_cli_command, create_sssp_family):
    """Test the `aiida-sssp show` command."""
    result = run_cli_command(cmd_show, raises=SystemExit)
    assert 'Missing argument' in result.output

    family = create_sssp_family()
    result = run_cli_command(cmd_show, [family.label], raises=SystemExit)
    assert '{} does not have an associated `SsspParameters` node'.format(family) in result.output


def test_show_raw(clear_db, run_cli_command, create_sssp_family, create_sssp_parameters):
    """Test the `-r/--raw` option."""
    family = create_sssp_family()
    create_sssp_parameters(uuid=family.uuid).store()

    for option in ['-r', '--raw']:
        result = run_cli_command(cmd_show, [option, family.label])
        assert len(result.output_lines) == len(family.nodes)


def test_show_structure(clear_db, run_cli_command, create_sssp_family, create_sssp_parameters, create_structure):
    """Test the `-s/--structure` option."""
    family = create_sssp_family()
    create_sssp_parameters(uuid=family.uuid).store()
    structure = create_structure(site_kind_names=['Ar', 'He']).store()

    for option in ['-S', '--structure']:
        result = run_cli_command(cmd_show, [option, str(structure.pk), family.label])
        assert 'Ar' in result.output
        assert 'He' in result.output
        assert 'Ne' not in result.output
