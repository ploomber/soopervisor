from soopervisor import name_format


def test_to_pascal_case():
    assert name_format.to_pascal_case('ml_online') == 'MlOnline'
