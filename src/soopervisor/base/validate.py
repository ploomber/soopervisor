"""
Functions to validate projects before executing/exporting them
"""

from pathlib import Path

from ploomber.spec import DAGSpec


def project(config, load_dag=True):
    """
    Verify project has the right structure before running the script.
    This runs as a sanity check in the development machine
    """
    if not Path(config.paths.environment).exists():
        raise FileNotFoundError(
            'Expected a conda "environment.yml" at: {}'.format(
                config.paths.environment))

    # TODO: warn if the environment file does not have pinned versions
    # TODO: warn if the setup.py dependencies (if any), does not have pinned
    # versions

    if config.environment_name is None:
        raise ValueError('Failed to extract the environment name from the '
                         'conda "environment.yaml"')

    pipeline_yaml = Path(config.paths.project, 'pipeline.yaml')

    if not pipeline_yaml.exists():
        raise FileNotFoundError('Expected a "pipeline.yaml" file at: ' +
                                str(pipeline_yaml))

    # when using soopervisor, sometimes the current environment is not fully
    # configured to instantiate the pipeline (e.g. if the pipeline has
    # PythonCallables, we have to import those, which involves importing all
    # packages imported by the modules where the functions are defined)
    # Sometimes we just want to export the project, so we shoulnd't expect the
    #  the user to have a fully configured environment, and even when executing
    # locally, we should limit ourselves to have soopervisor installed. The
    # only advantage of instantiating the DAG here is that we can do more
    # validation. lazy_import helps "partially load" the pipeline by
    # instantiating a DAG object whose imports are lazily loaded but this still
    # doesn't remove 100% imports required, if we set load_dag=False, we
    # completely skip loading the DAG (which means fewer validations) but
    # we skip all imports
    if load_dag:
        try:
            # NOTE: should lazy_import be an option from config?
            dag = DAGSpec(pipeline_yaml, lazy_import=True).to_dag()
            # forcing makes it faster because we don't have to check task status
            dag.render(force=True, show_progress=False)
        except Exception as e:
            raise RuntimeError(
                'Failed to initialize DAG from pipeline.yaml') from e
    else:
        dag = None

    return dag
