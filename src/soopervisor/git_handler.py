from git import Repo
from git.exc import InvalidGitRepositoryError


class GitRepo:
    def __init__(self, path):
        try:
            self.repo = Repo(path)
        except InvalidGitRepositoryError:
            raise ValueError("The path is not a valid git repository")

    def get_git_hash(self, length=8):
        sha = self.repo.head.commit.hexsha
        return self.repo.git.rev_parse(sha, short=length)


    def get_previous_git_hash(self, length=8):
        """Get git has in the project root
        """
        pass


    def is_dirty(self):
        """Returns True if there are uncommitted changes
        """
        pass
