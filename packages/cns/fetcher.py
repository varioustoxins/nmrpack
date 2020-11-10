
import sys
from pathlib import Path
from spack.fetch_strategy import URLFetchStrategy
from spack.fetch_strategy import fetcher
import spack.util.spack_yaml as syaml




@fetcher
class CNS_URL_Fetch_Strategy(URLFetchStrategy):
    url_attr = 'cns_url'


    def __init__(self, **kwargs):

        if not 'cns_url' in kwargs:
            raise ValueError(f'CNS_URL_Fetch_Strategy requires a cns_url attribute, (i got {kwargs.keys()}):')

        super(CNS_URL_Fetch_Strategy, self).__init__(url=kwargs['cns_url'],**kwargs)


    def _find_configuration_file_in_args(self):
        result = None
        for arg in sys.argv:
            if arg.startswith('configuration='):
                result = arg.split('=')[1]
                break
        return result

    def _read_configuation_file(self, file_name):
        result = None
        try:
            result = syaml.load(open(file_name))
        except:
            pass
        return result

    def _check_configuration_file(self,file_name):

        result = True
        path = Path(file_name)
        if not path.is_file():
            print(f"ERROR: file {file_name} isn't a file")
            result=False

        if result:
            try:
                open(path, 'r')
            except:
                print(f"ERROR: couldn't read {file_name}")
                result = False

        return result


    def _check_configuration_data(self, file_name, parameters):
        result = True
        for parameter_name in 'user_name', 'password':
            if not parameter_name in parameters['cns']:
                print(f"ERROR: couldn't find parameter {parameter_name} in parameter_file {file_name}")
                result = False
                break
        return result


    def fetch(self):

        config_file_name =  self._find_configuration_file_in_args()
        config_data =  None
        if self._check_configuration_file(config_file_name):
            try:
                config_data = self._read_configuation_file(config_file_name)
            except Exception as e:
                print(f"ERROR: couldn't read config file because {' '.join(e.args())}")

        if config_data:
            if self._check_configuration_data(config_file_name, config_data):

                user_name = config_data['cns']['user_name']
                pass_word = config_data['cns']['password']

                self.curl.add_default_arg('-u')
                self.curl.add_default_arg(f'{user_name}:{pass_word}')

                return super(CNS_URL_Fetch_Strategy, self).fetch()

@fetcher
class ARIA_URL_Fetch_Strategy(URLFetchStrategy):
    url_attr = 'aria_url'


    def __init__(self, **kwargs):

        if not self.url_attr in kwargs:
            raise ValueError(f'ARIA_URL_Fetch_Strategy requires a aria_url attribute, (i got {kwargs.keys()}):')

        super(ARIA_URL_Fetch_Strategy, self).__init__(url=kwargs[self.url_attr],**kwargs)


    def _find_configuration_file_in_args(self):
        result = None
        for arg in sys.argv:
            if arg.startswith('configuration='):
                result = arg.split('=')[1]
                break
        return result

    def _read_configuation_file(self, file_name):
        result = None
        try:
            result = syaml.load(open(file_name))
        except:
            pass
        return result

    def _check_configuration_file(self,file_name):

        result = True
        path = Path(file_name)
        if not path.is_file():
            print(f"ERROR: file {file_name} isn't a file")
            result=False

        if result:
            try:
                open(path, 'r')
            except:
                print(f"ERROR: couldn't read {file_name}")
                result = False

        return result


    def _check_configuration_data(self, file_name, parameters):
        result = True
        for parameter_name in 'user_name', 'password':
            if not parameter_name in parameters['aria']:
                print(f"ERROR: couldn't find parameter {parameter_name} in parameter_file {file_name}")
                result = False
                break
        return result


    def fetch(self):

        config_file_name =  self._find_configuration_file_in_args()
        config_data =  None
        if self._check_configuration_file(config_file_name):
            try:
                config_data = self._read_configuation_file(config_file_name)
            except Exception as e:
                print(f"ERROR: couldn't read config file because {' '.join(e.args())}")

        if config_data:
            if self._check_configuration_data(config_file_name, config_data):

                user_name = config_data['aria']['user_name']
                pass_word = config_data['aria']['password']

                self.curl.add_default_arg('-u')
                self.curl.add_default_arg(f'{user_name}:{pass_word}')

                return super(ARIA_URL_Fetch_Strategy, self).fetch()