from pathlib import Path


def project(config):
    """
    Verify project has the right structure before running the script
    """
    if not Path(config.paths.environment).exists():
        raise FileNotFoundError(
            'An environment file was expected at: {}'.format(
                config.paths.environment))

    if not Path(config.paths.project,
                'pipeline.yaml').exists() and not config.args:
        raise FileNotFoundError('A "pipeline.yaml" is required to declare '
                                'the pipeline')
