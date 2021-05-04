import shutil


def warn_if_not_installed(name):
    if not shutil.which(name):
        print(f'It appears you don\'t have {name} CLI installed, you need it '
              'to execute "invoke aws-lambda build"')
