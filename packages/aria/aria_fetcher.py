
from spack.fetch_strategy import fetcher
from nmrpack.lib.fetchers import Password_Fetcher_Strategy_Base, find_configuration_file_in_args, ENVIRONMENT_AS_FILE
from spack import error
from os import environ

@fetcher
class ARIA_URL_Fetch_Strategy(Password_Fetcher_Strategy_Base):

    url_attr = 'aria_url'

    def __init__(self, **kwargs):

        super(ARIA_URL_Fetch_Strategy, self).add_credentials_to_kwargs(kwargs)

        super(ARIA_URL_Fetch_Strategy, self).__init__(**kwargs)


def check_aria_config_file(*args,**kwargs):

    do_check = args[-1][0]

    if do_check:
        value = find_configuration_file_in_args()
        if value == 'none':
            msg = 'the option configuration is required and needs a value ' \
                  'giving the path to a configuration file as an argument [configuration=<FILE_PATH>]'
            raise error.SpecError(msg)
        elif value == ENVIRONMENT_AS_FILE and ('NMRPACK_ARIA_USER' in environ and 'NMRPACK_ARIA_PASS' in environ):
            pass
        else:
            result = ARIA_URL_Fetch_Strategy.check_configuration_file(value)
            if result != ARIA_URL_Fetch_Strategy.OK:
                raise error.SpecError(f'Error with configuration {value} {result}')
