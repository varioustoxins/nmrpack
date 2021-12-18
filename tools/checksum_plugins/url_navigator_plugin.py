import pluggy
import sys
# noinspection PyUnresolvedReferences
from checksum_url import  Navigator, transfer_page
from plugins import register_navigator
# noinspection PyProtectedMember
from bs4 import BeautifulSoup, SoupStrainer
from fnmatch import fnmatch



def check_root_exists_or_exit(root, target_session, username_password=(None, None)):

    response = transfer_page(target_session, root, username_password)

    if response.status_code != 200:
        print(f"the web site {root} isn't accessible")
        print('exiting...')
        sys.exit()

    return response


def get_urls_for_templates(target_page, templates):
    target_urls = []
    result = []
    for link in BeautifulSoup(target_page.content, parse_only=SoupStrainer('a'), features="html.parser"):

        if link.has_attr('href'):
            target_urls.append(link['href'])

        result = set()
        for target_url in target_urls:
            for template in templates:
                if fnmatch(target_url.rsplit('/', 1)[-1], template):
                    result.add(target_url)

    return list(result)


def get_urls_from_args(root, target_urls):
    if root:
        target_urls = [f'{root}/{target_url}' for target_url in target_urls]

    return target_urls

@register_navigator()
class UrlNavigator(Navigator):

    NAME = 'url'

    def __init__(self, browser, target_args):
        super(UrlNavigator, self).__init__(browser, target_args)
        self._root = None

    def login_with_form(self, root, password, form=None, verbose=0):
        self._root = check_root_exists_or_exit(root, self._target_session, password)
        return self._root

    def get_urls(self, sorted_by_version=True):
        target_args = self._args

        result = []
        if target_args.form and target_args.root and not target_args.use_templates:
            for target_url in target_args.urls:
                result.append(target_url)
        elif target_args.root and not target_args.use_templates:
            for target_url in get_urls_from_args(target_args.root, target_args.urls):
                result.append(target_url)
        elif target_args.use_templates:
            page = transfer_page(self._target_session, target_args.root, target_args.password)

            for target_url in get_urls_for_templates(page, target_args.urls):
                result.append(target_url)
        else:
            print(f'Bad combination of template {target_args.use_templates} and root {target_args.root}')

        return result

    def get_version(self, url):
        return None

    def get_extra_info(self, url):
        return {}

    def get_package_info(self):
        return 'none available'


