from pathlib import Path

import yaml
import pytest

from soopervisor.airflow.export import AirflowExporter


@pytest.mark.parametrize('products', [
    '{{here}}/output',
    '{{here}}/subfolder/output',
])
def test_error_if_products_inside_project_root(products, tmp_sample_project):
    env_airflow = {'path': {'products': products}}
    Path('env.serve.yaml').write_text(yaml.dump(env_airflow))

    with pytest.raises(ValueError) as excinfo:
        AirflowExporter('soopervisor.yaml', env_name='serve')

    assert 'The initialized DAG with "env.serve.yaml" is invalid.' in str(
        excinfo.value)


@pytest.mark.parametrize('products', [
    '{{here}}/../output',
    '/output',
])
def test_no_error_if_products_outside_project_root(products,
                                                   tmp_sample_project):
    env_airflow = {'path': {'products': products}}
    Path('env.serve.yaml').write_text(yaml.dump(env_airflow))

    AirflowExporter('soopervisor.yaml', env_name='serve')
