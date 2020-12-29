import pluggy
# noinspection PyUnresolvedReferences
from checksum_url import Navigator, transfer_page
from plugins import register_navigator
from .url_navigator_plugin import UrlNavigator



@register_navigator()
class PipNavigator(UrlNavigator):

    NAME = 'pip'

    def __init__(self, browser, target_args):
        super(PipNavigator, self).__init__(browser, target_args)

    @classmethod
    def _translate_pip_urls(cls, urls):
        results = []
        for url in urls:
            file_name = url.split('/')[-1]
            first_letter = file_name[0]
            package_name = file_name.split('-')[0]

            new_url = f'https://pypi.io/packages/source/{first_letter}/{package_name}/{file_name}'

            results.append(new_url)

        return results

    def get_urls(self, sorted_by_version=True):

        results = super(PipNavigator, self).get_urls()

        if sorted_by_version:
            url_versions = [arg.split('#')[0] for arg in results]
            url_versions = self._urls_to_url_version(url_versions, self._args.version_regex)
            url_versions = self._sort_url_versions(url_versions)
            results = list(url_versions.keys())

        results = self._translate_pip_urls(results)

        return results




