from soopervisor.script.ScriptConfig import ScriptConfig
from soopervisor.executors.LocalExecutor import LocalExecutor


def test_run_script(git_hash, tmp_sample_project):
    executor = LocalExecutor(project_root='.',
                             product_root='output',
                             script=ScriptConfig().to_script())
    executor.execute()
