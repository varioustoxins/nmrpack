import yaml
import sys

EXIT_ERROR = 1

if __name__ == '__main__':

    if (nargs := len(sys.argv))  != 2:
        print(f'I need one file to run on got {nargs-1}', file=sys.stderr)
        print('Exiting...')
        sys.exit(EXIT_ERROR)

    RESOURCE_REMOVALS = (
        'NMRPipeL.tZ'
    )


    data = yaml.safe_load(open(sys.argv[1], 'rb'))

    for version in data:

        for elem in result[new_version]:

            if elem == 'resources':
                for resource in result[new_version]['resources']:
                    if resource in RESOURCE_REMOVALS and len(result[new_version]['resources'][resource]) < 3:
                        del data[version]['resources'][resource]

    print(yaml.dump(data, default_flow_style=False, sort_keys=False))

