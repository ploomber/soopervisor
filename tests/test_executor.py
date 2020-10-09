import pytest
from soopervisor.executors.Executor import _check_products_root


@pytest.mark.parametrize('create', [True, False])
def test_check_products_root(create, tmp_path):
    some_directory = tmp_path / 'some' / 'directory'

    if create:
        some_directory.mkdir(parents=True)

    _check_products_root(some_directory)

    assert some_directory.exists() and some_directory.is_dir()


def test_check_products_root_with_existing_files(tmp_path):
    some_directory = tmp_path / 'some-directory'
    some_directory.mkdir()

    (some_directory / 'file.txt').touch()

    with pytest.raises(ValueError):
        _check_products_root(some_directory)
