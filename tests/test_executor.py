from soopervisor.script.script import generate_script
from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor.executors.LocalExecutor import LocalExecutor


def test_run_script(mock_git_hash, tmp_sample_project):
    config = ScriptConfig()
    script = generate_script(config=config)
    executor = LocalExecutor(project_root='.',
                             product_root='output',
                             script=script)
    executor.execute()
