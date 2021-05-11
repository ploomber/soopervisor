from pathlib import Path


def get(product):
    """Get data
    """
    Path(str(product)).touch()


def features(upstream, product):
    """Generate new features from existing columns
    """
    _ = upstream['get']
    Path(str(product)).touch()


def join(upstream, product):
    """Join raw data with generated features
    """
    _ = upstream['get']
    _ = upstream['features']
    Path(str(product)).touch()
