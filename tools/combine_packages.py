import argparse
import sys
from collections import OrderedDict

from yaml import safe_load, safe_dump
from cmp_version import VersionString
from fnmatch import fnmatch


def parse_args():
    parser = argparse.ArgumentParser(description='calculate hashes from web links.',
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-p', '--prefer', dest='prefer', required=True, nargs=1,
                        help='glob defining a website to prefer for clashes')

    parser.add_argument('file_names', nargs='*')

    return parser.parse_args()


def choose_version(data, args, version):
    result = None
    if len(data) > 1:
        for datum in data:
            if fnmatch(datum['root_url'], f'*{args.prefer}*'):
                result = datum
                break
    else:
        result = data[0]

    if not result:
        print(f'Error: for version {version} there were {len(data)} choices, none were selected by {args.prefer}', file=sys.stderr)
        print('Exiting...', file=sys.stderr)
        sys.exit(1)
    return result


if __name__ == '__main__':

    args = parse_args()

    if len(args.file_names) < 1:
        print('Error: I need a least one file!', file=sys.stderr)
        print('Exiting...', file=sys.stderr)
        sys.exit(1)

    data = {}

    for file_name in args.file_names:
        with open(file_name) as file_h:
            for version, version_data in safe_load(file_h).items():
                data.setdefault(version,[]).append(version_data)

    result = {}
    for version, version_data in data.items():
        result[version] = choose_version(version_data, args, version)

    sorted_versions = sorted([(VersionString(version)) for version in result.keys()])

    output = {}

    for version in sorted_versions:
        version = str(version)
        output[version] = result[version]

    print(safe_dump(output, sort_keys=False))







