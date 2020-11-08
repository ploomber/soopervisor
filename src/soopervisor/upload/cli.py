from soopervisor.storage.box import BoxUploader
import click


@click.command()
@click.argument('folder')
@click.argument('to')
def upload(folder, to, help='Directory to upload'):
    """
    Upload files
    """
    uploader = BoxUploader.from_environ(root_folder=to)
    uploader.upload_files([folder])
