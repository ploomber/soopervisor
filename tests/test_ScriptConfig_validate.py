from pathlib import Path

import pytest
from soopervisor.script.ScriptConfig import ScriptConfig


def test_error_if_missing_environment_yml(tmp_empty):
    with pytest.raises(FileNotFoundError) as excinfo:
        ScriptConfig.from_path('.').export()

    assert 'Expected a conda "environment.yml"' in str(excinfo.value)


def test_error_if_missing_name_in_environment_yml(tmp_empty):
    Path('environment.yml').touch()

    with pytest.raises(ValueError) as excinfo:
        ScriptConfig.from_path('.').export()

    assert ('Failed to extract the environment name from the '
            'conda "environment.yaml"') == str(excinfo.value)


def test_error_if_missing_pipeline_yaml(tmp_empty):
    Path('environment.yml').write_text('name: some-env')

    with pytest.raises(FileNotFoundError) as excinfo:
        ScriptConfig.from_path('.').export()

    assert 'Expected a "pipeline.yaml"' in str(excinfo.value)


def test_error_if_dag_fails_to_initialize(tmp_empty):
    Path('environment.yml').write_text('name: some-env')
    Path('pipeline.yaml').write_text("{'invalid': 'spec'}")

    with pytest.raises(RuntimeError) as excinfo:
        ScriptConfig.from_path('.').export()

    # check the original traceback is shown (must be a chained exception)
    assert hasattr(excinfo.value, '__cause__')


# Airflow validations