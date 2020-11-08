"""Module for uploading data to box
"""
import os
import hashlib
import logging
from pathlib import Path
from typing import List
from tqdm import tqdm

import yaml
from boxsdk import Client, OAuth2
from boxsdk.exception import BoxAPIException, BoxValueError

CHUNKED_UPLOAD_MINIMUM = 20000000


class BoxUploader:
    """

    Parameters
    ----------
    client_id : str
        Client ID

    primary_access_token : str
        Primary access token

    root_folder : str
        The name of the folder to use for this upload session

    Examples
    --------
    >>> from soopervisor.storage.box import BoxUploader
    >>> uploader = BoxUploader.from_yaml('~/.auth/box.yaml', 'my_uploads')
    >>> uploader.upload_files(['some_file.png'])
    """
    def __init__(self, client_id, primary_access_token, root_folder):
        auth = OAuth2(
            client_id=client_id,
            client_secret='',
            access_token=primary_access_token,
        )

        self.client = Client(auth)

        # TODO: only works when passing a single name, breaks with "a/b/c"
        # '0' is the root folder id
        self.root_folder = self._create_folder('0', root_folder)

    @classmethod
    def from_yaml(cls, path_to_credentials, root_folder):
        with open(str(Path(path_to_credentials).expanduser())) as f:
            d = yaml.safe_load(f)

        return cls(d['client_id'], d['primary_access_token'], root_folder)

    @classmethod
    def from_environ(cls, root_folder):
        return cls(os.environ['CLIENT_ID'], os.environ['PRIMARY_ACCESS_TOKEN'],
                   root_folder)

    def upload_files(self, paths: List[str], replace: bool = False):
        """
        Upload files to Box

        Parameters
        ----------
        paths: List[str]
            List of all the paths to be uploaded
        replace: bool,optional
            If True, all the files and folders will be replaced by the new ones
        """
        for path in paths:
            path = Path(path)
            if path.exists():
                if path.is_dir():
                    total_size_upload = sum(
                        file.stat().st_size for file in path.glob('**/*')
                        if (not file.name.startswith(".") and file.is_file()))
                    progress_bar = tqdm(total=total_size_upload)
                    folder = self._create_folder(self.root_folder.id,
                                                 path.name,
                                                 replace_folder=replace)
                    self._upload_directory(path=path,
                                           parent_folder_id=folder.id,
                                           progress_bar=progress_bar)
                elif path.is_file():
                    self._upload_each_file(folder_id=self.root_folder.id,
                                           file=path,
                                           replace_file=replace)
            else:
                raise FileNotFoundError("Invaid or non-existent path")

        return True

    def _upload_directory(self,
                          path: Path,
                          parent_folder_id: str,
                          progress_bar,
                          replace_folder: bool = False):
        """
        Upload a directory

        Parameters
        ----------
        paths: Path
            The path to be uploaded
        parent_folder_id:
            The folder id from Box where the directory is to be uploaded
        progress_bar:
            Used to show the progress for the uploading folders
        replace_folder: bool,optional
            If True, the folder on Box is to be replaced by the one to be
            uploaded

        Notes
        -----
        All the .* files will be ignored

        """
        file_system_objects = (file for file in path.iterdir()
                               if not file.name.startswith("."))
        for file_ in file_system_objects:
            if file_.is_dir():
                folder = self._create_folder(parent_folder_id, file_.name)
                self._upload_directory(path=file_.absolute(),
                                       parent_folder_id=folder.id,
                                       progress_bar=progress_bar)
            elif file_.is_file():
                self._upload_each_file(folder_id=parent_folder_id, file=file_)

            progress_bar.set_postfix(file=file_.name, refresh=False)
            progress_bar.update(file_.stat().st_size)

        return True

    def _create_folder(self,
                       parent_folder_id: str,
                       folder_name: str,
                       replace_folder: bool = False):
        """Create a new folder
        """
        try:
            subfolder = self.client.folder(
                folder_id=parent_folder_id).create_subfolder(folder_name)
            logging.info("Folder {} created".format(folder_name))
            return subfolder
        except BoxAPIException as e:
            if replace_folder:
                folder_id = e.context_info.get("conflicts")[0].get("id")
                self._delete_folder(folder_id=folder_id)
                return self._create_folder(parent_folder_id, folder_name)
            else:
                raise FileExistsError("The folder already exists")

    def _delete_folder(self, folder_id: str):
        try:
            return self.client.folder(folder_id).delete()
        except BoxAPIException:
            raise ValueError("Invalid folder ID")

    def _upload_each_file(self,
                          folder_id: str,
                          file: Path,
                          replace_file: bool = False):
        file_size = file.stat().st_size
        if file_size < CHUNKED_UPLOAD_MINIMUM:
            file_uploaded = self._upload_file(folder_id, file, replace_file)
        else:
            file_uploaded = self._upload_large_file(folder_id=folder_id,
                                                    file=file,
                                                    file_size=file_size,
                                                    replace_file=replace_file)

        return file_uploaded

    def _upload_file(self,
                     folder_id: str,
                     file: str,
                     replace_file: bool = False):
        try:
            new_file = self.client.folder(folder_id=folder_id).upload(file)
            logging.info("File {} uploaded".format(new_file.name))
            return new_file
        except BoxAPIException as e:
            context_info = e.context_info
            file_id = context_info.get("conflicts").get("id")
            if replace_file:
                self._delete_file(file_id)
                return self._upload_file(folder_id, file)
            else:
                raise FileExistsError("File already exists")

    def _delete_file(self, file_id: str):
        try:
            return self.client.file(file_id).delete()
        except BoxAPIException:
            raise ValueError("Invalid file ID")

    def _upload_large_file(self,
                           folder_id: str,
                           file: Path,
                           file_size: int,
                           replace_file: bool = False):
        part_array = []
        with tqdm(total=file_size, unit="B", desc=file.name) as progress_bar:
            with open(file.absolute(), mode="rb") as f:
                sha1 = hashlib.sha1()
                upload_session = self.client.folder(
                    folder_id=folder_id).create_upload_session(
                        file_size, file_name=file.name)

                for part_num in range(upload_session.total_parts):
                    copied_length = 0
                    chunk = b''
                    while copied_length < upload_session.part_size:
                        bytes_read = f.read(upload_session.part_size -
                                            copied_length)
                        if bytes_read is None:
                            continue
                        if len(bytes_read) == 0:
                            break
                        chunk += bytes_read
                        copied_length += len(bytes_read)

                        progress_bar.update(copied_length)

                    uploaded_part = upload_session.upload_part_bytes(
                        chunk, part_num * upload_session.part_size, file_size)
                    part_array.append(uploaded_part)
                    updated_sha1 = sha1.update(chunk)

                content_sha1 = sha1.digest()
                uploaded_file = upload_session.commit(
                    content_sha1=content_sha1, parts=part_array)

        logging.info("File: {0} uploaded".format(uploaded_file.name))

        return True
