from packaging.version import Version
from tools.dependency_guesser import expand_version_star, add_star_as_last_component, dependency_to_version_ranges, \
    MIN_VERSION, MAX_VERSION, extend_version_releases
import portion as p


def test_extend_version_releases():
    assert extend_version_releases(Version('1')) == Version('1.0.0')


def test_expand_version_star():

    assert expand_version_star('1.0.0') == [Version('1.0.0')]
    assert expand_version_star('1.0.*') == [Version('1.0.0'), Version('1.0.9999')]
    assert expand_version_star('1.*') == [Version('1.0'), Version('1.9999')]
    assert expand_version_star('1.5.*') == [Version('1.5.0'), Version('1.5.9999')]


def test_add_star_as_last_component():
    assert add_star_as_last_component('1.1') == '1.*'


def test_dependency_to_version_ranges():

    assert dependency_to_version_ranges('any == 1.0.0') == [p.closed(Version('1.0.0'), Version('1.0.0'))]
    assert dependency_to_version_ranges('any') == [p.closed(MIN_VERSION, MAX_VERSION)]
    assert dependency_to_version_ranges('any ~=2.2') == [p.closed(Version('2.2.0'),Version('2.2.9999'))]
    assert dependency_to_version_ranges('any !=2.2') == [p.closedopen(MIN_VERSION, Version('2.2.0')),
                                                         p.openclosed(Version('2.2.0'), MAX_VERSION)]
    assert dependency_to_version_ranges('any!=2.2.*') == [p.closedopen(MIN_VERSION, Version('2.2.0')),
                                                          p.openclosed(Version('2.2.9999'), MAX_VERSION)]

    assert dependency_to_version_ranges('any!=2.2.*') == [p.closedopen(MIN_VERSION, Version('2.2.0')),
                                                          p.openclosed(Version('2.2.9999'), MAX_VERSION)]

    # [0.0.0,2.2.0) | (2.2.9999,4.0.0) | (4.0.0,9999.9999.9999]
    expected = [p.closedopen(Version('0.0.0'),Version('2.2.0')),
                p.open(Version('2.2.9999'), Version('4.0')),
                p.openclosed(Version('4.0'), Version('9999.9999.9999'))]
    assert dependency_to_version_ranges('any!=2.2.*, !=4.0') == expected
