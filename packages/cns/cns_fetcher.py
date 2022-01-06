
from spack.fetch_strategy import fetcher
from nmrpack.lib.fetchers import Password_Fetcher_Strategy_Base


@fetcher
class CNS_URL_Fetch_Strategy(Password_Fetcher_Strategy_Base):
    url_attr = 'cns_url'

    def __init__(self, **kwargs):

        super(CNS_URL_Fetch_Strategy, self).add_credentials_to_kwargs(kwargs)

        super(CNS_URL_Fetch_Strategy, self).__init__(**kwargs)




