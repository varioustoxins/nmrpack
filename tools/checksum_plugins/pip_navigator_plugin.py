import pluggy
# noinspection PyUnresolvedReferences
from checksum_url import CHECK_SUM_PROJECT, CHECK_SUM_IMPL, Navigator, transfer_page
from .url_navigator_plugin import UrlNavigator

pm = pluggy.PluginManager(CHECK_SUM_PROJECT)


class PipNavigator(UrlNavigator):

    def __init__(self, browser, target_args):
        super(PipNavigator, self).__init__(browser, target_args)

    def get_urls(self):

        result = super(PipNavigator, self).get_urls()

        return [arg.split('#')[0] for arg in result]


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
