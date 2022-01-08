
from spack.fetch_strategy import fetcher
from nmrpack.lib.fetchers import Password_Fetcher_Strategy_Base
import spack.error as error

@fetcher
class CNS_URL_Fetch_Strategy(Password_Fetcher_Strategy_Base):
    url_attr = 'cns_url'

    def __init__(self, **kwargs):

        super(CNS_URL_Fetch_Strategy, self).add_credentials_to_kwargs(kwargs)

        super(CNS_URL_Fetch_Strategy, self).__init__(**kwargs)


def check_cns_config_file(*args,**kwargs):

    value = args[-1][0]
    if value == 'none':
        msg = 'the option configuration is required and needs a value ' \
              'giving the path to a configuration file as an argument [configuration=<FILE_PATH>]'
        raise error.SpecError(msg)
    else:
        cns_result = CNS_URL_Fetch_Strategy.check_configuration_file(value)
        if cns_result != CNS_URL_Fetch_Strategy.OK:
            raise error.SpecError(f'Error with configuration {value} {cns_result}')


