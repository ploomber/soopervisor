from ploomberci.script.script import generate_script
from ploomberci.script.ScriptConfig import ScriptConfig


def test_generate_default_script():
    config = ScriptConfig()
    assert generate_script(config=config)