
import sys
import pathlib
import platform
from pathlib import Path
from types import MappingProxyType
from urllib.parse import urlparse

import spack.util.spack_yaml as syaml
from spack.directives import version
from spack.directives import resource


def url_to_extension(url):
    url_parts = urlparse(url)
    return ''.join(Path(url_parts.path).suffixes)

EXPANDABLE = '.tar.gz','.gz', '.gz', '.tgz'

def expandable(release, url):
    expand = False
    if 'expand' in release:
        expand = release['expand']
    elif url_to_extension(url) in EXPANDABLE:
        expand = True
    return expand


def build_when_clause(when_clause: dict):

    result =  {
        'platform': platform.system().lower(),
        'target': platform.machine().lower()
    }
    result.update(when_clause)
    return result

def read_releases(package, when_predicates = MappingProxyType({})):

    when_predicates = build_when_clause(when_predicates)

    package_root = str(pathlib.Path(__file__).parents[1])

    file_name = package_root / Path('packages') / Path(package) / Path('package.yaml')


    releases = syaml.load(open(file_name))

    for version_number, release in releases.items():
        url = f"{release['root_url']}"

        check_sum = None
        for check_sum_name in 'md5', 'sha256', 'sha512':
            if check_sum_name in release:
                check_sum = release[check_sum_name]
                break

        if 'url_type' in release:
            url_arg = release['url_type']
        else:
            url_arg = 'url'
        params = {url_arg : url,  check_sum_name : check_sum}

        expand = expandable(release, url)

        version(version_number, **params, expand=expand)

        # NOTE: we could be downloading resources we don't need because a variant is marked as not required
        # however, how to access variants from the spec at this point...
        if 'resources' in release and release['resources'] is not None:
            for file_name, info in release['resources'].items():

                url = info['url']
                sha256 = info['hash']
                when = info['when'] if 'when' in info else {}

                expand = expandable(info, url)

                use_resource = True
                for when_key, when_value in when.items():
                    if when_key in when_predicates:
                        if when[when_key] != when_predicates[when_key]:
                            use_resource = False
                            break

                if use_resource:
                    params = {'name': file_name, url_arg: url, 'sha256':sha256, 'expand': expand, 'destination': '.',
                             'placement': f'tmp_{file_name}', 'when': f'@{version_number}'}

                    resource(**params)




