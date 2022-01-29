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
    assert ArgoConfig.hints() == {
        'repository': 'your-repository/name',
        'backend': 'argo-workflows'
    }


def test_sample_project_from_empty_config(tmp_empty):
    cfg = ArgoConfig.new('soopervisor.yaml', env_name='env')
    assert cfg.dict() == {
        'repository': 'your-repository/name',
        'mounted_volumes': None,
        'include': None,
        'exclude': None,
        'preset': None,
    }
