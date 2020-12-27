import pluggy
import sys
# noinspection PyUnresolvedReferences
from checksum_url import CHECK_SUM_PROJECT, CHECK_SUM_IMPL, Navigator, transfer_page, OutputBase

pm = pluggy.PluginManager(CHECK_SUM_PROJECT)


class SimpleOutput(OutputBase):

    def display_hash(self, target_url, _hash, url_field_length, index, num_urls=None):

        target_url = target_url.ljust(url_field_length)
        index_string = f'[{index}]'.ljust(5)
        sys.stdout.write(f"\rsum {index_string} {target_url} {_hash}")

    def finish(self):
        pass


class SimpleOutputFactory:

    NAME = 'simple'

    @CHECK_SUM_IMPL
    def create_output(self, name):
        if name == self.NAME or name is None:
            return SimpleOutput()

    @CHECK_SUM_IMPL
    def get_output_name(self):
        return f'{self.NAME} [default]'


pm.register(SimpleOutputFactory())
