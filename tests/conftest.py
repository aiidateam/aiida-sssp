# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Configuration and fixtures for unit test suite."""
import json
import os
import tempfile

import pytest

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']  # pylint: disable=invalid-name


@pytest.fixture
def clear_db(clear_database_before_test):
    """Alias for the `clear_database_before_test` fixture from `aiida-core`."""
    yield


@pytest.fixture
def run_cli_command():
    """Run a `click` command with the given options.

    The call will raise if the command triggered an exception or the exit code returned is non-zero
    """

    def _run_cli_command(command, options=None, raises=None):
        """Run the command and check the result.

        :param options: the list of command line options to pass to the command invocation
        :param raises: optionally an exception class that is expected to be raised
        """
        import traceback
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(command, options or [])

        if raises is not None:
            assert result.exception is not None, result.output
            assert result.exit_code != 0
        else:
            assert result.exception is None, ''.join(traceback.format_exception(*result.exc_info))
            assert result.exit_code == 0, result.output

        result.output_lines = [line.strip() for line in result.output.split('\n') if line.strip()]

        return result

    return _run_cli_command


@pytest.fixture
def uuid():
    """Return a UUID4."""
    import uuid
    return uuid.uuid4()


@pytest.fixture
def filepath_fixtures():
    """Return the absolute filepath to the directory containing the file `fixtures`."""
    return os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture
def filepath_pseudos(filepath_fixtures):
    """Return the absolute filepath to the directory containing the pseudo potential files."""
    return os.path.join(filepath_fixtures, 'pseudos')


@pytest.fixture
def get_upf_data(filepath_pseudos):
    """Return `UpfData` for a given element."""

    def _get_upf_data(element='He'):
        from aiida.plugins import DataFactory
        UpfData = DataFactory('upf')
        return UpfData(os.path.join(filepath_pseudos, '{}.upf'.format(element)))

    return _get_upf_data


@pytest.fixture
def sssp_parameter_metadata():
    """Return default metadata parameters for construction of `SsspParameter`."""
    return {
        'Ar': {
            'cutoff_wfc': 10.,
            'cutoff_rho': 20.,
            'filename': 'Ar.upf',
            'md5': '62a1754735fbb79bac662092d68a8bb9'
        },
        'He': {
            'cutoff_wfc': 20.,
            'cutoff_rho': 80.,
            'filename': 'He.upf',
            'md5': '5e00510a01c97f7faa8d22f18dd6c41f'
        },
        'Ne': {
            'cutoff_wfc': 30.,
            'cutoff_rho': 240.,
            'filename': 'Ne.upf',
            'md5': 'd8afbe89a47929da4eb817a75c908077'
        }
    }


@pytest.fixture
def sssp_parameter_filepath(sssp_parameter_metadata):
    """Return a filepath that contains the parameter metadata."""
    with tempfile.NamedTemporaryFile() as filepath:
        with open(filepath.name, 'w') as handle:
            json.dump(sssp_parameter_metadata, handle)
        yield filepath.name


@pytest.fixture
def create_sssp_family(filepath_pseudos):
    """Create an `SsspFamily` from the `tests/fixtures/pseudos` directory."""

    def factory(label='SSSP/1.1/PBE/efficiency', description='SSSP v1.1 PBE efficiency'):
        from aiida_sssp.groups import SsspFamily
        return SsspFamily.create_from_folder(filepath_pseudos, label, description)

    return factory


@pytest.fixture
def create_sssp_parameters(sssp_parameter_metadata, uuid):
    """Create an `SsspParameters` from the `tests/fixtures/pseudos` directory."""

    def factory(parameters=None, uuid=uuid):
        from aiida_sssp.data import SsspParameters

        if parameters is None:
            parameters = sssp_parameter_metadata

        return SsspParameters(parameters, uuid)

    return factory


@pytest.fixture
def create_structure():
    """Return a `StructureData` instance."""

    def _create_structure(site_kind_names):
        """Return a `StructureData` instance."""
        import re
        from aiida.plugins import DataFactory

        StructureData = DataFactory('structure')

        if not isinstance(site_kind_names, (list, tuple)):
            site_kind_names = (site_kind_names,)

        structure = StructureData(cell=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])

        for kind_name in site_kind_names:
            structure.append_atom(name=kind_name, symbols=re.sub('[0-9]', '', kind_name), position=(0., 0., 0.))

        return structure

    return _create_structure
