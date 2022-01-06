

@fetcher
class ARIA_URL_Fetch_Strategy(Password_Fetcher_Strategy_Base):

    url_attr = 'aria_url'

    def __init__(self, **kwargs):

        super(ARIA_URL_Fetch_Strategy, self).add_credentials_to_kwargs(kwargs)

        super(ARIA_URL_Fetch_Strategy, self).__init__(**kwargs)