import io
import re
import ast
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('src/soopervisor/__init__.py', 'rb') as f:
    VERSION = str(
        ast.literal_eval(
            _version_re.search(f.read().decode('utf-8')).group(1)))


def read(*names, **kwargs):
    return io.open(join(dirname(__file__), *names),
                   encoding=kwargs.get('encoding', 'utf8')).read()


REQUIRES = ['click', 'tqdm', 'pydantic', 'boxsdk', 'Jinja2', 'pyyaml']
REQUIRES_TEST = ['pytest', 'Faker']
REQUIRES_DOC = []

setup(
    name='soopervisor',
    version=VERSION,
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],

    # Include any files in any package with these extensions
    # NOTE: for these files to be included, they have to be inside a proper
    # module (there has to be an __init__.py file)
    package_data={"": ["*.txt", "*.rst", "*.sql", "*.ipynb", "*.sh"]},
    install_requires=REQUIRES,
    extras_require={
        'dev': REQUIRES_TEST + REQUIRES_DOC,
    },
    setup_requires=[],
    entry_points={
        'console_scripts': ['soopervisor=soopervisor.cli:cli'],
    },
)
