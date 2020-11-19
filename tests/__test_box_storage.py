from pathlib import Path
from soopervisor.storage.box import BoxUploader


def find_directory_from_parent(client, name, parent_id='0'):
    parent = client.folder(parent_id)

    for directory in parent.get_items():
        if directory.name == name:
            return directory

    return False


def test_upload(tmp_empty):
    Path('output').mkdir()
    Path('output/subdir').mkdir()
    Path('output/a').touch()
    Path('output/subdir/b').touch()

    uploader = BoxUploader.from_yaml('~/.auth/box.yaml')
    uploader.upload(src='output', dst='box_folder')

    box_folder = find_directory_from_parent(uploader.client,
                                            'box_folder',
                                            parent_id='0')
    assert box_folder
    assert box_folder.object_type == 'folder'
    assert 'a' in [
        item.name for item in box_folder.get_items()
        if item.object_type == 'file'
    ]

    subdir = find_directory_from_parent(uploader.client,
                                        'subdir',
                                        parent_id=box_folder.id)

    assert subdir
    assert subdir.object_type == 'folder'
    assert 'b' in [
        item.name for item in subdir.get_items() if item.object_type == 'file'
    ]
