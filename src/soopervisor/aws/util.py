import ast
import shutil
import os
import subprocess
from pathlib import Path


class ScriptExecutor:
    def __init__(self, debug=True):
        self._initial_working_directory = os.getcwd()
        self._names = []
        self._debug = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if not self._debug:
            for name in self._names:
                name = Path(name)
                if name.exists():
                    name.unlink()

        os.chdir(self._initial_working_directory)

    def execute(self, name):
        self._names.append(name)
        content = _env.get_template(name).render()
        Path(name).write_text(content)
        subprocess.run(['bash', name], check=True)

    def copy_template(self, path, **render_kwargs):
        path = Path(path)

        path.parent.mkdir(exist_ok=True, parents=True)

        # self._names.append(path)
        content = _env.get_template(str(path)).render(**render_kwargs)
        path.write_text(content)

    def inline(self, *code):
        subprocess.run(code, check=True)

    def cd(self, dir_):
        path = Path(dir_)

        if not path.exists():
            path.mkdir(exist_ok=True, parents=True)

        os.chdir(dir_)

    def append(self, name, dst):
        # TODO: keep a copy of the original content to restore if needed
        content = _env.get_template(name).render()
        original = Path(dst).read_text()
        Path(dst).write_text(original + '\n' + content)

    def copy(self, src):
        # TODO should replace it if exists
        path = Path(src)

        if path.is_file():
            shutil.copy(src, path.name)
        else:
            shutil.copytree(src, path.name)

    def create_if_not_exists(self, name):
        if not Path(name).exists():
            content = _env.get_template(f'default/{name}').render()
            Path(name).write_text(content)
            self._names.append(name)


def warn_if_not_installed(name):
    if not shutil.which(name):
        print(f'It appears you don\'t have {name} CLI installed, you need it '
              'to execute "invoke aws-lambda build"')


def declares_name(path, name):
    m = ast.parse(Path(path).read_text())
    return name in [getattr(node, 'name', None) for node in m.body]
