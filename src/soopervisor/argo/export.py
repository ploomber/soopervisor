"""
Functions for generating Argo YAML spec
"""
import shlex
import subprocess

from ploomber.spec import DAGSpec
import yaml
from yaml.representer import SafeRepresenter

try:
    import importlib.resources as pkg_resources
except ImportError:
    # if python<3.7
    import importlib_resources as pkg_resources

from soopervisor import assets


class literal_str(str):
    """Custom str to represent it in YAML literal style
    Source: https://stackoverflow.com/a/20863889/709975
    """
    pass


def change_style(style, representer):
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar

    return new_representer


# configure yaml to represent "literal_str" objects in literal style
represent_literal_str = change_style('|', SafeRepresenter.represent_str)
yaml.add_representer(literal_str, represent_literal_str)


def _make_argo_task(name, dependencies):
    task = {
        'name': name,
        'dependencies': dependencies,
        'template': 'run-task',
        'arguments': {
            'parameters': [{
                'name': 'task_name',
                'value': name,
            }]
        }
    }
    return task


def upload_code(config):

    if config.code_pod is None:
        raise ValueError('"code_pod" section in the configuration file '
                         'is required when using the upload option')

    get_pods_args = shlex.split(config.code_pod.args or '')

    print('Locating nfs-server pod...')
    result = subprocess.run([
        'kubectl', 'get', 'pods', '--output',
        'jsonpath="{.items[0].metadata.name}"'
    ] + get_pods_args,
                            check=True,
                            capture_output=True)

    pod_name = result.stdout.decode('utf-8').replace('"', '')
    print(f'Got pod: "{pod_name}". Uploading code to "{config.code_pod.path}"')

    subprocess.run([
        'kubectl', 'cp',
        str(config.paths.project), f'{pod_name}:{config.code_pod.path}'
    ])


def project(config):
    """Export Argo YAML spec from Ploomber project to argo.yaml

    Parameters
    ----------
    project_root : str
        Project root (pipeline.yaml parent folder)
    """
    # TODO: validate returns a dag, maybe use that one?
    dag = DAGSpec(f'{config.paths.project}/pipeline.yaml',
                  lazy_import=config.lazy_import).to_dag()

    volumes, volume_mounts = zip(*((mv.to_volume(), mv.to_volume_mount())
                                   for mv in config.mounted_volumes))
    # force them to be lists to prevent "!!python/tuple" to be added
    volumes = list(volumes)
    volume_mounts = list(volume_mounts)

    d = yaml.safe_load(pkg_resources.read_text(assets, 'argo-workflow.yaml'))
    d['spec']['volumes'] = volumes

    tasks_specs = []

    for task_name in dag:
        task = dag[task_name]
        spec = _make_argo_task(task_name, list(task.upstream))
        tasks_specs.append(spec)

    d['metadata']['generateName'] = f'{config.project_name}-'
    d['spec']['templates'][1]['dag']['tasks'] = tasks_specs
    d['spec']['templates'][0]['script']['volumeMounts'] = volume_mounts

    # set Pods working directory to the root of the first mounted volume
    working_dir = volume_mounts[0]['mountPath']
    d['spec']['templates'][0]['script']['workingDir'] = working_dir

    d['spec']['templates'][0]['script']['image'] = config.image

    config_in_argo = config.with_project_root(working_dir)

    # use literal_str to make the script source code be represented in YAML
    # literal style, this makes it readable
    d['spec']['templates'][0]['script']['source'] = literal_str(
        config_in_argo.to_script(
            command='ploomber task {{inputs.parameters.task_name}} --force'))

    with open(f'{config.paths.project}/argo.yaml', 'w') as f:
        yaml.dump(d, f)

    return d
