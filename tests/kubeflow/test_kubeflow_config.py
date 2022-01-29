from soopervisor.kubeflow.config import KubeflowConfig


def test_default_values(session_sample_project):
    config = KubeflowConfig.hints()

    assert config == {
        'backend': 'kubeflow',
        'repository': 'your-repository/name'
    }
