import shutil
import tempfile
import git
from models import Repository, Commit


def get_latest_commits_per_branch(url):
    """
    get_latest_commits_per_branch('https://github.com/edublancas/ds-template')
    """
    dir_ = tempfile.mkdtemp()
    print('dir:', dir_)

    # how to speed this up? clone bare repo?
    repo = git.Repo.clone_from(url, dir_)

    repo_db = Repository.get(Repository.url == url)

    # get the latest fetched commit
    latest_hashes = {commit.branch: commit.hash_ for commit
                     in Commit.select().where(Commit.repo == repo_db)}

    res = []

    for ref in repo.remotes.origin.refs:
        name = ref.name.replace('origin/', '')

        if name == 'HEAD':
            continue

        print('Checking out branch:', name)
        ref.checkout()
        commits = repo.iter_commits()

        # TODO: what happens when they delete then create a new branch
        # with an existing name?

        # new branch just pull latest commit
        if name not in latest_hashes:
            print('New branch...')
            latest = next(commits)
            print('Adding commit:', latest.hexsha)
            res.append({'branch': name, 'hash': latest.hexsha})
        else:
            print('Existing branch...')
            a_commit = next(commits)

            while a_commit.hexsha != latest[name]:
                print('Adding commit:', a_commit.hexsha)
                res.append({'branch': name, 'hash': a_commit.hexsha})
                a_commit = next(commits)

    # reverse order, older commits go first
    res = res[::-1]

    shutil.rmtree(dir_)

    return res
