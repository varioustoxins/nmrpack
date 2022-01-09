from icecream import ic
from spack.fetch_strategy import fetcher
from nmrpack.lib.fetchers import Password_Fetcher_Strategy_Base, find_configuration_file_in_args, ENVIRONMENT_AS_FILE
import spack.error as error

from os import environ

@fetcher
class CNS_URL_Fetch_Strategy(Password_Fetcher_Strategy_Base):
    url_attr = 'cns_url'

    def __init__(self, **kwargs):

        super(CNS_URL_Fetch_Strategy, self).add_credentials_to_kwargs(kwargs)

        super(CNS_URL_Fetch_Strategy, self).__init__(**kwargs)


def check_cns_config_file(*args,**kwargs):

    value = args[-1][0]

    if value == 'none':
        value = find_configuration_file_in_args()
    ic(value)


    if value == 'none' or value is None:
        msg = 'the option configuration is required and needs a value ' \
              'giving the path to a configuration file as an argument [configuration=<FILE_PATH>]'
        raise error.SpecError(msg)
    elif value == ENVIRONMENT_AS_FILE and ('NMRPACK_CNS_USER' in environ and 'NMRPACK_CNS_PASS'  in environ):
        pass
    elif value == ENVIRONMENT_AS_FILE and ('NMRPACK_CNS_USER' not in environ or 'NMRPACK_CNS_PASS' not in environ):
        raise error.SpecError(f'Error with configuration expected envirionment variables NMRPACK_CNS_USER and NMRPACK_CNS_PASS when configuration is {ENVIRONMENT_AS_FILE}')
    else:
        cns_result = CNS_URL_Fetch_Strategy.check_configuration_file(value)
        if cns_result != CNS_URL_Fetch_Strategy.OK:
            raise error.SpecError(f'Error with configuration {value} {cns_result}')


