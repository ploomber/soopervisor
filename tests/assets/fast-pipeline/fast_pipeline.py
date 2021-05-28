from pathlib import Path

from ploomber.clients import LocalStorageClient


def get_client():
    return LocalStorageClient('remote')


def root(product):
    Path(product).touch()


def another(product, upstream):
    root = upstream['root']
    Path(product).touch()
