import base64
import http
import os
import shutil
import sys
from pathlib import Path

from html2text import html2text


from mechanicalsoup import StatefulBrowser
import spack
from spack.fetch_strategy import URLFetchStrategy
from spack.fetch_strategy import fetcher, _needs_stage, FailedDownloadError
import spack.util.spack_yaml as syaml

from llnl.util.filesystem import  working_dir
from spack.util.web import SpackWebError
import llnl.util.tty as tty
import spack.util.url as url_util
from spack.config import get as get_config
from spack.util.web import uses_ssl, __UNABLE_TO_VERIFY_SSL, warn_no_ssl_cert_checking, _urlopen, _timeout, get_header
from six.moves.urllib.request import Request
from six.moves.urllib.error import URLError
import ssl

from collections import namedtuple

RequestInfo = namedtuple('RequestInfo', 'url timeout cafile capath context'.split())

class RequestModifier:
    def __call__(self, url, timeout, cafile=None, capath=None, context=None) -> RequestInfo:
        ...

class ArgModifier:
    def __call__(self, args):
        ...

def read_from_url(url, accept_content_type=None, request_modifier: RequestModifier=None) -> RequestInfo:

    parsed_url = url_util.parse(url)
    context = None

    verify_ssl = get_config('config:verify_ssl')

    # Don't even bother with a context unless the URL scheme is one that uses
    # SSL certs.
    if uses_ssl(parsed_url):
        if verify_ssl:
            if __UNABLE_TO_VERIFY_SSL:
                # User wants SSL verification, but it cannot be provided.
                warn_no_ssl_cert_checking()
            else:
                # User wants SSL verification, and it *can* be provided.
                context = ssl.create_default_context()  # novm
        else:
            # User has explicitly indicated that they do not want SSL
            # verification.
            if not __UNABLE_TO_VERIFY_SSL:
                context = ssl._create_unverified_context()

    req = Request(url_util.format(parsed_url))

    content_type = None
    is_web_url = parsed_url.scheme in ('http', 'https')

    if accept_content_type and is_web_url:
        # Make a HEAD request first to check the content type.  This lets
        # us ignore tarballs and gigantic files.
        # It would be nice to do this with the HTTP Accept header to avoid
        # one round-trip.  However, most servers seem to ignore the header
        # if you ask for a tarball with Accept: text/html.
        req.get_method = lambda: "HEAD"


    # Do the real GET request when we know it's just HTML.
    req.get_method = lambda: "GET"

    local_timeout = _timeout
    if request_modifier is not None:

        modified_request = request_modifier(req, timeout=_timeout, context=context)
        req = modified_request.url
        local_timeout = modified_request.timeout
        context = modified_request.context


    try:
        resp = _urlopen(req, timeout=local_timeout, context=context)

        content_type = get_header(resp.headers, 'Content-type')
        try:
            response = _urlopen(req, timeout=1000000, context=context)
        except URLError as err:
            raise SpackWebError('Download failed: {ERROR}'.format(
                ERROR=str(err)))

        if accept_content_type and not is_web_url:
            content_type = get_header(response.headers, 'Content-type')

        reject_content_type = (
                accept_content_type and (
                content_type is None or
                not content_type.startswith(accept_content_type)))

        if reject_content_type:
            tty.debug("ignoring page {0}{1}{2}".format(
                url_util.format(parsed_url),
                " with content type " if content_type is not None else "",
                content_type or ""))

            return None, None, None

        result = response.geturl(), response.headers, response

    except Exception as e:

        if e.code == http.HTTPStatus.UNAUTHORIZED:
            msg = f'''Error: Could not access {url} because access is not authorized [HTTP Error 401 - Unauthorized]
                             this may mean the user name or password in your configuration file is wrong out of date!'''
        else:
            msg = f'Error: Could not access {url} because of HTTP Error: {e.code} [{http.HTTPStatus(e.code).phrase}]'

        tty.msg(msg)

        raise SpackWebError(msg)

    return result

configuration=''
for arg in reversed(sys.argv):
    if arg.startswith('configuration='):
        configuration=arg
        break

def find_configuration_file_in_args():
    result = None
    for arg in sys.argv:
        if arg.startswith('configuration='):
            result = arg.split('=')[1]
            break
    return result

