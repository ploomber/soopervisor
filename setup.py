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

DESCRIPTION = ''

setup(
    name='soopervisor',
    version=VERSION,
    description=DESCRIPTION,
    long_description='%s\n%s' %
    (re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub(
        '', read('README.rst')),
     re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))),
    author='',
    author_email='',
    url='https://github.com/ploomber/soopervisor',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    package_data={"": ["*.txt", "*.rst", "*.sql", "*.ipynb", "*.sh"]},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=REQUIRES,
    extras_require={
        'dev': REQUIRES_TEST + REQUIRES_DOC,
    },
    setup_requires=[],
    entry_points={
        'console_scripts': ['soopervisor=soopervisor.cli:cli'],
    },
)
