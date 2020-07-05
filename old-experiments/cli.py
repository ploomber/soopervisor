import click
from models import db, Repository, Commit
from repo import get_latest_commits_per_branch
from container import run_in_container


@click.group()
def cli():
    pass


@cli.command()
def init():
    click.echo('Creating tables...')
    db.create_tables([Repository, Commit])


@cli.command()
@click.argument('url')
def add(url):
    click.echo('Adding url %s...' % url)
    Repository.create(url=url)


@cli.command()
def pull():
    click.echo('Checking repositories...')

    for repo in Repository.select():
        click.echo('Checking repo %s' % repo.url)
        commits = get_latest_commits_per_branch(repo.url)

        for commit in commits:
            click.echo('\tAdding commit from branch %s' % commit['branch'])
            Commit.create(repo=repo, branch=commit['branch'],
                          hash_=commit['hash'], status='pending')


@cli.command()
def run():
    """
    rm -f my.db
    python cli.py init
    python cli.py add https://github.com/edublancas/ds-template
    python cli.py pull
    python cli.py run
    """
    workspace = '/Users/Edu/ci-workspace/'
    click.echo('Running pending commits...')

    for commit in Commit.select().where(Commit.status == 'pending'):
        print(commit.hash_, commit.branch, commit.repo.url, workspace)
        run_in_container(commit.hash_, commit.branch, commit.repo.url, workspace)


# Commit.create(status='pending')


if __name__ == '__main__':
    cli()
