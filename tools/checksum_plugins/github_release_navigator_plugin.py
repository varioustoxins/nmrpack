
from fnmatch import fnmatch

from cmp_version import VersionString
# noinspection PyUnresolvedReferences
from checksum_url import  Navigator, transfer_page, UNKNOWN_VERSION
# noinspection PyUnresolvedReferences
from plugins import register_navigator
from .url_navigator_plugin import UrlNavigator
# noinspection PyUnresolvedReferences
from checksum_url import TYPE, MAIN_FILE, EXTRA_FILE, FORMAT, VERSION, NAME, INFO, WEBSITE, DEPENDENCIES, DIGESTS
from urllib.parse import urlparse, unquote
from json import loads
from pathlib import Path


def split_url_to_path_and_file(target_url):
    url_parts = urlparse(target_url)
    full_path = Path(url_parts.path)
    path = full_path.parent
    file = full_path.name

    return path, file

def url_to_releases_url(target_url, has_file=False):
    url_parts = urlparse(target_url)
    url_parts = url_parts._replace(netloc=f'api.{url_parts.netloc}')

    if has_file:
        path, file = split_url_to_path_and_file(target_url)
        url_parts = url_parts._replace(path=f'/repos{path}/releases/{file}')
    else:
        url_parts = url_parts._replace(path=f'/repos{url_parts.path}/releases')
    target_url = url_parts.geturl()
    return target_url


@register_navigator()
class GithubReleaseNavigator(UrlNavigator):

    NAME = 'github_release'

    def __init__(self, browser, target_args):
        super(GithubReleaseNavigator, self).__init__(browser, target_args)
        self._extra_item_info = {}

    def login_with_form(self, target_url, username_password, form=None, verbose=0):

        target_url = url_to_releases_url(target_url)

        response = super(GithubReleaseNavigator, self).login_with_form(target_url, username_password)

        if response.status_code == 200:
            install_page_url = target_url
            install_page_response = transfer_page(self._target_session, install_page_url, username_password)
            self._root = loads(install_page_response.content)
            if install_page_response.status_code != 200:
                print(f'WARNING: response from {install_page_url} was {install_page_response.status_code}')


    @staticmethod
    def _parse_json_to_versions(release):

        url_path = urlparse(release['html_url']).path
        url_path = unquote(url_path)

        file_name = Path(url_path).parts[-1]
        file_name_parts = file_name.split('-')
        version = '-'.join(file_name_parts[1:])

        return VersionString(version)


    def get_urls(self, sorted_by_version=True):

        result = []

        target_args = self._args

        if target_args.root and not target_args.use_templates:
            if target_args.form:
                print('Warning: login form not supported for github, ignored...')
            for target_url in target_args.urls:
                result.append(target_url)
        elif target_args.use_templates:

            main_file_template = self._args.main_file_template if self._args.main_file_template else '*'
            for release in self._root:
                version = self._parse_json_to_versions(release)

                for asset in release['assets']:
                    download_url = asset['browser_download_url']
                    for template in target_args.urls:

                        file_name = download_url.rsplit('/', 1)[-1]
                        if fnmatch(file_name, template):

                            result.append(download_url)

                            main_file = MAIN_FILE if fnmatch(file_name, main_file_template) else EXTRA_FILE
                            file_name_parts = file_name.split('.')

                            file_format = file_name_parts[-1] if  len(file_name_parts) > 1 else 'unknown'

                            self._extra_item_info[download_url] = {
                                TYPE: main_file,
                                FORMAT: file_format,
                                VERSION: str(version),
                            }
        else:
            print(f'Bad combination of template {target_args.use_templates} and root {target_args.root}')

        return result

    def get_version(self, url):
        return self._extra_item_info[url]['version']

    def get_version_info(self, url):
        return self._extra_item_info[url]

    #TODO: is package info needed
    def get_package_info(self):
        return {}
