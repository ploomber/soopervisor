from soopervisor.base.config import ScriptConfig
from soopervisor.storage.box import BoxUploader
from soopervisor.storage.LocalStorage import LocalStorage
import click


@click.command()
@click.argument('folder')
@click.argument('to')
def upload(folder, to, help='Directory to upload'):
    """
    Upload files
    """
    cfg = ScriptConfig.from_project('.')

    if cfg.storage.provider == 'box':
        uploader = BoxUploader.from_environ(root_folder=to)
        uploader.upload_files([folder])
    elif cfg.storage.provider == 'local':
        uploader = LocalStorage()
        uploader.upload(folder, to)
