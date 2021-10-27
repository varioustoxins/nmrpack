import sys
from fnmatch import fnmatch

import pluggy

# noinspection PyUnresolvedReferences
from checksum_url import Navigator, transfer_page, OutputBase, MAIN_FILE
from plugins import register_output
from cmp_version import VersionString

import yaml
import os
from urllib.parse import urlparse, urlunparse

class HashableVersionString(VersionString):

    def __hash__(self):
        return hash(repr(self))


@register_output()
class NmrpackOutput(OutputBase):

    NAME = 'nmrpack'

    def __init__(self, target_args=None):
        super(NmrpackOutput, self).__init__(target_args=target_args)
        self._urls_and_hashes = {}

    def display_hash(self, target_url, hash, url_field_length, index, num_urls=None, hash_type='unknown'):

        self._urls_and_hashes[target_url] = (hash_type, hash)

    @staticmethod
    def get_versions_and_urls(extra_version_infos):
        result = {}

        for url, extra_info in extra_version_infos.items():
            result.setdefault(HashableVersionString(extra_info['version']), {})[url] =  extra_info

        return result

    def get_main_url(self, urls_extra_info):

        result = None
        for url, extra_info in urls_extra_info.items():
            if extra_info['type'] == 'main_file':
                result=url
                break

        if not result and self._target_args and self._target_args.main_file_template:
            filename_template = self._target_args.main_file_template
            for url, extra_info in urls_extra_info.items():
                file_name = self.url_to_filename(url)

                if fnmatch(file_name, filename_template):
                    result=url
                    break

        return result

    @staticmethod
    def url_to_filename(url):
        return os.path.basename(urlparse(url).path)

    @staticmethod
    def url_to_root(url):
        parts = list(urlparse(url))
        path = os.path.split(parts[2])
        parts[2] = os.path.join(*path[:-1])

        return urlunparse(parts)


    def finish(self, extra_package_info, extra_version_info):

        versions_and_urls = self.get_versions_and_urls(extra_version_info)

        result = {}
        for version in sorted(versions_and_urls):
            version_dict = {'version': str(version)}
            result[str(version)] = version_dict

            main_url = self.get_main_url(versions_and_urls[version])
            if not main_url:
                print('Error: no main url specified', file=sys.stderr)
                print('Exiting...', file=sys.stderr)
                sys.exit(1)
            extra_version_info[main_url]['type'] = MAIN_FILE

            version_dict['install_file'] = self.url_to_filename(self.get_main_url(versions_and_urls[version]))

            version_dict[self._urls_and_hashes[main_url][0]] = self._urls_and_hashes[main_url][1]
            version_dict['root_url'] = self.url_to_root(self.get_main_url(versions_and_urls[version]))
            resources = {}
            version_dict['resources'] = resources



            for url in sorted(extra_version_info):
                extra_info = extra_version_info[url]
                if extra_info['type'] == 'extra_file':
                    file_name = self.url_to_filename(url)
                    root_url = self.url_to_root(url)
                    resources[file_name]= [root_url, self._urls_and_hashes[url][1]]


        print(yaml.dump(result, default_flow_style=False, sort_keys=False))




