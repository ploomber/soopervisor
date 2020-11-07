import pytest

from soopervisor.argo.config import ArgoConfig, ArgoMountedVolume


@pytest.mark.parametrize(
    'claim_name, sub_path, expected_sub_path',
    [
        ['name', 'sub_path', 'sub_path'],
        ['name', '{{project_name}}', 'some_project'],
        ['name', 'data/{{project_name}}', 'data/some_project'],
    ],
)
def test_argo_mounted_volume_render(claim_name, sub_path, expected_sub_path):
    mv = ArgoMountedVolume(claim_name=claim_name, sub_path=sub_path)
    mv.render(project_name='some_project')

    assert mv.sub_path == expected_sub_path
    assert mv.claim_name == 'name'


@pytest.mark.parametrize(
    'mvs, expected_sub_paths',
    [
        [[
            {
                'claim_name': 'name',
                'sub_path': 'path'
            },
        ], ['path']],
        [[
            {
                'claim_name': 'name',
                'sub_path': '{{project_name}}'
            },
            {
                'claim_name': 'name',
                'sub_path': 'path'
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
        'claim_name': 'nfs',
        'sub_path': 'sample_project'
    }]
    assert cfg.lazy_import


def test_sample_project_from_path(session_sample_project):
    cfg = ArgoConfig.from_path('.')

    assert cfg.image == 'continuumio/miniconda3'
    assert cfg.mounted_volumes == [{
        'claim_name': 'nfs',
        'sub_path': 'sample_project'
    }]