class NullRequestModifier:
    def __init__(self):
        pass

    def __call__(self, url, timeout, cafile=None, capath=None, context=None) -> RequestInfo:
        return RequestInfo(url, timeout, cafile, capath, context)

class BasicAuthorisationModifier:

    def __init__(self, username, password):
        self._username = username
        self._password = password

    def __call__(self, url, timeout, cafile=None, capath=None, context=None) -> RequestInfo:

        if not isinstance(url, Request):
            url = Request(url)

        base64string = base64.b64encode(('%s:%s' % (self._username, self._password)).encode('ascii'))
        authentication = f'Basic {base64string.decode("ascii")}'
        url.add_header("Authorization", authentication)

        return RequestInfo(url, timeout, cafile, capath, context)

class NullModifier(ArgModifier):
    def __call__(self, args):
        return args

class CurlAuthorisationModifier(ArgModifier):
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def __call__(self, args):
        args.append('-u')
        args.append(f'{self._username}:{self._password}')

        return args


class Password_Fetcher_Strategy_Base(URLFetchStrategy):

    OK = 'OK'

    def __init__(self, **kwargs):

        if self.url_attr not in kwargs:
            raise ValueError(f'{self.format_name.upper()} URL Fetch Strategy requires a {self.format_name}_url attribute, (i got {kwargs.keys()}):')

        kwargs['url']=kwargs[self.url_attr]


        super(Password_Fetcher_Strategy_Base, self).__init__(**kwargs)


    def _get_request_modifier(self):

        authentification = self.extra_options.setdefault('authentification', None)

        if authentification:
            if authentification != 'basic':
                raise ValueError(f'authentification must be basic or None, got {authentification}')

            have_username = 'username' in self.extra_options
            have_password = 'password' in self.extra_options

            if not have_username or not have_password:
                fetch_options = self.extra_options
                raise ValueError(f'username and password require for basic authentification got {fetch_options}')

            username = self.extra_options['username']
            password = self.extra_options['password']

            result = BasicAuthorisationModifier(username, password)
        else:
            result = NullRequestModifier()

        return result


    @_needs_stage
    def _fetch_urllib(self, url):

        save_file = None
        if self.stage.save_filename:
            save_file = self.stage.save_filename
        tty.msg('Fetching {0}'.format(url))

        request_modifier = self._get_request_modifier()
        # Run urllib but grab the mime type from the http headers
        try:
            url, headers, response = read_from_url(url, request_modifier=request_modifier)
        except SpackWebError as e:
            # clean up archive on failure.
            if self.archive_file:
                os.remove(self.archive_file)
            if save_file and os.path.exists(save_file):
                os.remove(save_file)
            msg = 'urllib failed to fetch with error {0}'.format(e)
            raise FailedDownloadError(url, msg)

        with open(save_file, 'wb') as _open_file:
            shutil.copyfileobj(response, _open_file)

        self._check_headers(str(headers))
        return None, save_file

    @_needs_stage
    def _fetch_curl(self, url):
        tty.msg('using curl fetch method')
        save_file = None
        partial_file = None
        if self.stage.save_filename:
            save_file = self.stage.save_filename
            partial_file = self.stage.save_filename + '.part'
        tty.msg('Fetching {0}'.format(url))
        if partial_file:
            save_args = ['-C',
                         '-',  # continue partial downloads
                         '-o',
                         partial_file]  # use a .part file
        else:
            save_args = ['-O']

        curl_args = save_args + [
            '-f',  # fail on >400 errors
            '-D',
            '-',  # print out HTML headers
            '-L',  # resolve 3xx redirects
            url,
        ]

        if not spack.config.get('config:verify_ssl'):
            curl_args.append('-k')

        if sys.stdout.isatty() and tty.msg_enabled():
            curl_args.append('-#')  # status bar when using a tty
        else:
            curl_args.append('-sS')  # show errors if fail

        connect_timeout = spack.config.get('config:connect_timeout', 10)

        if self.extra_options:
            cookie = self.extra_options.get('cookie')
            if cookie:
                curl_args.append('-j')  # junk cookies
                curl_args.append('-b')  # specify cookie
                curl_args.append(cookie)

            timeout = self.extra_options.get('timeout')
            if timeout:
                connect_timeout = max(connect_timeout, int(timeout))

        if connect_timeout > 0:
            # Timeout if can't establish a connection after n sec.
            curl_args.extend(['--connect-timeout', str(connect_timeout)])

        # Run curl but grab the mime type from the http headers
        curl = self.curl
        with working_dir(self.stage.path):
            curl_args = self.modify_curl_args(curl_args)
            headers = curl(*curl_args, output=str, fail_on_error=False)

        if curl.returncode != 0:
            # clean up archive on failure.
            if self.archive_file:
                os.remove(self.archive_file)

            if partial_file and os.path.exists(partial_file):
                os.remove(partial_file)

            if curl.returncode == 22:
                # This is a 404.  Curl will print the error.
                raise FailedDownloadError(
                    url, "URL %s was not found!" % url)

            elif curl.returncode == 60:
                # This is a certificate error.  Suggest spack -k
                raise FailedDownloadError(
                    url,
                    "Curl was unable to fetch due to invalid certificate. "
                    "This is either an attack, or your cluster's SSL "
                    "configuration is bad.  If you believe your SSL "
                    "configuration is bad, you can try running spack -k, "
                    "which will not check SSL certificates."
                    "Use this at your own risk.")

            else:
                # This is some other curl error.  Curl will print the
                # error, but print a spack message too
                raise FailedDownloadError(
                    url,
                    "Curl failed with error %d" % curl.returncode)

        self._check_headers(headers)
        return partial_file, save_file

    @classmethod
    def format_name(cls):
        return cls.url_attr.split('_')[0]

    def _read_configuation_file(self, file_name):
        result = None
        try:
            result = syaml.load(open(os.path.expanduser(file_name)))
        except:
            pass
        return result

    @classmethod
    def check_configuration_file(cls,file_name):

        result = cls.OK

        path = Path(file_name).expanduser()

        if not path.is_file():
            result = (f"file {file_name} isn't a file")

        if result == cls.OK:
            try:
                open(path, 'r')
            except Exception as e:
                result = f"couldn't read {file_name} because {e}"

        if result == cls.OK:
            try:
                data = syaml.load(open(path.absolute()))
            except Exception as e:
                result = f'there was an exception reading {file_name} {e}'

        if result == cls.OK:
            result = cls.check_configuration_data(data, file_name)

        return result

    @classmethod
    def check_configuration_data(cls, data, file_name):
        result = cls.OK
        for parameter_name in 'user_name', 'password':
            if parameter_name not in data[cls.format_name()]:
                result = f"couldn't find parameter {parameter_name} in parameter_file {file_name}"
                break
        return result

    def _existing_url(self, url):
        tty.debug('my Checking existence of {0}'.format(url))

        if spack.config.get('config:url_fetch_method') == 'curl':
            curl = self.curl
            # Telling curl to fetch the first byte (-r 0-0) is supposed to be
            # portable.
            curl_args = ['--stderr', '-', '-s', '-f', '-r', '0-0', url]
            if not spack.config.get('config:verify_ssl'):
                curl_args.append('-k')
            curl_args =  self.modify_curl_args(curl_args)
            _ = curl(*curl_args, fail_on_error=False, output=os.devnull)
            result =  curl.returncode == 0
        else:
            # Telling urllib to check if url is accessible
            try:
                request_modifier = self._get_request_modifier()
                url, headers, response = read_from_url(url, request_modifier=request_modifier)
            except spack.util.web.SpackWebError as e:
                msg = "Urllib fetch failed to verify url {0}".format(url)
                raise FailedDownloadError(url, msg)
            result = (response.getcode() is None or response.getcode() == 200)

        return result

    def fetch(self):

        username, password = self.get_credentials_from_configuration()

        self.add_credentials_to_curl(username, password)

        return super(Password_Fetcher_Strategy_Base, self).fetch()

    def add_credentials_to_curl(self, user_name, password):

        self.curl.add_default_arg('-u')
        self.curl.add_default_arg(f'{user_name}:{password}')

    def get_credentials_from_configuration(self):
        username = None
        password = None
        config_file_name = find_configuration_file_in_args()
        config_data = None
        try:
            config_data = self._read_configuation_file(config_file_name)
        except Exception as e:
            tty.msg(f"ERROR: couldn't read config file because {' '.join(e.args())}")


        if config_data:

            if self.check_configuration_data(config_data, config_file_name):
                username = config_data[self.format_name()]['user_name']
                password = config_data[self.format_name()]['password']

        return username, password

    def add_credentials_to_kwargs(self, kwargs):

        username, password = self.get_credentials_from_configuration()

        kwargs.setdefault('fetch_options',{})
        kwargs['fetch_options']['authentification'] = 'basic'
        kwargs['fetch_options']['username'] = username
        kwargs['fetch_options']['password'] = password

