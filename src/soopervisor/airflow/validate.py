from pathlib import Path
from itertools import chain

from ploomber.spec import DAGSpec
from ploomber.products import MetaProduct


def pre(config, dag):
    """
    Validates a project before exporting as an Airflow DAG.
    This runs as a sanity check in the development machine
    """
    project_root = Path(config.paths.project)
    env_airflow_yaml = project_root / 'env.airflow.yaml'

    if not env_airflow_yaml.exists():
        raise FileNotFoundError('Expected an "env.airflow.yaml" at: ' +
                                str(env_airflow_yaml))
    elif env_airflow_yaml.is_dir():
        raise FileNotFoundError('Expected an "env.airflow.yaml", but got a '
                                'directory at: ' + str(env_airflow_yaml))

    # NOTE: should lazy_import be an option from config?
    dag_airflow = DAGSpec(project_root / 'pipeline.yaml',
                          env=env_airflow_yaml,
                          lazy_import=True).to_dag()
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

    # check all products are prefixed with products root - this implies
    # that files should be absolute paths otherwise it's ambiguous -
    # should then we raise an arror if any product if defined with relative
    # paths?


def post():
    """
    Validates an Airflow DAG converted from a Ploomber DAG.
    This runs as a sanity check in the development machine
    """
    pass


def host_pre():
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
