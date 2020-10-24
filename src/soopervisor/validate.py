from pathlib import Path
from itertools import chain

from ploomber.spec import DAGSpec
from ploomber.products import MetaProduct
from ploomber.tasks import PythonCallable


def project(config_dict):
    """
    Verify project has the right structure before running the script.
    This runs as a sanity check in the development machine
    """
    if not Path(config_dict['paths']['environment']).exists():
        raise FileNotFoundError(
            'Expected a conda "environment.yml" at: {}'.format(
                config_dict['paths']['environment']))

    if config_dict['environment_name'] is None:
        raise ValueError('Failed to extract the environment name from the '
                         'conda "environment.yaml"')

    pipeline_yaml = Path(config_dict['paths']['project'], 'pipeline.yaml')
    if not pipeline_yaml.exists():
        raise FileNotFoundError('Expected a "pipeline.yaml" file at: ' +
                                str(pipeline_yaml))

    try:
        # read from abs path
        dag = DAGSpec('pipeline.yaml').to_dag()
        dag.render()
    except Exception as e:
        raise RuntimeError(
            'Failed to initialize DAG from pipeline.yaml') from e

    return dag


def airflow_pre(config_dict, dag):
    """
    Validates a project before exporting as an Airflow DAG.
    This runs as a sanity check in the development machine
    """
    project_root = Path(config_dict['paths']['project'])
    env_airflow_yaml = project_root / 'env.airflow.yaml'

    if not env_airflow_yaml.exists():
        raise FileNotFoundError('Expected an "env.airflow.yaml" at: ' +
                                str(env_airflow_yaml))
    elif env_airflow_yaml.is_dir():
        raise FileNotFoundError('Expected an "env.airflow.yaml", but got a '
                                'directory at: ' + str(env_airflow_yaml))

    # TODO: read from abs path
    dag_airflow = DAGSpec('pipeline.yaml', env='env.airflow.yaml').to_dag()
    dag_airflow.render()

    # if factory function, check it's decorated to load from env.yaml (?)

    # with the dag instance and using env.airflow.yaml, check that products
    # are not saved inside the projects root folder
    #  airflow continuously scans $AIRFLOW_HOME/dags/ for dag definitions and
    # any extra files can break this process - maybe also show the products
    # to know where things will be saved when running using airflow

    # TODO: test when some products aren't files
    products = [dag_airflow[t].product for t in dag_airflow._iter()]
    products = chain(*([p] if not isinstance(p, MetaProduct) else list(p)
                       for p in products))

    # TODO: improve error message by showing task names for each invalid
    # product

    def resolve_product(product):
        """Converts a File product to str with absolute path
        """
        return str(Path(str(product)).resolve())

    products_invalid = [
        # products cannot be inside project root, convert to absolute
        # otherwise /../../ might cause false positives
        str(p) for p in products
        if resolve_product(p).startswith(str(project_root))
    ]

    if products_invalid:
        products_invalid_ = '\n'.join(products_invalid)
        raise ValueError(
            'The initialized DAG with "env.airflow.yaml" is '
            'invalid. Some products are located under '
            'the project\'s root folder, which is not allowed when deploying '
            'to Airflow. Modify your pipeline so all products are saved '
            f'outside the project\'s root folder "{project_root}". Fix '
            f'the following products:\n{products_invalid_}')

    # TODO: ignore non-files
    # TODO: also raise if relative paths - because we don't know where
    # the dag will be executed from

    # maybe instantiate with env.yaml and env.airflow.yaml to make sure
    # products don't clash?

    # check dag has no PythonCallable tasks - we will support this when
    # ploomber has an public api to export functions to notebooks. It is
    # technically possible to use them but this would require the Airflow
    # host to have all dependencies that those functions use,
    # because instantiating the Ploomber DAG requires importing them.
    # Requiring certain packages to be installed in Airflow can cause a lot
    # of trouble. There is a potential solution for this, see Ploomber issue
    # #275
    has_callables = any(
        isinstance(dag_airflow[t], PythonCallable)
        for t in dag_airflow._iter())

    if has_callables:
        raise ValueError(
            'The initialized DAG is invalid. It contains at  '
            'least one PythonCallable task, whcih are currently not supported '
            'when exporting to Airflow. Convert them to scripts and use '
            'NotebookRunner instead')

    # check all products are prefixed with products root - this implies
    # that files should be absolute paths otherwise it's ambiguous -
    # should then we raise an arror if any product if defined with relative
    # paths?


def airflow_post():
    """
    Validates an Airflow DAG converted from a Ploomber DAG.
    This runs as a sanity check in the development machine
    """
    pass


def airflow_host_pre():
    """
    Validate a Ploomer DAG about to be exported to an Airflow DAG, this
    function is meant to be executed in the Airflow host. It is called
    in the auto-generated .py file with the DAG declaration that Airflow loads.

    With cannot run this in the development machine because some checks depend
    on the AIRFLOW_HOME env variable in the machine running Airflow
    """
    # NOTE: here we don't care about product's status - we should make sure
    # we render the dag in the fastest way possible

    # check env.yaml

    # compare version that generated the file? what is the best way?
    # maybe create a metadata file after exporting

    # check environment will not be created inside the dags folder

    # if running in isolated containers, tasks cannot read upstream products,
    # we have to check that the File products have a valid client so they
    # can fetch them

    pass
