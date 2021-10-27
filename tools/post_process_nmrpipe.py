import yaml
import sys

EXIT_ERROR = 1

if __name__ == '__main__':

    if (nargs := len(sys.argv)) != 2:
        print(f'I need one file to run on got {nargs-1}', file=sys.stderr)
        print('Exiting...')
        sys.exit(EXIT_ERROR)

    RESOURCE_REMOVALS = (
        'NMRPipeL.tZ',
    )


    data = yaml.safe_load(open(sys.argv[1], 'rb'))

    result = {}
    for version in data:
        for elem, datum in data[version].items():
            if elem == 'resources':
                for resource in RESOURCE_REMOVALS:

                    if resource in data[version]['resources']:
                        del data[version]['resources'][resource]

    print(yaml.dump(data, default_flow_style=False, sort_keys=False))
