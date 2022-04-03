"""
Loading dags
"""
from pathlib import Path

from ploomber.constants import TaskStatus
from ploomber.spec import DAGSpec
from ploomber.exceptions import DAGSpecInvalidError
from ploomber.products import File
from ploomber.io._commander import Commander

from soopervisor import commons
from soopervisor.enum import Mode


def _is_relative_path(path):
    return not Path(path).is_absolute()


def _extract_product_parent(task_spec):
    product_spec = task_spec.data['product']

    try:
        # single product
        paths = [Path(product_spec)]
    except TypeError:
        # dictionary
        try:
            paths = [Path(product) for product in product_spec.values()]
        except Exception:
            # any other thing
            return []

    return [str(path.parent) for path in paths if _is_relative_path(path)]


def product_prefixes_from_spec(spec):
    parents = [_extract_product_parent(t) for t in spec['tasks']]
    parents_flat = [path for sub in parents for path in sub]
    return sorted(set(parents_flat)) or None


def find_spec(cmdr, name, lazy_import=False):
    """
    Find spec to use. It first tries to load a file with pipeline.{name}.yaml,
    if that doesn't exist, it tries to load a pipeline.yaml
    """
    cmdr.info('Loading DAG')

    try:
        spec, relative_path = DAGSpec._find_relative(name=name,
                                                     lazy_import=lazy_import)
        cmdr.print(f'Found {spec.path!s}. Loading...')
    except DAGSpecInvalidError:
        cmdr.print(f'No pipeline.{name}.yaml found, '
                   'looking for pipeline.yaml instead')
        spec = None

    if spec is None:
        spec, relative_path = DAGSpec._find_relative(lazy_import=lazy_import)
        cmdr.print(f'Found {spec.path!s}. Loading...')

    return spec, relative_path


def load_dag(cmdr, name=None, mode='incremental', lazy_import=False):
    """Load tasks names and their upstream dependencies

    Parameters
    ----------
    cmdr : Commander
        Commander instance used to print output

    name : str
        Target environment name. This prioritizes loading a
        pipeline.{name}.yaml spec, if such doesn't exist, it loads a
        pipeline.yaml

    mode : bool, default='incremental'
        One of 'incremental' (only include outdated tasks with respect to
        the remote metadata), 'regular' (ignore status, submit all tasks
        and determine status at runtime) or 'force' (ignore status, submit
        all tasks and force execution regardless of status)

        Returns
        -------
        dag : class
            A DAG class - collection of tasks with dependencies (values)
        relative_path : str
            The relative location of the pipeline.yaml file
        """

    valid = Mode.get_values()

    spec, relative_path = find_spec(cmdr=cmdr,
                                    name=name,
                                    lazy_import=lazy_import)
    dag = spec.to_dag()

    if mode not in valid:
        raise ValueError(f'mode must be one of {valid!r}')

    if mode == 'incremental':

        # what if user has a shared disk but still wants to upload artifacts?
        # maybe add a way to force this
        if dag.clients.get(File):
            dag.render(remote=True)
        else:
            dag.render()

    else:
        # force makes rendering faster. we just need this to ensure the
        # pipeline does not have any rendering problems before proceeding
        dag.render(force=True)

    return dag, relative_path


def load_tasks(cmdr, name=None, mode='incremental', lazy_import=False):
    """Load tasks names and their upstream dependencies

    Parameters
    ----------
    cmdr : Commander
        Commander instance used to print output

    name : str
        Target environment name. This prioritizes loading a
        pipeline.{name}.yaml spec, if such doesn't exist, it loads a
        pipeline.yaml

    mode : bool, default='incremental'
        One of 'incremental' (only include outdated tasks with respect to
        the remote metadata), 'regular' (ignore status, submit all tasks and
        determine status at runtime) or 'force' (ignore status, submit all
        tasks and force execution regardless of status)

    Returns
    -------
    task : dict
        A dictionary with tasks (keys) and upstream dependencies (values)
        to submit

    args : list
        A list of arguments to pass to "ploomber task {name}"
    """

    dag, relative_path = load_dag(cmdr, name, mode, lazy_import=lazy_import)

    if mode == 'incremental':
        tasks = []

        for name, task in dag.items():
            if not mode or task.exec_status != TaskStatus.Skipped:
                tasks.append(name)
    else:
        tasks = list(dag.keys())

    out = {}

    for t in tasks:
        out[t] = [name for name in dag[t].upstream.keys() if name in tasks]

    args = ['--entry-point', relative_path]

    if mode == 'force':
        args.append('--force')

    return out, args


def load_dag_and_spec(env_name, lazy_import=False):
    # initialize dag (needed for validation)
    # TODO: _export also has to find_spec, maybe load it here and
    # pass it directly to _export?
    with Commander() as cmdr:
        spec, _ = commons.find_spec(cmdr=cmdr,
                                    name=env_name,
                                    lazy_import=lazy_import)

    dag = spec.to_dag().render(force=True, show_progress=False)

    return dag, spec