@fetcher
class ARIA_URL_Fetch_Strategy(Password_Fetcher_Strategy_Base):

    url_attr = 'aria_url'

    def __init__(self, **kwargs):

        if not self.url_attr in kwargs:
            raise ValueError(f'ARIA_URL_Fetch_Strategy requires an aria_url attribute, (i got {kwargs.keys()}):')

        super(ARIA_URL_Fetch_Strategy, self).add_credentials_to_kwargs(kwargs)

        super(ARIA_URL_Fetch_Strategy, self).__init__(**kwargs)



class DownloadFailedException(Exception):
    def __init__(self, msg):
        super(DownloadFailedException, self).__init__(msg)


def display_text(text, header):
    max_line_length = 0
    for line in text.split('\n'):
        line_length = len(line)
        if line_length > max_line_length:
            max_line_length = line_length

    under_length = max_line_length - len(header)
    if under_length <= 6:
        under_length = 6

    if under_length % 2:
        under_length += 1

    under_length //= 2

    tty.msg('-' * under_length + header + '-' * under_length)
    tty.msg()
    tty.msg(text)
    tty.msg()
    tty.msg('-' * (under_length * 2 + len(header)))

def display_response(response, header='response'):
    text = html2text(response.text)
    display_text(text, header)


PLATFORMS = ['darwin', 'linux', 'Irix', 'Ppc', 'SunOs', 'OSF1', ]
IGNORED_PLATFORMS = [
    'Irix',
    'Ppc',
    'SunOs',
    'OSF1',
]
IGNORED_PLATFORMS_LOWER = [platform.lower() for platform in IGNORED_PLATFORMS]

