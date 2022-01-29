from soopervisor.airflow.config import AirflowConfig


def test_default_values(session_sample_project):
    config = AirflowConfig.defaults()
    assert config == {
        'backend': 'airflow',
        'repository': 'your-repository/name'
    }
