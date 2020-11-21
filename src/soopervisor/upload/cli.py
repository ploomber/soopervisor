from soopervisor.base.config import ScriptConfig
from soopervisor.storage.LocalStorage import LocalStorage
import click


@click.command()
@click.argument('folder')
@click.argument('to')
def upload(folder, to, help='Directory to upload'):
    """
    Upload files
    """
    # NOTE: should this logic be here? or rather generate script.sh wit the
    # appropriate option (e.g. with a parameter --service box), instead of
    # parsing the config file again
    cfg = ScriptConfig.from_project('.')

    if cfg.storage.provider == 'box':
        from soopervisor.storage.box import BoxUploader

        uploader = BoxUploader.from_environ()
        uploader.upload_files([folder], to)
    elif cfg.storage.provider == 'local':
        uploader = LocalStorage()
        uploader.upload(folder, to)
