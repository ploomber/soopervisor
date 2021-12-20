def pprint(collection):
    return ', '.join(f"'{element}'" for element in sorted(collection))


def keys(expected, actual, error):
    missing = set(expected) - set(actual)

    if missing:
        raise ValueError(f'{error}: {pprint(missing)}')
