from pathlib import Path

import yaml
import pytest
from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor import validate


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


def test_error_if_missing_env_airflow_yaml(tmp_sample_project):
    d, dag = ScriptConfig.from_path('.').export(return_dag=True)
    Path('env.airflow.yaml').unlink()

    with pytest.raises(FileNotFoundError) as excinfo:
        validate.airflow_pre(d, dag)

    assert 'Expected an "env.airflow.yaml"' in str(excinfo.value)


def test_error_if_env_airflow_yaml_is_dir(tmp_sample_project):
    d, dag = ScriptConfig.from_path('.').export(return_dag=True)

    Path('env.airflow.yaml').unlink()
    Path('env.airflow.yaml').mkdir()

    with pytest.raises(FileNotFoundError) as excinfo:
        validate.airflow_pre(d, dag)

    assert 'Expected an "env.airflow.yaml", but got a directory' in str(
        excinfo.value)


@pytest.mark.parametrize('products', [
    '{{here}}/output',
    '{{here}}/subfolder/output',
])
def test_error_if_products_inside_project_root(products, tmp_sample_project):
    d, dag = ScriptConfig.from_path('.').export(return_dag=True)

    env_airflow = {'path': {'products': products}}
    Path('env.airflow.yaml').write_text(yaml.dump(env_airflow))

    with pytest.raises(ValueError) as excinfo:
        validate.airflow_pre(d, dag)

    assert 'The initialized DAG with "env.airflow.yaml" is invalid.' in str(
        excinfo.value)


@pytest.mark.parametrize('products', [
    '{{here}}/../output',
    '/output',
])
def test_no_error_if_products_outside_project_root(products,
                                                   tmp_sample_project):
    d, dag = ScriptConfig.from_path('.').export(return_dag=True)
    env_airflow = {'path': {'products': products}}
    Path('env.airflow.yaml').write_text(yaml.dump(env_airflow))

    validate.airflow_pre(d, dag)


def test_no_error_when_validating_from_a_parent_folder(
        tmp_sample_project_in_subdir):
    d, dag = ScriptConfig.from_path('subdir').export(return_dag=True)
    validate.airflow_pre(d, dag)


def test_error_if_pipeline_has_python_callables(tmp_callables):
    d, dag = ScriptConfig.from_path('.').export(return_dag=True)

    with pytest.raises(ValueError) as excinfo:
        validate.airflow_pre(d, dag)

    assert ('The initialized DAG is invalid. It contains at  least one '
            'PythonCallable task' in str(excinfo.value))
