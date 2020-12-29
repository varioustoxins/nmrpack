import pluggy
import sys
# noinspection PyUnresolvedReferences
from checksum_url import  Navigator, transfer_page, OutputBase
from plugins import register_output

@register_output()
class SimpleOutput(OutputBase):

    NAME = 'simple'

    def display_hash(self, target_url, _hash, url_field_length, index, num_urls=None):

        target_url = target_url.ljust(url_field_length)
        index_string = f'[{index}]'.ljust(5)
        sys.stdout.write(f"\rsum {index_string} {target_url} {_hash}")

    def finish(self):
        pass


