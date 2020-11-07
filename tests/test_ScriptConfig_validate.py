from pathlib import Path

import yaml
import pytest
from soopervisor.base.config import ScriptConfig
from soopervisor.airflow import validate

# TODO: re organize this tests file


def test_error_if_missing_environment_yml(tmp_empty):
    with pytest.raises(FileNotFoundError) as excinfo:
        ScriptConfig.from_path('.')

    assert 'Expected a conda "environment.yml"' in str(excinfo.value)


def test_error_if_missing_name_in_environment_yml(tmp_empty):
    Path('environment.yml').touch()

    with pytest.raises(ValueError) as excinfo:
        ScriptConfig.from_path('.')

    assert ('Failed to extract the environment name from the '
            'conda "environment.yaml"') == str(excinfo.value)


def test_error_if_missing_pipeline_yaml(tmp_empty):
    Path('environment.yml').write_text('name: some-env')

    with pytest.raises(FileNotFoundError) as excinfo:
        ScriptConfig.from_path('.')

    assert 'Expected a "pipeline.yaml"' in str(excinfo.value)


def test_error_if_dag_fails_to_initialize(tmp_empty):
    Path('environment.yml').write_text('name: some-env')
    Path('pipeline.yaml').write_text("{'invalid': 'spec'}")

    with pytest.raises(RuntimeError) as excinfo:
        ScriptConfig.from_path('.')

    # check the original traceback is shown (must be a chained exception)
    assert hasattr(excinfo.value, '__cause__')


# Airflow validations, TODO: script to AirflowConfig


def test_error_if_missing_env_airflow_yaml(tmp_sample_project):
    d, dag = ScriptConfig.from_path('.', return_dag=True)
    Path('env.airflow.yaml').unlink()

    with pytest.raises(FileNotFoundError) as excinfo:
        validate.pre(d, dag)

    assert 'Expected an "env.airflow.yaml"' in str(excinfo.value)


def test_error_if_env_airflow_yaml_is_dir(tmp_sample_project):
    d, dag = ScriptConfig.from_path('.', return_dag=True)

    Path('env.airflow.yaml').unlink()
    Path('env.airflow.yaml').mkdir()

    with pytest.raises(FileNotFoundError) as excinfo:
        validate.pre(d, dag)

    assert 'Expected an "env.airflow.yaml", but got a directory' in str(
        excinfo.value)


@pytest.mark.parametrize('products', [
    '{{here}}/output',
    '{{here}}/subfolder/output',
])
def test_error_if_products_inside_project_root(products, tmp_sample_project):
    d, dag = ScriptConfig.from_path('.', return_dag=True)

    env_airflow = {'path': {'products': products}}
    Path('env.airflow.yaml').write_text(yaml.dump(env_airflow))

    with pytest.raises(ValueError) as excinfo:
        validate.pre(d, dag)

    assert 'The initialized DAG with "env.airflow.yaml" is invalid.' in str(
        excinfo.value)


@pytest.mark.parametrize('products', [
    '{{here}}/../output',
    '/output',
])
def test_no_error_if_products_outside_project_root(products,
                                                   tmp_sample_project):
    d, dag = ScriptConfig.from_path('.', return_dag=True)
    env_airflow = {'path': {'products': products}}
    Path('env.airflow.yaml').write_text(yaml.dump(env_airflow))

    validate.pre(d, dag)


def test_no_error_when_validating_from_a_parent_folder(
        tmp_sample_project_in_subdir):
    d, dag = ScriptConfig.from_path('subdir', return_dag=True)
    validate.pre(d, dag)
