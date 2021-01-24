import pytest

from soopervisor.argo.config import ArgoConfig, ArgoMountedVolume


@pytest.mark.parametrize(
    'name, sub_path, expected_sub_path',
    [
        ['name', 'sub_path', 'sub_path'],
        ['name', '{{project_name}}', 'some_project'],
        ['name', 'data/{{project_name}}', 'data/some_project'],
    ],
)
def test_argo_mounted_volume_render(name, sub_path, expected_sub_path):
    mv = ArgoMountedVolume(name=name, sub_path=sub_path, spec=dict())
    mv.render(project_name='some_project')

    assert mv.sub_path == expected_sub_path
    assert mv.name == 'name'


def test_make_volume_entries():
    mv = ArgoMountedVolume(
        name='name',
        sub_path='sub_path',
        spec=dict(persistentVolumeClaim=dict(claimName='claimName')))

    assert mv.to_volume() == {
        'name': 'name',
        'persistentVolumeClaim': {
            'claimName': 'claimName'
        }
    }

    assert mv.to_volume_mount() == {
        'name': 'name',
        'mountPath': '/mnt/name',
        'subPath': 'sub_path'
    }


def test_make_volume_entries_no_sub_path():
    mv = ArgoMountedVolume(name='name', spec=dict())

    assert mv.to_volume_mount() == {
        'name': 'name',
        'mountPath': '/mnt/name',
        'subPath': ''
    }


@pytest.mark.parametrize(
    'mvs, expected_sub_paths',
    [
        [[
            {
                'name': 'name',
                'sub_path': 'path',
                'spec': dict()
            },
        ], ['path']],
        [[
            {
                'name': 'name',
                'sub_path': '{{project_name}}',
                'spec': dict(),
            },
            {
                'name': 'name',
                'sub_path': 'path',
                'spec': dict(),
            },
        ], ['sample_project', 'path']],
    ],
)
def test_argo_config_render(mvs, expected_sub_paths, session_sample_project):
    cfg = ArgoConfig(mounted_volumes=mvs)
    cfg.render()

    assert [mv.sub_path for mv in cfg.mounted_volumes] == expected_sub_paths


def test_argo_config_defaults():
    cfg = ArgoConfig()

    assert cfg.image == 'continuumio/miniconda3'
    # FIXME: why is this using session_sample_project fixture if I didn't
    # add it to this test?
    assert cfg.mounted_volumes == [{
        'name': 'nfs',
        'sub_path': 'sample_project',
        'spec': {
            'persistentVolumeClaim': {
                'claimName': 'nfs'
            }
        }
    }]
    assert cfg.lazy_import
    assert cfg.code_pod is None


def test_sample_project_from_path(session_sample_project):
    cfg = ArgoConfig.from_project('.')

    assert cfg.image == 'continuumio/miniconda3'
    assert cfg.mounted_volumes == [{
        'name': 'nfs',
        'sub_path': 'sample_project',
        'spec': {
            'persistentVolumeClaim': {
                'claimName': 'nfs'
            }
        }
    }]
