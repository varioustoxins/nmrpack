import re

# noinspection PyUnresolvedReferences
import urllib
from urllib.parse import urlparse

from checksum_url import Navigator, transfer_page, OutputBase
# noinspection PyUnresolvedReferences
from plugins import register_output

from jinja2 import Template

from itertools import product

# Supported archive extensions from spack @0.17.
PRE_EXTS   = ["tar", "TAR"]
EXTS       = ["gz", "bz2", "xz", "Z"]
NOTAR_EXTS = ["zip", "tgz", "tbz", "tbz2", "txz"]

# Add PRE_EXTS and EXTS last so that .tar.gz is matched *before* .tar or .gz
ALLOWED_ARCHIVE_TYPES = [".".join(ext) for ext in product(
    PRE_EXTS, EXTS)] + PRE_EXTS + EXTS + NOTAR_EXTS

output_template = '''

class {{name}}(PythonPackage):
    """{{info|wordwrap(78)}}."""

    url = "{{url}}"
    
    {% for item in versions -%}
    version('{{item.version}}', {{item.digest_type}}='{{item.digest}}', 
             url='{{item.url}}'{{item.expand}})
    {% endfor%}
    
    {% if format == 'sdist'  %}
    depends_on('py-setuptools', type='build')
    {% endif %}
    

'''


@register_output()
class SpackOutput(OutputBase):

    NAME = "spack"

    def __init__(self, target_args=None):
        super(SpackOutput, self).__init__(target_args=target_args)
        self._info = {}
        self._hash_type = None

    def display_hash(self, target_url, _hash, url_field_length, index, num_urls=None, hash_type=None):

        self._hash_type = hash_type
        self._info[target_url] = _hash

    def _ordered_urls(self):
        for elem in self._info:
            yield elem

    def _check_digests_agree(self, url, extra_version_info, i):
        pip_digest = extra_version_info[url]['digests'][self.digest]
        download_digest = self._info[url]
        if not pip_digest == download_digest:
            msg = f"for url {url} {self.digest} from pip [{pip_digest}] and download [{download_digest}] don't agree"
            raise Exception(msg)

    def _should_expand(self, url):

        expand = False
        for extension in ALLOWED_ARCHIVE_TYPES:
            if url[-len(extension):] ==  extension:
                expand = True
                break

        return "" if expand else ", expand=False"

    def _build_version_data(self, extra_version_info):
        version_data = []
        for i, url in enumerate(self._ordered_urls()):

            version_info = extra_version_info[url]

            self._check_digests_agree(url, extra_version_info, i)

            file_type = version_info['type'] if 'type' in version_info else 'main_file'
            if file_type == 'main_file':
                data = {
                    'version': version_info['version'],
                    'digest_type': self.digest,
                    'digest': version_info['digests'][self.digest],
                    'expand': self._should_expand(url),
                    'url': url
                }
                version_data.append(data)
        return version_data

    def _is_pypi_package(self):

        result = False
        for url in self._info:
            if urlparse(url).netloc =='pypi.io':
                result = True
                break
        return result

    def finish(self, extra_package_info, extra_version_info):

        version_data = self._build_version_data(extra_version_info)

        extra_package_info = extra_package_info if extra_package_info else {}
        extra_info = {
            **extra_package_info,
            'url': extra_package_info['website'],
            'versions': version_data,
        }

        if self._is_pypi_package():
            extra_info['name'] =  f"Py{extra_info['name']}"
        if 'info' not in extra_info:
            extra_info['info'] = 'FIXME: Put a proper description of your package here (no info found)'

        template = Template(output_template)
        print(template.render(extra_info))
