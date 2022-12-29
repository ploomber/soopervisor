from pathlib import Path

import pytest

from soopervisor import _io, exceptions


def test_load_config_file(tmp_empty):
    Path("soopervisor.yaml").write_text("")

    with pytest.raises(exceptions.ConfigurationFileTypeError) as excinfo:
        _io.load_config_file()

    expected = (
        "Expected 'soopervisor.yaml' to contain a dictionary"
        " but got an object of type: NoneType"
    )
    assert str(excinfo.value) == expected


def test_load_config_file_missing_file_error(tmp_empty):

    with pytest.raises(exceptions.ConfigurationError) as excinfo:
        _io.load_config_file()

    expected = "Error loading 'soopervisor.yaml'. File does not exist."
    assert str(excinfo.value) == expected


def test_load_config_file_existing_directory_error(tmp_empty):
    Path("soopervisor.yaml").mkdir()

    with pytest.raises(exceptions.ConfigurationError) as excinfo:
        _io.load_config_file()

    expected = "Error loading 'soopervisor.yaml'. Path is a directory."
    assert str(excinfo.value) == expected
