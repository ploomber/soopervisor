class GitRepo:
    def __init__(self, path):
        try:
            self.repo = git.Repo(path)
        except git.exc.InvalidGitRepositoryError:
            raise ValueError("The path is not a valid git repository")

    def get_git_hash(self, length=8):
        sha = self.repo.head.commit.hexsha
        return self.repo.git.rev_parse(sha, short=length)