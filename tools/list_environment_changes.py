

import os
from ..lib.environment import get_environment_change

EXAMPLE_FILE = 'example.cshrc'



if __name__ == '__main__':

    from tabulate import tabulate

    prefix = os.getcwd()
    result = get_environment_change(prefix, EXAMPLE_FILE)

    print(tabulate(result,headers=['Variable', 'Action','Value']))