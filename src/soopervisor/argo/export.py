from pathlib import Path
import subprocess

from ploomber.spec import DAGSpec
import yaml
try:
    import importlib.resources as pkg_resources
except ImportError:
    # if python<3.7
    import importlib_resources as pkg_resources

from soopervisor import assets
from soopervisor.argo.config import ArgoConfig


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


def upload_code(project_root):

    print('Locating nfs-server pod...')
    result = subprocess.run([
        'kubectl', 'get', 'pods', '-l', 'role=nfs-server', '-o',
        'jsonpath="{.items[0].metadata.name}"'
    ],
                            check=True,
                            capture_output=True)

    pod_name = result.stdout.decode('utf-8').replace('"', '')
    project_name = Path(project_root).resolve().name

    print('Uploading code...')
    subprocess.run([
        'kubectl', 'cp',
        str(project_root), f'{pod_name}:/exports/{project_name}'
    ])


def _make_volume_entries(mv):
    """
    Generate volume-related entries in argo spec, returns one for "volumes"
    section and another one for "volumeMounts"
    """
    volume = {
        'name': mv.claim_name,
        'persistentVolumeClaim': {
            'claimName': mv.claim_name
        }
    }

    # reference: https://argoproj.github.io/argo/fields/#volumemount
    volume_mount = {
        'name': mv.claim_name,
        # by convention, mount to /mnt/ and use the claim name
        'mountPath': f'/mnt/{mv.claim_name}',
        'subPath': mv.sub_path
    }

    return volume, volume_mount


def project(project_root):
    """Export Argo YAML spec from Ploomber project to argo.yaml

    Parameters
    ----------
    project_root : str
        Project root (pipeline.yaml parent folder)
    """
    # TODO: from project can return the dag
    config = ArgoConfig.from_project(project_root)

    dag = DAGSpec(f'{project_root}/pipeline.yaml',
                  lazy_import=config.lazy_import).to_dag()

    volumes, volume_mounts = zip(*(_make_volume_entries(mv)
                                   for mv in config.mounted_volumes))

    d = yaml.safe_load(pkg_resources.read_text(assets, 'argo-workflow.yaml'))
    d['volumes'] = volumes

    tasks_specs = []

    for task_name in dag:
        task = dag[task_name]
        spec = _make_argo_task(task_name, list(task.upstream))
        tasks_specs.append(spec)

    d['metadata']['generateName'] = f'{config.project_name}-'
    d['spec']['templates'][1]['dag']['tasks'] = tasks_specs
    d['spec']['templates'][0]['script']['volumeMounts'] = volume_mounts

    # set Pods working directory to the root of the first mounted volume
    d['spec']['templates'][0]['script']['workingDir'] = volume_mounts[0][
        'mountPath']

    d['spec']['templates'][0]['script']['image'] = config.image

    with open(f'{project_root}/argo.yaml', 'w') as f:
        yaml.dump(d, f)

    return d
