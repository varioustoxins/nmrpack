from packaging.version import Version
from tools.dependency_guesser import expand_version


def test_version_expansion():

    assert expand_version('1.0.0') == [Version('1.0.0')]
    assert expand_version('1.0.*') == [Version('1.0.0'), Version('1.0.9999')]
    assert expand_version('1.*') == [Version('1.0'), Version('1.9999')]
    assert expand_version('1.5.*') == [Version('1.5.0'), Version('1.5.9999')]


