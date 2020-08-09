import pytest
from click.testing import CliRunner

from soopervisor.cli import cli
from soopervisor.executors.LocalExecutor import LocalExecutor


def null_execute(self):
    pass


@pytest.mark.parametrize('args',
                         [['build'], ['build', '--clean-products-path']])
def test_build(args, monkeypatch, tmp_sample_project, mock_git_hash):
    monkeypatch.setattr(LocalExecutor, 'execute', null_execute)
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0