@fetcher
class XPLOR_URL_Fetch_Strategy(Password_Fetcher_Strategy_Base):

    url_attr = 'xplor_url'

    def __init__(self, **kwargs):

        if not self.url_attr in kwargs:
            raise ValueError(f'XPLOR_URL_Fetch_Strategy requires an xplor_url attribute, (i got {kwargs.keys()}):')

        super(XPLOR_URL_Fetch_Strategy, self).__init__(**kwargs)

    @staticmethod
    def _do_login(browser, target_url, username_password, form, verbose=0):
        username, password = username_password
        if form:
            form_selector, user_field, pass_field, selector = form

        response = browser.open(target_url)

        if verbose > 1:
            display_response(response, 'login-form')

        if response.status_code != 200:
            raise DownloadFailedException(f"couldn't open the password page\n\n{response.text}")
        if form:

            if not form_selector:
                form_selector = 'form'
                browser.select_form(form_selector)
            else:
                browser.select_form(form_selector, 0)

            browser[user_field] = username
            browser[pass_field] = password
            response = browser.submit_selected()

        if verbose > 1:
            display_response(response, 'login-response')

        if response.status_code != 200:
            raise DownloadFailedException(f"bad response from password page\n\n{response.text}")

        return browser



    def login_with_form(self, target_url, username_password, form=None, verbose=0):

        if not form:
            form = (0, 'UserName', 'Password', None)

        browser = self._browser

        self._target_url = target_url

        self._form = form

        self._do_login(browser, target_url, username_password, form, verbose)

    @staticmethod
    def get_platform(url):
        result = 'any'
        for name in PLATFORMS:
            if name in url.lower():
                result = name

        return result


    def fetch(self):

        username_password = self.get_credentials_from_configuration()

        self._browser = StatefulBrowser()

        self.login_with_form('https://nmr.cit.nih.gov/xplor-nih/download.cgi', username_password)

        return super(XPLOR_URL_Fetch_Strategy, self).fetch()

