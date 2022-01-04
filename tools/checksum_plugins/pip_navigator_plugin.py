# noinspection PyUnresolvedReferences
from checksum_url import Navigator, transfer_page
# noinspection PyUnresolvedReferences
from plugins import register_navigator
from .url_navigator_plugin import UrlNavigator
# noinspection PyUnresolvedReferences
from checksum_url import TYPE, MAIN_FILE, EXTRA_FILE, EXPAND , VERSION, NAME, INFO, WEBSITE, DEPENDENCIES, DIGESTS
from http import HTTPStatus
import json


OK = HTTPStatus.OK


@register_navigator()
class PipNavigator(UrlNavigator):

    NAME = 'pip'

    def __init__(self, browser, target_args):
        super(PipNavigator, self).__init__(browser, target_args)
        self._raw_extra_info ={}
        self._long_to_short_urls = {}
        self._short_url_release = {}

    @staticmethod
    def _dump_json(json_data):
        print(json.dumps(json_data, indent=4, sort_keys=True))

    @staticmethod
    def _get_version(url):

        last = str(url.split('-')[1])

        extensions = ['.tar.gz', '.whl', '.zip']

        version =  None
        for extension in extensions:
            len_extension = len(extension)
            if last[-len_extension:] == extension:
                version = last[:-len_extension]
                break

        if not version:
            raise Exception(f"couldn't recognise version for {url}")

        return version

    @staticmethod
    def _root_url_to_json(root):
        url_components = root.split('/')

        result = None

        url_components =  url_components[:5]

        if not(url_components[2] != 'pypi.org'):
            url_components[-2] = 'pypi'
            url_components.append('json')

            result = '/'.join(url_components)

        return result

    def login_with_form(self, root, password, form=None, verbose=False):
        result = super(PipNavigator, self).login_with_form(root, password, form, verbose)

        info_url = self._root_url_to_json(root)

        if not info_url:
            print(f'WARNING: url is {root} not interpretable as a pypi url,'
                  f' no extra information will be gathered')

        response = None
        if info_url:
            response = transfer_page(self._target_session, info_url)

        if response.status_code != OK:
            print(f"WARNING: couldn't down;load info from {info_url}")
        else:
            self._raw_extra_info = json.loads(response.content)

        return result

    @staticmethod
    def invert_dict(in_dict):
        return {value : key for key, value in in_dict.items()}

    @classmethod
    def _translate_pip_urls(cls, urls):
        results = {}
        for url in urls:
            file_name = url.split('/')[-1]
            first_letter = file_name[0]
            package_name = file_name.split('-')[0]

            new_url = f'https://pypi.io/packages/source/{first_letter}/{package_name}/{file_name}'

            results[url] = new_url

        return results

    def get_urls(self, sorted_by_version=True):

        long_urls = super(PipNavigator, self).get_urls()
        long_urls = [url.split('#')[0] for url in long_urls]

        long_url_versions = self._urls_to_url_version(long_urls, self._args.version_regex)
        if sorted_by_version:
            long_url_versions = self._sort_url_versions(long_url_versions)

        long_urls_to_short_pip = self._translate_pip_urls(long_url_versions)

        for release in self._raw_extra_info['releases']:
            install_formats = self._raw_extra_info['releases'][release]
            for install_format in install_formats:
                long_url = install_format['url']
                if long_url in long_urls_to_short_pip.keys():
                    short_url = long_urls_to_short_pip[long_url]
                    self._short_url_release[short_url] = install_format
                    self._short_url_release[short_url]['version'] = long_url_versions[long_url]

        results = long_urls_to_short_pip.values()

        return results

    def get_extra_info(self, url):

        result = {
                    TYPE: MAIN_FILE,
                    EXPAND: False,
                    VERSION: self._get_version(url),
                    DEPENDENCIES: self._raw_extra_info['info']['requires_dist'],
                    DIGESTS: self._short_url_release[url]['digests']

        }

        return result

    def get_package_info(self):

        return {
            NAME: self._raw_extra_info['info']['name'],
            INFO: self._raw_extra_info['info']['summary'],
            WEBSITE: self._raw_extra_info['info']['home_page'],
            DEPENDENCIES: []
        }

