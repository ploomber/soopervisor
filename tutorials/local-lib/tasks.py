from pathlib import Path


def task(product):
    """Add description here
    """
    # put the import here to prevent it from breaking
    # when loading the dag
    from functions import print_message
    print_message()

    Path(product).touch()
