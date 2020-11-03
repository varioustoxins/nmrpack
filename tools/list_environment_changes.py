
import subprocess
import os
from os import path
EXAMPLE_FILE = 'example.cshrc'
PREPEND='PREPEND'
NEW='NEW'

def fail_if_file_not_there(file_name):
   if not path.isfile(file_name):
       raise Exception(f"I can't find the file {file_name}")

def get_environment_change(prefix, file_name=EXAMPLE_FILE):

    result = []
    fail_if_file_not_there(path.join(prefix,file_name))

    pre_command = '''
          printenv
    '''

    post_command = f'''
          source ./{file_name} 
          printenv
    '''

    pre = subprocess.run(['/usr/bin/env', '-i', '/bin/csh', '-c', f"{pre_command}"], capture_output=True)
    post = subprocess.run(['/usr/bin/env', '-i', '/bin/csh','-c', f"{post_command}"], capture_output=True)

    pre_lines = set(pre.stdout.decode('ascii').split('\n'))
    post_lines = set(post.stdout.decode('ascii').split('\n'))

    pre_environment = split_environment(pre_lines)
    post_environment = split_environment(post_lines)

    new_keys = post_environment.keys() - pre_environment.keys()

    for key in new_keys:
        # prepends LD_LIBRARY_PATH, MANPATH, PATH, DYLD_LIBRARY_PATH - all PATHS
        if 'PATH' in key:
            for elem in post_environment[key].split(':'):
                result.append((key, PREPEND, elem))
        else:
            result.append((key, NEW, post_environment[key]))


    return result



def split_environment(pre_lines):
    result = {}
    for line in pre_lines:
        line=line.strip()
        if '=' in line:
            name, value = line.split('=', 1)
            result[name] = value
        elif len(line):
            result[line] = None

    return result



if __name__ == '__main__':

    from tabulate import tabulate

    prefix = os.getcwd()
    result = get_environment_change(prefix)

    print(tabulate(result,headers=['Variable', 'Action','Value']))