from pathlib import Path
import os
from unittest.mock import Mock, ANY, call

import pytest

from ploomber.spec import DAGSpec
from soopervisor.shell.export import SlurmExporter, commons, subprocess


@pytest.fixture
def monkeypatch_slurm(monkeypatch):
    load_tasks_mock = Mock(wraps=commons.load_tasks)

    def factory(value):
        mock = Mock()
        mock.stdout = value
        return mock

    run_mock = Mock(side_effect=[factory(b'0'), factory(b'1'), factory(b'2')])
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)
    monkeypatch.setattr(subprocess, 'run', run_mock)

    return load_tasks_mock, run_mock


def test_slurm_add_sample_project(monkeypatch, tmp_sample_project,
                                  no_sys_modules_cache):
    exporter = SlurmExporter(path_to_config='soopervisor.yaml',
                             env_name='serve')
    exporter.add()

    assert set(os.listdir('serve')) == {'template.sh'}


@pytest.mark.parametrize('template, error', [
    ['{{name}}', "missing placeholders: 'command'"],
    ['{{command}}', "missing placeholders: 'name'"],
    ['', "missing placeholders: 'command', 'name'"],
])
def test_slurm_export_errors_if_missing_placeholder_in_template(
        monkeypatch_slurm, tmp_sample_project, template, error):
    exporter = SlurmExporter(path_to_config='soopervisor.yaml',
                             env_name='serve')
    exporter.add()

    Path('serve', 'template.sh').write_text(template)

    with pytest.raises(ValueError) as excinfo:
        exporter.export(mode='incremental')

    assert error in str(excinfo.value)


def test_slurm_export_sample_project(monkeypatch_slurm, tmp_sample_project):
    load_tasks_mock, run_mock = monkeypatch_slurm

    exporter = SlurmExporter(path_to_config='soopervisor.yaml',
                             env_name='serve')

    exporter.add()
    exporter.export(mode='incremental')

    load_tasks_mock.assert_called_once_with(cmdr=ANY,
                                            name='serve',
                                            mode='incremental')

    run_mock.assert_has_calls([
        call(['sbatch', '--parsable', '_job.sh'],
             capture_output=True,
             check=True),
        call([
            'sbatch',
            '--dependency=afterok:0',
            '--parsable',
            '--kill-on-invalid-dep=yes',
            '_job.sh',
        ],
             capture_output=True,
             check=True),
        call([
            'sbatch',
            '--dependency=afterok:1',
            '--parsable',
            '--kill-on-invalid-dep=yes',
            '_job.sh',
        ],
             capture_output=True,
             check=True)
    ])

    expected = """\
#!/bin/bash
#SBATCH --job-name=plot
#SBATCH --output=result.out
#

source myproj/bin/activate
srun ploomber task plot --entry-point pipeline.yaml\
"""

    assert Path('_job.sh').read_text() == expected


def test_slurm_export_sample_project_incremental(monkeypatch,
                                                 tmp_sample_project):
    dag = DAGSpec('pipeline.yaml').to_dag()
    dag.build()

    load_tasks_mock = Mock(wraps=commons.load_tasks)

    def factory(value):
        mock = Mock()
        mock.stdout = value
        return mock

    run_mock = Mock(side_effect=[factory(b'0'), factory(b'1'), factory(b'2')])
    monkeypatch.setattr(commons, 'load_tasks', load_tasks_mock)
    monkeypatch.setattr(subprocess, 'run', run_mock)

    exporter = SlurmExporter(path_to_config='soopervisor.yaml',
                             env_name='serve')

    exporter.add()
    exporter.export(mode='incremental')

    load_tasks_mock.assert_called_once_with(cmdr=ANY,
                                            name='serve',
                                            mode='incremental')

    run_mock.assert_not_called()


# TODO: test task --force
