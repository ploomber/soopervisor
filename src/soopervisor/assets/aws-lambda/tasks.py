@task
def aws_lambda_build(c):
    """Build Docker image for AWS Lambda deployment
    """
    c.run('pytest aws-lambda', pty=True)

    c.run('rm -rf dist/ build/')
    c.run('python -m build --wheel .')
    c.run('cp -r dist aws-lambda')

    with c.cd('aws-lambda'):
        c.run('sam build')
