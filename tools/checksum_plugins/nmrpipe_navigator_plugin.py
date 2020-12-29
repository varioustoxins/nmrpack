import re

from bs4 import BeautifulSoup
from cmp_version import VersionString
# noinspection PyUnresolvedReferences
from checksum_url import  Navigator, transfer_page, UNKNOWN_VERSION
# noinspection PyUnresolvedReferences
from plugins import register_navigator
from .url_navigator_plugin import UrlNavigator


@register_navigator()
class NmrPipeNavigator(UrlNavigator):

    NAME = 'nmrpipe'

    def __init__(self, browser, target_args):
        super(NmrPipeNavigator, self).__init__(browser, target_args)
        self._version = UNKNOWN_VERSION

    def login_with_form(self, target_url, username_password, form=None, verbose=0):

        response = super(NmrPipeNavigator, self).login_with_form(target_url, username_password)

        if response.status_code == 200:
            install_page_url = f'{target_url}/install.html'
            install_page_response = transfer_page(self._target_session, install_page_url, username_password)
            if install_page_response.status_code == 200:
                content_soup = BeautifulSoup(install_page_response.content, 'html.parser')
                self._parse_page(content_soup)
            else:
                print(f'WARNING: response from {install_page_url} was {install_page_response.status_code}')

    @staticmethod
    def _parse_page(content_soup):
        version_regex = re.compile(r'\(NMRPipe Version ([0-9\.]+) Rev ([0-9\.]+).*\)')

        versions = set()
        for i in content_soup.body():
            match = version_regex.search(str(i))
            if match:
                versions.add('.'.join(match.group(1, 2)))

        if not versions:
            print('WANING: nop version string found setting version to 0.0.0')
            versions.append('0.0.0')
        elif versions and len(versions) > 1:
            print(f'WARNING: more than one version string found ({", ".join(versions)}), taking highest!')

        versions = [VersionString(version) for version in versions]
        versions.sort()

        result = versions[-1]

        return result

    def get_urls(self, sorted_by_version=True):

        result = super(NmrPipeNavigator, self).get_urls()

        return result


# class NmrPipeNavigatorFactory:
#
#     NAME = 'nmrpipe'
#
#     @CHECK_SUM_IMPL
#     def get_plugin_name(self):
#         return self.NAME
#
#     @CHECK_SUM_IMPL
#     def create_navigator(self, name):
#         if name.lower() == self.NAME:
#             return NmrPipeNavigator
#
#
# pm.register(NmrPipeNavigatorFactory())

