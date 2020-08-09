import pytest
from boxsdk.exception import BoxValueError, BoxAPIException
from pathlib import Path

from soopervisor.storage import box


def test_upload_files(monkeypatch):
    class RootFolder:
        def __init__(self):
            self.id = "0"

    def mock_root_folder():
        class MockRootFolder:
            @staticmethod
            def get():
                return RootFolder()

        return MockRootFolder()

    def mock_upload_directory(*args, **kwargs):
        pass

    def mock_upload_each_file(*args, **kwargs):
        pass

    monkeypatch.setattr(box.client, "root_folder", mock_root_folder)
    monkeypatch.setattr(box, "_upload_directory", mock_upload_directory)
    monkeypatch.setattr(box, "_upload_each_file", mock_upload_each_file)

    assert box.upload_files(["./", "./README.md"])


def test_upload_files_wrong_paths(monkeypatch):
    class RootFolder:
        def __init__(self):
            self.id = "0"

    def mock_root_folder():
        class MockRootFolder:
            @staticmethod
            def get():
                return RootFolder()

        return MockRootFolder()

    monkeypatch.setattr(box.client, "root_folder", mock_root_folder)

    with pytest.raises(FileNotFoundError):
        assert box.upload_files(["wrong/path"])


def test_upload_directory(faker, monkeypatch):
    def mock_create_folder(*args, **kwargs):
        return str(faker.pyint())

    def mock_upload_each_file(*args, **kwargs):
        pass

    monkeypatch.setattr(box, "_create_folder", mock_create_folder)
    monkeypatch.setattr(box, "_upload_each_file", mock_upload_each_file)

    assert box._upload_directory(path=Path("./"),
                                 parent_folder_id=str(faker.pyint()))


def test_create_folder(faker, monkeypatch):
    class Subfolder:
        def __init__(self):
            self.id = str(faker.pyint())

    def mock_folder(folder_id):
        class MockFolder:
            @staticmethod
            def create_subfolder(folder_name):
                return Subfolder()

        return MockFolder()

    monkeypatch.setattr(box.client, "folder", mock_folder)

    assert box._create_folder(str(faker.pyint()), "path/to/folder")


def test_create_a_duplicated_folder(faker, monkeypatch):
    def mock_folder(folder_id):
        class MockFolder:
            @staticmethod
            def create_subfolder(folder_name):
                raise BoxAPIException(status=409)

        return MockFolder()

    monkeypatch.setattr(box.client, "folder", mock_folder)

    with pytest.raises(FileExistsError):
        assert box._create_folder(str(faker.pyint()), "path/to/folder")


def test_delete_folder(faker, monkeypatch):
    def mock_folder(folder_id):
        class MockFolder:
            @staticmethod
            def delete():
                return True

        return MockFolder()

    monkeypatch.setattr(box.client, "folder", mock_folder)
    assert box._delete_folder(str(faker.pyint()))


def test_delete_wrong_folder(faker, monkeypatch):
    def mock_delete_folder(folder_id):
        class MockFolder:
            @staticmethod
            def delete():
                raise BoxValueError()

        return MockFolder()

    monkeypatch.setattr(box.client, "folder", mock_delete_folder)

    with pytest.raises(ValueError):
        assert box._delete_folder(str(faker.pyint()))


def test_upload_each_file_normal_size(faker, monkeypatch):
    class Stat:
        def __init__(self):
            self.st_size = 20

    def mock_file():
        class MockStat:
            @staticmethod
            def stat():
                return Stat()

        return MockStat()

    def mock_upload_file(*args, **kwargs):
        return True

    monkeypatch.setattr(box, "_upload_file", mock_upload_file)

    assert box._upload_each_file(str(faker.pyint()), mock_file())


def test_upload_each_file_large_size(faker, monkeypatch):
    class Stat:
        def __init__(self):
            self.st_size = box.CHUNKED_UPLOAD_MINIMUM + 1

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

    monkeypatch.setattr(box, "_upload_large_file", mock_upload_large_file)

    assert box._upload_each_file(str(faker.pyint()), mock_file())


def test_upload_file(faker, monkeypatch):
    def mock_folder(folder_id):
        class MockFolder:
            @staticmethod
            def upload(file):
                class File:
                    def __init__(self):
                        self.name = "file.ext"

                return File()

        return MockFolder

    monkeypatch.setattr(box.client, "folder", mock_folder)
    assert box._upload_file(str(faker.pyint()), "path/to/file.ext")


def test_upload_an_existing_file(faker, monkeypatch):
    def mock_folder(folder_id):
        class MockFolder:
            @staticmethod
            def upload(file):
                raise BoxAPIException(
                    status=409, context_info={"conflicts": {
                        "id": "1234"
                    }})

        return MockFolder

    monkeypatch.setattr(box.client, "folder", mock_folder)

    with pytest.raises(FileExistsError):
        assert box._upload_file(str(faker.pyint()), "path/to/file.ext")


def test_delete_file(faker, monkeypatch):
    def mock_file(file_id):
        class MockFile:
            @staticmethod
            def delete():
                return True

        return MockFile()

    monkeypatch.setattr(box.client, "file", mock_file)
    assert box._delete_file(str(faker.pyint()))


def test_delete_wrong_file(faker, monkeypatch):
    def mock_delete_file(file_id):
        class MockFile:
            @staticmethod
            def delete():
                raise BoxValueError()

        return MockFile()

    monkeypatch.setattr(box.client, "file", mock_delete_file)

    with pytest.raises(ValueError):
        assert box._delete_file(str(faker.pyint()))


def test_upload_large_file(faker, monkeypatch):
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

    monkeypatch.setattr(box.client, "folder", mock_folder)

    result = box._upload_large_file(str(faker.pyint()), "README.md",
                                    faker.pyint())
    assert result


def test_upload_large_file_not_found(faker):
    with pytest.raises(FileNotFoundError):
        assert box._upload_large_file(str(faker.pyint()), "file.txt",
                                      faker.pyint())
