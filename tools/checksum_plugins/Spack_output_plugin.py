import re

# noinspection PyUnresolvedReferences
from checksum_url import Navigator, transfer_page, OutputBase
# noinspection PyUnresolvedReferences
from plugins import register_output

from jinja2 import Template

output_template = '''


class {{name}}(PythonPackage):
    """{{info|wordwrap(78)}}."""

    pypi     = "{{pypi}}"
    
    {% for item in versions -%}
    version('{{item.version}}', {{item.digest_type}}='{{item.digest}}, 
             url={{item.url}}, expand={{item.expand}}')
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
        self._info = []

    def display_hash(self, target_url, _hash, url_field_length, index, num_urls=None):

        self._info.append((target_url, _hash, url_field_length, index, num_urls))

    def _ordered_urls(self):
        for elem in self._info:
            yield elem[0]

    def _check_digests_agree(self, url, extra_version_info, i):
        pip_digest = extra_version_info[url]['digests'][self.digest]
        download_digest = self._info[i][1]
        if not pip_digest == download_digest:
            msg = f"for url {url} {self.digest} from pip [{pip_digest}] and download [{download_digest}] don't agree"
            raise Exception(msg)

    def _get_preferred_package_type(self, extra_version_info):
        latest_url = list(self._ordered_urls())[0]
        return extra_version_info[latest_url]['format']

    def _should_expand(self, url):
        expand = '.tgz', '.tar.gz', '.tz', '.zip'

        result = False
        for extension in expand:
            if url[:-len(extension)] ==  extension:
                result = True
                break

        return result

    def _build_version_data(self, extra_version_info):
        version_data = []
        for i, url in enumerate(self._ordered_urls()):

            version_info = extra_version_info[url]

            self._check_digests_agree(url, extra_version_info, i)

            if version_info['type'] == 'main_file':
                data = {
                    'version': version_info['version'],
                    'digest_type': self.digest,
                    'digest': version_info['digests'][self.digest],
                    'expand': self._should_expand(url),
                    'url': url
                }
                version_data.append(data)
        return version_data

    @staticmethod
    def _get_pypi_url_path(url):
        url_segments = url.split('/')
        result = '/'.join(url_segments[-2:])

        return result

    @staticmethod
    def _filter_versions_by_package_type(version_data, extra_version_info, preferred_package_type):
        result = []
        for version_datum in version_data:
            package_format = extra_version_info[version_datum['url']]['format']
            if package_format == preferred_package_type:
                result.append(version_datum)

        return result

    def finish(self, extra_package_info, extra_version_info):

        preferred_package_type = self._get_preferred_package_type(extra_version_info)

        pattern = re.compile(r'(?<!^)(?=[A-Z])')
        snake_name = pattern.sub('-', extra_package_info['name']).lower()
        print(f'# package-name: py-{snake_name}')

        latest_version_url = self._info[0][0]

        version_data = self._build_version_data(extra_version_info)
        version_data = self._filter_versions_by_package_type(version_data, extra_version_info, preferred_package_type)

        extra_info = {
            **extra_package_info,
            'pypi': self._get_pypi_url_path(latest_version_url),
            'versions': version_data,
            'format':  preferred_package_type
        }

        template = Template(output_template)
        print(template.render(extra_info))
