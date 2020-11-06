from soopervisor.airflow.config import AirflowConfig


def test_default_values(git_hash, session_sample_project):
    config = AirflowConfig().export(validate=False)
    assert config['lazy_import']
