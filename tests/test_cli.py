from click.testing import CliRunner

from ploomberci.cli import cli
from ploomberci.executors.LocalExecutor import LocalExecutor


def null_execute(self):
    pass


def test_build(monkeypatch, tmp_sample_project, mock_git_hash):
    monkeypatch.setattr(LocalExecutor, 'execute', null_execute)
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    assert result.exit_code == 0
