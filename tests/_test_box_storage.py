import pytest
from pathlib import Path
from tqdm import tqdm

from soopervisor.storage.box import BoxUploader, CHUNKED_UPLOAD_MINIMUM


def test_upload_files(tmpdir):
    tmp_dir = tmpdir.mkdir("tmp_ploomber_folder")
    file1 = tmp_dir.mkdir("subdir1").join("file1.txt")
    file1.write("lorem ipsum")
    file2 = tmp_dir.mkdir("subdir2").join("file2.txt")
    file2.write("lorem ipsum")

    box = BoxUploader.from_environ()
    root_folder = box.get_root_folder()
    tmp_directory_tests = box._create_folder(parent_folder_id=root_folder.id,
                                             folder_name="tmp_directory_tests")

    assert box.upload_files([tmp_dir.strpath],
                            replace=True,
                            root_folder=tmp_directory_tests)
    assert box._delete_folder(folder_id=tmp_directory_tests.id)


def test_upload_files_wrong_paths():
    box = BoxUploader.from_environ()
    with pytest.raises(FileNotFoundError):
        assert box.upload_files(["wrong/path"])


def test_upload_directory(tmpdir):
    tmp_dir = tmpdir.mkdir("tmp_ploomber_folder")

    file1 = tmp_dir.mkdir("subdir1").join("file1.txt")
    file1.write("lorem ipsum")
    file2 = tmp_dir.mkdir("subdir2").join("file2.txt")
    file2.write("lorem ipsum")

    box = BoxUploader.from_environ()
    root_folder = box.get_root_folder()
    tmp_directory_tests = box._create_folder(parent_folder_id=root_folder.id,
                                             folder_name="tmp_directory_tests")

    progress_bar = tqdm(total=file1.size() + file2.size())

    box._upload_directory(path=Path(tmp_dir.strpath),
                          parent_folder_id=tmp_directory_tests.id,
                          progress_bar=progress_bar,
                          replace_folder=True)

    assert box._delete_folder(folder_id=tmp_directory_tests.id)


def test_create_folder():
    box = BoxUploader.from_environ()
    root_folder = box.get_root_folder()
    assert box._create_folder(root_folder.id, "tmp_folder")

    with pytest.raises(FileExistsError):
        assert box._create_folder(root_folder.id, "tmp_folder")

    folder = box._create_folder(parent_folder_id=root_folder.id,
                                folder_name="tmp_folder",
                                replace_folder=True)

    assert box._delete_folder(folder.id)


def test_delete_folder():
    box = BoxUploader.from_environ()
    root_folder = box.get_root_folder()
    folder = box._create_folder(root_folder.id, "tmp_folder")
    assert box._delete_folder(folder.id)

    with pytest.raises(ValueError):
        assert box._delete_folder(folder.id)


def test_upload_each_file_normal_size(tmp_path):
    file = tmp_path / "tmp_ploomber_file.txt"
    file.write_text("lorem ipsum")

    box = BoxUploader.from_environ()
    root_folder = box.get_root_folder()

    file_box = box._upload_each_file(folder_id=root_folder.id,
                                     file=Path(file.absolute()))
    assert file_box

    assert box._delete_file(file_box.id)


def test_upload_each_file_large_size(tmp_path, faker, monkeypatch):
    class Stat:
        def __init__(self):
            self.st_size = CHUNKED_UPLOAD_MINIMUM + 1

    def mock_file():
        class MockStat:
            def __init__(self):
                self.name = "file.txt"

            @staticmethod
            def stat():
                return Stat()

        return MockStat()

    def mock_upload_large_file(*args, **kwargs):
        return True

    box = BoxUploader.from_environ()
    monkeypatch.setattr(box, "_upload_large_file", mock_upload_large_file)

    assert box._upload_each_file(folder_id=box.get_root_folder().id,
                                 file=mock_file())


def test_upload_file(tmp_path):
    file = tmp_path / "tmp_ploomber_file.txt"
    file.write_text("lorem ipsum")

    box = BoxUploader.from_environ()
    root_folder = box.get_root_folder()
    file_box = box._upload_file(folder_id=root_folder.id, file=file.absolute())
    assert file_box

    with pytest.raises(FileExistsError):
        box._upload_file(folder_id=root_folder.id, file=file.absolute())

    file_box = box._upload_file(folder_id=root_folder.id,
                                file=file.absolute(),
                                replace_file=True)
    assert file_box

    # Remove the file from Box account used by the test
    assert box._delete_file(file_box.id)


def test_delete_file(tmp_path):
    file = tmp_path / "tmp_ploomber_file.txt"
    file.write_text("lorem ipsum")
    box = BoxUploader.from_environ()
    root_folder = box.get_root_folder()
    file_box = box._upload_file(folder_id=root_folder.id, file=file.absolute())
    assert box._delete_file(file_box.id)

    with pytest.raises(ValueError):
        box._delete_file(file_box.id)


def test_upload_large_file(faker, monkeypatch, tmp_path):
    class File:
        def __init__(self):
            self.name = "file.txt"

    class UploadSession:
        def __init__(self):
            self.part_size = faker.pyint(min_value=1, max_value=100)
            self.total_parts = 1

        def upload_part_bytes(*args, **kwargs):
            return None

        def commit(*args, **kwargs):
            return File()

    def mock_folder(folder_id):
        class MockFolder:
            @staticmethod
            def create_upload_session(*args, **kwargs):
                return UploadSession()

        return MockFolder()

    box = BoxUploader.from_environ()
    monkeypatch.setattr(box.client, "folder", mock_folder)

    file = tmp_path / "tmp_ploomber_file.txt"
    file.write_text("lorem ipsum")

    result = box._upload_large_file(folder_id=str(faker.pyint()),
                                    file=file,
                                    file_size=faker.pyint())
    assert result


def test_upload_large_file_not_found(faker):
    box = BoxUploader.from_environ()
    with pytest.raises(FileNotFoundError):
        assert box._upload_large_file(folder_id=str(faker.pyint()),
                                      file=Path("file.txt"),
                                      file_size=faker.pyint())
