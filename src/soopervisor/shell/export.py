from pathlib import Path
import subprocess

from ploomber.io._commander import Commander, CommanderStop
from jinja2 import Template
import click

from soopervisor import abc
from soopervisor import commons
from soopervisor.shell.config import SlurmConfig


# TODO: check ploomber version
# TODO: submit all tasks to a single node
class SlurmExporter(abc.AbstractExporter):
    CONFIG_CLASS = SlurmConfig

    @staticmethod
    def _add(cfg, env_name):
        """
        Add sample template
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets'),
                       environment_kwargs=dict(
                           variable_start_string='[[',
                           variable_end_string=']]',
                       )) as e:
            e.copy_template('slurm/template.sh')
            e.success('Done')

    @staticmethod
    def _validate(cfg, dag, env_name):
        pass

    @staticmethod
    def _export(cfg, env_name, mode, until, skip_tests):
        """
        Export and submit jbs
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as cmdr:

            tasks, args = commons.load_tasks(cmdr=cmdr,
                                             name=env_name,
                                             mode=mode)

            if not tasks:
                raise CommanderStop(f'Loaded DAG in {mode!r} mode has no '
                                    'tasks to submit. Try "--mode force" to '
                                    'submit all tasks regardless of status')

            _submit_to_slurm(tasks, args, env_name)


def _submit_to_slurm(tasks, args, workspace):
    """
    Script to submit tasks in a Ploomber pipeline as SLURM jobs.

    Parameters
    ----------
    tasks : dict

    args : list

    workspace : str

    """
    # maps task name to SLURM job id
    name2id = {}

    # iterate over tasks
    for name, upstream in tasks.items():

        # generate script and save
        job_sh = Template(Path(workspace, 'template.sh').read_text())
        script = job_sh.render(name=name, args=' '.join(args))
        Path('_job.sh').write_text(script)

        # does the task have dependencies?
        if upstream:
            # if yes, then use --dependency=afterok:
            ids = ':'.join([name2id[task_name] for task_name in upstream])
            # docs: https://hpc.nih.gov/docs/job_dependencies.html
            # https://slurm.schedmd.com/sbatch.html
            # sbatch [options] script [args...]
            cmd = [
                'sbatch',
                f'--dependency=afterok:{ids}',
                '--parsable',
                # kill job if upstream dependencies fail
                '--kill-on-invalid-dep=yes',
                '_job.sh',
            ]
        else:
            # if no, just submit
            cmd = ['sbatch', '--parsable', '_job.sh']

        # print the submitted command
        click.echo(f'Running command: {" ".join(cmd)}')
        click.echo(f'_job.sh content:\n{script}')

        # submit job
        res = subprocess.run(cmd, capture_output=True, check=True)

        # retrieve the job id, we'll use this to register --dependency
        name2id[name] = res.stdout.decode().strip()
