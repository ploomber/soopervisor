"""Module for uploading data to box
"""

import hashlib
import logging
from os import stat
from pathlib import Path
from typing import List
from boxsdk import Client, OAuth2
from boxsdk.exception import BoxOAuthException, BoxAPIException, BoxValueError


CHUNKED_UPLOAD_MINIMUM = 20000000

auth = OAuth2(
    client_id='[CLIENT_ID]',
    client_secret='[CLIENT_SECRET]',
    access_token='[ACCESS_TOKEN]',
)
client = Client(auth)

def upload_files(paths: List[str], replace: bool = False):
    """
    Upload files to Box

    Parameters
    ----------
    paths: List[str]
        List of all the paths to be uploaded
    replace: bool,optional
        If True, all the files and folders will be replaced by the new ones
    """
    root_folder = client.root_folder().get()

    for path in paths:
        path = Path(path)
        if path.exists():
            if path.is_dir():
                _upload_directory(path=path, root_folder_id=root_folder.id, replace_folder=replace)
            elif path.is_file():
                _upload_each_file(folder_id=root_folder.id, file=path, replace_file=replace)
        else:
            raise FileNotFoundError("Invaid or non-existent path")

    return True


def _upload_directory(path: Path, parent_folder_id: str, replace_folder: bool = False):
    """
    Upload a directory

    Parameters
    ----------
    paths: Path
        The path to be uploaded
    parent_folder_id:
        The folder id from Box where the directory is to be uploaded
    replace_folder: bool,optional
        If True, the folder on Box is to be replaced by the one to be uploaded

    Notes
    -----
    All the .* files will be ignored

    """
    folder_id = _create_folder(parent_folder_id, path.name, replace_folder)

    file_system_objects = (file for file in path.glob('**/*') if not file.name.startswith("."))
    for object in file_system_objects:
        if object.is_dir():
            folder_id = _create_folder(folder_id, object.name)
        elif object.is_file():
            _upload_each_file(folder_id=folder_id, file=object)

    return True


def _create_folder(parent_folder_id: str, folder_name: str, replace_folder: bool = False):
    try:
        subfolder = client.folder(folder_id=parent_folder_id).create_subfolder(folder_name)
        logging.info("Folder {} created".format(folder_name))
        return subfolder.id
    except BoxAPIException as e:
        if replace_folder:
            folder_id = e.context_info.get("conflicts")[0].get("id")
            _delete_folder(folder_id=folder_id)
            return _create_folder(parent_folder_id, folder_name)
        else:
            raise FileExistsError("The folder already exists")


def _delete_folder(folder_id: str):
    try:
        return client.folder(folder_id).delete()
    except BoxValueError:
        raise ValueError("Invalid file ID")


def _upload_each_file(folder_id: str, file: Path, replace_file: bool = False):
    file_size = file.stat().st_size
    if file_size < CHUNKED_UPLOAD_MINIMUM:
        response = _upload_file(folder_id, file, replace_file)
    else:
        response = _upload_large_file(folder_id, file.name, file_size, replace_file)

    return response


def _upload_file(folder_id: str, file: str, replace_file: bool = False):
    try:
        new_file = client.folder(folder_id=folder_id).upload(file)
        logging.info("{} uploaded".format(new_file.name))
        return True
    except BoxAPIException as e:
        context_info = e.context_info
        file_id = context_info.get("conflicts").get("id")
        if replace_file:
            _delete_file(file_id)
            return _upload_file(folder_id, file)
        else:
            raise FileExistsError("File already exists")


def _delete_file(file_id: str):
    try:
        return client.file(file_id).delete()
    except BoxValueError:
        raise ValueError("Invalid file ID")


def _upload_large_file(folder_id: str, file_name: str, file_size: int, replace_file: bool = False):
    part_array = []
    with open(file_name, mode="rb") as f:
        sha1 = hashlib.sha1()
        upload_session = client.folder(folder_id=folder_id).create_upload_session(file_size, file_name=file_name)

        for part_num in range(upload_session.total_parts):
            copied_length = 0
            chunk = b''
            while copied_length < upload_session.part_size:
                bytes_read = f.read(upload_session.part_size - copied_length)
                if bytes_read is None:
                    continue
                if len(bytes_read) == 0:
                    break
                chunk += bytes_read
                copied_length += len(bytes_read)

            uploaded_part = upload_session.upload_part_bytes(chunk, part_num*upload_session.part_size, file_size)
            part_array.append(uploaded_part)
            updated_sha1 = sha1.update(chunk)
        content_sha1 = sha1.digest()
        uploaded_file = upload_session.commit(content_sha1=content_sha1, parts=part_array)
        logging.info("File: {0} uploaded".format(uploaded_file.name))

    return True
