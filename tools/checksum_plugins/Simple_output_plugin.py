import pluggy
import sys
# noinspection PyUnresolvedReferences
from checksum_url import  Navigator, transfer_page, OutputBase
from plugins import register_output

@register_output()
class SimpleOutput(OutputBase):

    NAME = 'simple'

    def __init__(self, target_args=None):
        super(SimpleOutput, self).__init__(target_args=target_args)

    def display_hash(self, target_url, _hash, url_field_length, index, num_urls=None, hash_type=None):

        target_url = target_url.ljust(url_field_length)
        index_string = f'[{index}]'.ljust(5)
        sys.stdout.write(f"\r{hash_type} {index_string} {target_url} {_hash}\n")


    def finish(self, extra_package_info, extra_version_info):
        pass


