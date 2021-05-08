from pathlib import Path

import yaml
import pytest

from soopervisor.airflow.export import AirflowExporter


def test_error_if_missing_env_airflow_yaml(tmp_sample_project):
    Path('env.airflow.yaml').unlink()

    with pytest.raises(FileNotFoundError) as excinfo:
        AirflowExporter('soopervisor.yaml', env_name='some_env')

    assert 'Expected an "env.airflow.yaml"' in str(excinfo.value)


def test_error_if_env_airflow_yaml_is_dir(tmp_sample_project):
    Path('env.airflow.yaml').unlink()
    Path('env.airflow.yaml').mkdir()

    with pytest.raises(FileNotFoundError) as excinfo:
        AirflowExporter('soopervisor.yaml', env_name='some_env')

    assert 'Expected an "env.airflow.yaml", but got a directory' in str(
        excinfo.value)


@pytest.mark.parametrize('products', [
    '{{here}}/output',
    '{{here}}/subfolder/output',
])
def test_error_if_products_inside_project_root(products, tmp_sample_project):
    env_airflow = {'path': {'products': products}}
    Path('env.airflow.yaml').write_text(yaml.dump(env_airflow))

    with pytest.raises(ValueError) as excinfo:
        AirflowExporter('soopervisor.yaml', env_name='some_env')

    assert 'The initialized DAG with "env.airflow.yaml" is invalid.' in str(
        excinfo.value)


@pytest.mark.parametrize('products', [
    '{{here}}/../output',
    '/output',
])
def test_no_error_if_products_outside_project_root(products,
                                                   tmp_sample_project):
    env_airflow = {'path': {'products': products}}
    Path('env.airflow.yaml').write_text(yaml.dump(env_airflow))

    AirflowExporter('soopervisor.yaml', env_name='some_env')


def test_no_error_when_validating_from_a_parent_folder(
        tmp_sample_project_in_subdir):
    AirflowExporter('subdir/soopervisor.yaml', env_name='some_env')
