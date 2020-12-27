import pluggy
# noinspection PyUnresolvedReferences
from checksum_url import CHECK_SUM_PROJECT, CHECK_SUM_IMPL, Navigator, transfer_page
from .url_navigator_plugin import UrlNavigator

pm = pluggy.PluginManager(CHECK_SUM_PROJECT)


class PipNavigator(UrlNavigator):

    def __init__(self, browser, target_args):
        super(PipNavigator, self).__init__(browser, target_args)

    @classmethod
    def _update_dict(cls, targets, sources):
        return target

    def get_urls(self, sorted_by_version=True):

        result = super(PipNavigator, self).get_urls()

        if sorted_by_version:
            url_versions = [arg.split('#')[0] for arg in result]
            url_versions = self._urls_to_url_version(url_versions, self._args.version_regex)
            url_versions = self._sort_url_versions(url_versions)
            result = list(url_versions.keys())

        return result


class PipNavigatorFactory:

    NAME = 'pip'

    @CHECK_SUM_IMPL
    def get_plugin_name(self):
        return f'{self.NAME}'

    @CHECK_SUM_IMPL
    def create_navigator(self, name):
        if name.lower() == self.NAME:
            return PipNavigator


pm.register(PipNavigatorFactory())
