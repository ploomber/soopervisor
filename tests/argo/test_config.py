import pytest

from soopervisor.argo.config import ArgoConfig, ArgoMountedVolume


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


def test_config_defaults():
    assert ArgoConfig.defaults() == {
        'submit': {
            'repository': 'your-repository'
        },
        'backend': 'argo-workflows'
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


def test_sample_project_from_path(session_sample_project):
    cfg = ArgoConfig.from_file_with_root_key('soopervisor.yaml',
                                             env_name='env')

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
