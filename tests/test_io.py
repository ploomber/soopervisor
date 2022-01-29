from pathlib import Path

import pytest

from soopervisor import _io, exceptions


def test_read_yaml_mapping(tmp_empty):
    Path('soopervisor.yaml').write_text('')

    with pytest.raises(exceptions.ConfigurationFileTypeError) as excinfo:
        _io.read_yaml_mapping()

    expected = ("Expected 'soopervisor.yaml' to contain a dictionary"
                " but got an object of type: NoneType")
    assert str(excinfo.value) == expected
