import pytest

from soopervisor.aws import util

MAPPING = {
    'fit-*': 'some-value',
    'another': 'another-value',
}


@pytest.mark.parametrize('mapping, task_name, task_resources, default', [
    [MAPPING, 'fit-0', 'some-value', None],
    [MAPPING, 'fit-10', 'some-value', None],
    [MAPPING, 'another', 'another-value', None],
    [MAPPING, 'no-key', None, None],
    [MAPPING, 'no-key', 42, 42],
])
def test_task_resources(mapping, task_name, task_resources, default):
    tr = util.TaskResources(mapping)

    assert tr.get(task_name, default=default) == task_resources
