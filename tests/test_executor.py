import pytest
from soopervisor.executors.Executor import _handle_product_root


def test_handle_product(hash, git_hash, tmpdir):
    product_root_version = _handle_product_root(tmpdir)
    assert product_root_version == tmpdir / hash


def test_handle_product_non_existent(hash, git_hash, tmpdir):
    non_existing_root = tmpdir / "non_existent_root"
    product_root_version = _handle_product_root(non_existing_root)
    assert product_root_version == non_existing_root / hash


def test_handle_product_with_existing_files(hash, git_hash, tmpdir):
    hash_dir = tmpdir.mkdir(hash)
    file1 = hash_dir.join("file1.txt")
    file1.write("lorem ipsum")
    file2 = hash_dir.join("file2.txt")
    file2.write("lorem ipsum")

    with pytest.raises(ValueError):
        product_root_version = _handle_product_root(tmpdir)
