import sys
from fnmatch import fnmatch
from pathlib import Path

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

        file_name = Path(urlparse(url).path).parts[-1]

        return file_name

    @staticmethod
    def url_to_root(url):
        parts = list(urlparse(url))
        path = os.path.split(parts[2])
        parts[2] = os.path.join(*path[:-1])

        return urlunparse(parts)

    def get_when(self, extra_info, parts=False):

        when_parts=[]
        if 'os' in extra_info and extra_info['os'] != 'any':
            when_parts.append(f'os={extra_info["os"]}')
        if 'platform' in extra_info and extra_info['platform'] != '':
            when_parts.append(f'platform={extra_info["platform"]}')
        if 'target' in extra_info and extra_info['target'] != '':
            when_parts.append(f'target={extra_info["target"]}')


        return' '.join(when_parts)

    def finish(self, extra_package_info, extra_version_info):

        versions_and_urls = self.get_versions_and_urls(extra_version_info)

        result = {}
        for version in reversed(sorted(versions_and_urls)):



            main_url = self.get_main_url(versions_and_urls[version])
            if not main_url:
                print(f'Warning: no main url specified for version {version}', file=sys.stderr)
                print('          continuing..', file=sys.stderr)
                continue

            version_dict = {'version': str(version)}
            result[str(version)] = version_dict

            extra_version_info[main_url]['type'] = MAIN_FILE

            main_url = self.get_main_url(versions_and_urls[version])

            version_dict[self._urls_and_hashes[main_url][0]] = self._urls_and_hashes[main_url][1]
            version_dict['root_url'] = main_url
            resources = {}
            version_dict['resources'] = resources

            for url in sorted(extra_version_info):
                extra_info = extra_version_info[url]
                if extra_info['type'] == 'extra_file' and extra_info['version'] == version:
                    when = self.get_when(extra_info)

                    file_name = self.url_to_filename(url)


                    resources[file_name] = {'url': url,
                                            'hash': self._urls_and_hashes[url][1],
                                            'when': when
                                            }
                    if 'when' == '':
                        del resources[file_name]['when']



        print(yaml.dump(result, default_flow_style=False, sort_keys=False))




