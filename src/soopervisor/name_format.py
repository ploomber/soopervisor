def to_pascal_case(name):
    return ''.join([w.capitalize() for w in name.split('_')])
