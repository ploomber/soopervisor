import subprocess
from pathlib import Path
from ploomberci import script


def test_simple_case(tmp_sample_project):
    code = script.generate_script(project_root=tmp_sample_project)
    Path('script.sh').write_text(code)
    subprocess.run(['bash', 'script.sh'])