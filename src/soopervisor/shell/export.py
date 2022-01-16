import fnmatch
import os
from pathlib import Path
import subprocess

from ploomber.io._commander import Commander, CommanderStop
from jinja2 import Template, meta
import click

from soopervisor import abc
from soopervisor import commons
from soopervisor.shell.config import SlurmConfig
from soopervisor import validate


def _check_template_variables(env, source):
    return meta.find_undeclared_variables(env.parse(source))


def _validate_template(env, source):
    vars = _check_template_variables(env, source)
    validate.keys({'command', 'name'}, vars,
                  'Error validating template.sh, missing placeholders')


def _script_name_for_task_name(name, workspace):
    """
    Returns the path to the script to use based on the task name
    """
    name_sh = f'{name}.sh'
    exact_match = Path(workspace, name_sh)

    if exact_match.is_file():
        return exact_match

    files = sorted(os.listdir(workspace))

    for file in files:
        if fnmatch.fnmatch(name_sh, file.replace('__', '*')):
            return Path(workspace, file)

    return Path(workspace, 'template.sh')


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

    def validate(self):
        """
        Override method from the abstract class, since it validates lock files
        exist, but we don't need those for SLURM
        """
        pass

    @staticmethod
    def _export(cfg, env_name, mode, until, skip_tests, ignore_git):
        """
        Export and submit jbs
        """
        with Commander(workspace=env_name,
                       templates_path=('soopervisor', 'assets')) as cmdr:
            template = Path(env_name, 'template.sh').read_text()
            _validate_template(cmdr._env, template)

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

        # determine which script file to use
        script_sh = _script_name_for_task_name(name, workspace)
        # generate script and save
        job_sh = Template(script_sh.read_text())

        ploomber_command = ' '.join(['ploomber', 'task', name] + args)
        script = job_sh.render(name=name, command=ploomber_command)
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
