import pytest

from soopervisor.script.script import generate_script
from soopervisor.script.ScriptConfig import ScriptConfig


def test_generate_default_script():
    config = ScriptConfig()
    assert generate_script(config=config)


@pytest.mark.parametrize('project_root, product_root, expected', [
    ['/', 'output', '/output'],
    ['/', '/path/to/output', '/path/to/output'],
])
def test_resolve_product_root_path(project_root, product_root, expected):
    config = ScriptConfig(
        paths=dict(project=project_root, products=product_root))
    assert config.paths.products == expected


@pytest.mark.parametrize('project_root, path_to_environment, expected', [
    ['/', 'environment.yml', '/environment.yml'],
    ['/', '/path/to/environment.yml', '/path/to/environment.yml'],
])
def test_resolve_path_to_environment(project_root, path_to_environment,
                                     expected):
    config = ScriptConfig(
        paths=dict(project=project_root, environment=path_to_environment))
    expected_line = ('conda env create --file ' + expected +
                     ' --name ploomber-env --force')

    assert config.paths.environment == expected
    assert expected_line in config.to_script()
