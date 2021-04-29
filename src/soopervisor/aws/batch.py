"""
Online DAG deployment using AWS Lambda
"""
import os
import importlib
from pathlib import Path
import boto3

from jinja2 import Environment, PackageLoader, StrictUndefined
from ploomber.util import default
from ploomber.spec import DAGSpec

from soopervisor import name_format
from soopervisor.aws.util import ScriptExecutor

_env = Environment(loader=PackageLoader('soopervisor', 'assets'),
                   undefined=StrictUndefined)
_env.filters['to_pascal_case'] = name_format.to_pascal_case


def main():
    if not Path('setup.py').exists():
        raise ValueError

    # if Path('aws-batch').exists():
    #     raise FileExistsError('aws-batch already exists, Rename or delete '
    #                           'to continue.')

    # if declares_name('tasks.py', 'aws_lambda_submit'):
    #     raise RuntimeError('tasks.py already has a "aws_lambda_submit" '
    #                        'function. Rename or delete to continue.')

    # check setup.py exists in the current dfolder

    pkg_name = default.find_package_name()
    version = importlib.import_module(pkg_name).__version__

    with ScriptExecutor() as e:
        # e.create_if_not_exists('tasks.py')
        e.inline('rm', '-rf', 'dist/', ' build/', 'aws-batch/')
        e.inline('python', '-m', 'build', '--sdist')

        filename = os.listdir('dist')[0]
        basename = filename.replace('.tar.gz', '')

        e.copy_template('aws-batch/Dockerfile',
                        filename=filename,
                        basename=basename)
        e.inline('cp', '-r', 'dist', 'aws-batch')
        e.inline('cp', 'environment.lock.yml', 'aws-batch')
        # e.append('aws-batch/tasks.py', 'tasks.py')
        e.cd('aws-batch')

        name = f'{pkg_name}:{version}'
        target = f'433232308104.dkr.ecr.us-east-1.amazonaws.com/{name}'

        e.inline('docker', 'build', '.', '--tag', name)
        e.inline('docker', 'tag', name, target)
        e.inline('docker', 'push', target)

        submit(job_def=name, target=target)

    print('Done. Files generated at aws-batch/. '
          'See aws-batch/README.md for details')
    print('Added submit command: invoke aws-batch-submit')

    # TODO:
    # test image after calling docker build by running ploomber status

    # to have dev prod parity, it's best to package as source distribution
    # that way we can include the requirements.txt file as top-level file
    # but then it becomes ambiguous if static files should go inside or out
    # the src/ or be top-level. at least the model and pipeline ahve to go
    # inside src/ to be able to load them using importlib resources. the other
    # ones (env.yaml) become a problem because if they are searched recursively
    # but when running in prod, the package is not installed in editable mode,
    # hence env.yaml at the root are not parents of the package. I need to
    # ensure that if the recursive srategy fails, the next thing is to
    # try to locate the root project directory, if none of this works, then
    # use the current directory. although the same strategy could be
    # applied to the model.joblib and pipeline.yaml to locate them
    # outside the pacakge

    # there is some mismatch in behavior when running from source and from a
    # package. for example, it might not be possible to find the root if
    # there is no requirementsx.txt or environment.yml

    # it's also kind of odd how to configure lcients inside the package
    # since relative paths are so to the file that contains them instead
    # of the current working directory

    # how do I make them behave in the same way? The idea is that if the
    # package (installed in editable mode) works locally, it should work
    # when installed as a package

    # another thing that might break is the non-existence of product parents,
    # the current implementation will break. perhaps we should generate
    # this on render? and also when downloading from cloud storage?


def submit(job_def, target):
    client = boto3.client("batch", region_name='us-east-1')

    print('submitting job definition...')
    client.register_job_definition(jobDefinitionName=job_def,
                                   type='container',
                                   containerProperties={
                                       "image": target,
                                       "memory": 2048,
                                       "vcpus": 2,
                                   })

    dag = DAGSpec.find().to_dag()

    job_ids = dict()

    print('Submitting jobs...')
    for name, task in dag.items():
        response = client.submit_job(
            jobName=name,
            jobQueue='ev2-queue-2',
            jobDefinition=job_def,
            dependsOn=[{
                "jobId": job_ids[name]
            } for name in task.upstream],
            containerOverrides={"command": ['ploomber', 'task', name]})

        job_ids[name] = response["jobId"]

    print('Done.')
