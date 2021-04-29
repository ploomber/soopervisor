@task
def aws_batch_submit(c):
    """Build Docker image for AWS Batch deployment
    """
    c.run('rm -rf dist/ build/')
    c.run('python -m build --wheel .')
    c.run('cp -r dist aws-batch')

    with c.cd('aws-batch'):
        c.run('docker build .')
