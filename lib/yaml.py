
import sys
import pathlib
from pathlib import Path
import spack.util.spack_yaml as syaml


def read_releases(package,version, resource, verbose = False):
    package_root = str(pathlib.Path(__file__).parents[1])

    file_name = package_root / Path('packages') / Path(package) / Path('package.yaml')

    # if verbose:
    #     print(f'reading package definitions from {file_name}')
    releases =  syaml.load(open(file_name))

    for release_id, release in releases.items():
        url = f"{release['root_url']}/{release['install_file']}"
        version_number = release['version']
        check =  release['md5']
        # if verbose:
        #     print(f'creating version definition {version_number} url: {url} : check {check}')
        if 'url_type' in release:
            url_arg = release['url_type']
        else:
            url_arg = 'url'
        url_param = {url_arg : url}
        expand=False
        if 'expand' in release:
            expand= release['expand']
        version(version_number, **url_param, md5=check, expand=expand)

        # NOTE: we could be downloading resources we don't need because a variant is marked as not required
        # however, how to access variants from the spec at this point...
        if 'resources' in release:
            for file_name, (url, md5, variant_name) in release['resources'].items():
                url = f'{url}/{file_name}'
                if verbose:
                    print(f'Loading resource definition {version_number} url: {url} : check {md5}')
                resource(name=file_name, url=url, md5=md5, expand=False, destination='',
                         placement=f'tmp_{file_name}', when=f'@{version_number}')
