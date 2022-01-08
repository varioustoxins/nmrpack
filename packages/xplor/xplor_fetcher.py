from spack.fetch_strategy import fetcher, Password_Fetcher_Strategy_Base, DownloadFailedException

from mechanicalsoup import StatefulBrowser
from html2text import html2text

PLATFORMS = ['darwin', 'linux', 'Irix', 'Ppc', 'SunOs', 'OSF1', ]
IGNORED_PLATFORMS = [
    'Irix',
    'Ppc',
    'SunOs',
    'OSF1',
]
IGNORED_PLATFORMS_LOWER = [platform.lower() for platform in IGNORED_PLATFORMS]

def display_response(response, header='response'):
    text = html2text(response.text)
    display_text(text, header)

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

        # if verbose > 1:
        #     display_response(response, 'login-form')

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

        # if verbose > 1:
        #     display_response(response, 'login-response')

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

