from packaging.version import Version
from tools.dependency_guesser import expand_version, add_star_as_last_component


def test_version_expansion():

    assert expand_version('1.0.0') == ['1.0.0']
    assert expand_version('1.0.*') == ['1.0.0', '1.0.9999']
    assert expand_version('1.*') == ['1.0', '1.9999']
    assert expand_version('1.5.*') == ['1.5.0', '1.5.9999']


def test_add_star_as_last_component():
    assert add_star_as_last_component('1.1') == '1.*'


