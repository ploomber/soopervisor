from soopervisor.kubeflow.config import KubeflowConfig


def test_default_values(session_sample_project):
    config = KubeflowConfig.defaults()

    assert config == {
        'backend': 'kubeflow',
        'repository': 'your-repository/name'
    }
