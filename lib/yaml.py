
import sys
import pathlib
from pathlib import Path
import spack.util.spack_yaml as syaml
from spack.directives import version
from spack.directives import resource


def read_releases(package):

    package_root = str(pathlib.Path(__file__).parents[1])

    file_name = package_root / Path('packages') / Path(package) / Path('package.yaml')


    releases = syaml.load(open(file_name))

    for release_id, release in releases.items():
        url = f"{release['root_url']}/{release['install_file']}"
        version_number = release['version']

        for check_sum_name in 'md5', 'sha256', 'sha512':
            if check_sum_name in release:
                check_sum = release[check_sum_name]

        if 'url_type' in release:
            url_arg = release['url_type']
        else:
            url_arg = 'url'
        params = {url_arg : url,  check_sum_name : check_sum}

        expand=False
        if 'expand' in release:
            expand= release['expand']
        version(version_number, **params, expand=expand)

        # NOTE: we could be downloading resources we don't need because a variant is marked as not required
        # however, how to access variants from the spec at this point...
        if 'resources' in release:
            for file_name, (url, md5) in release['resources'].items():
                url = f'{url}/{file_name}'
                resource(name=file_name, url=url, md5=md5, expand=False, destination='.',
                         placement=f'tmp_{file_name}', when=f'@{version_number}')
    return releases
