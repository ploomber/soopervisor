import subprocess


def _run_command(cmd):
    result = subprocess.run(cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            check=True)
    return result.stdout.decode().replace('\n', '')


def get_git_hash(project_root):
    """Get git has in the project root
    """
    return _run_command('git rev-parse --short HEAD')


def get_previous_git_hash(project_root):
    """Get git hash from the previous commit
    """
    pass


def is_dirty(project_root):
    """Returns True if there are uncommitted changes
    """
    pass


def restore_previous(product_root):
    """Restore the products from the previous commit
    """
    pass
