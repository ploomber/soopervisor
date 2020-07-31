from ploomberci.script.script import generate_script
from ploomberci.script.ScriptConfig import ScriptConfig
from ploomberci.executors.LocalExecutor import LocalExecutor


def test_run_script(tmp_sample_project):
    config = ScriptConfig()
    script = generate_script(config=config)
    executor = LocalExecutor(project_root='.',
                             product_root='output',
                             script=script)
    executor.execute()
