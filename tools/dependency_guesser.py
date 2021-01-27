import argparse
import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from requirements_detector import find_requirements
from packaging.requirements import Requirement
from packaging.version import Version
from operator import and_
from functools import reduce

import requests
from requirements_detector.detect import RequirementsNotFound
from tqdm import tqdm

import portion as p

STORE_TRUE = 'store_true'

suffixes = ['B ', 'KB', 'MB', 'GB', 'TB', 'PB']

MAX_DIGITS = 4  # allows for year based versions
MIN_VERSION_COMPONENT = 0
MAX_VERSION_COMPONENT = int('9' * 4)
MIN_VERSION_COMPONENT_STR = str(MIN_VERSION_COMPONENT)
MAX_VERSION_COMPONENT_STR = str(MAX_VERSION_COMPONENT)
MAX_VERSION = Version(f'{MAX_VERSION_COMPONENT}.{MAX_VERSION_COMPONENT}.{MAX_VERSION_COMPONENT}')
MIN_VERSION = Version(f'{MIN_VERSION_COMPONENT}.{MIN_VERSION_COMPONENT}.{MIN_VERSION_COMPONENT}')


def human_size(number_bytes):
    index = 0
    while number_bytes >= 1024 and index < len(suffixes)-1:
        number_bytes /= 1024.
        index += 1
    f = ('%6.2f' % number_bytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[index])


def download(directory, target_url):

    file_name = target_url.split('/')[-1]
    target_file = Path(directory) / file_name

    response = requests.get(target_url, allow_redirects=True, timeout=10, stream=True)
    if response.status_code == 200:
        total_data_length = int(response.headers.get('content-length'))
        human = human_size(total_data_length)

        bar_format = f'Reading {human} {{l_bar}}{{bar:150}} [remaining time: {{remaining}}]'
        progress_bar = tqdm(total=total_data_length, bar_format=bar_format, file=sys.stdout, leave=False)

        with open(target_file, 'wb') as file_handle:
            for chunk in response.iter_content(chunk_size=512 * 1024):
                if chunk:  # filter out keep-alive new chunks
                    file_handle.write(chunk)
                    progress_bar.update(len(chunk))
    else:
        raise Exception(f'failed to down load {file_name} to {directory}')

    return file_name


def extract(directory, file_name):
    file_name = Path(file_name)
    directory = Path(directory)
    handled = False
    for extension in 'tar.gz', 'zip', 'whl':
        if extension in ''.join(file_name.suffixes):
            full_file_name = directory / file_name
            if extension == 'tar.gz':
                handled = True
                with tarfile.open(full_file_name, 'r:gz') as tar_file:
                    tar_file.extractall(directory)
            elif extension in ('zip', 'whl'):
                handled = True
                with zipfile.ZipFile(full_file_name, 'r') as zip_file:
                    zip_file.extractall(directory)

    if not handled:
        raise Exception(f"couldn't extract file {file_name}")


def list_sub_directories(directory):
    return [elem.path for elem in os.scandir(directory) if elem.is_dir()]


def expand_version_star(version):

    result = []

    components = str(version).split('.')

    result_components = []
    found_star = False
    for element in components:
        if element != '*':
            result_components.append(element)
        else:
            found_star = True
            break

    if found_star:
        result.append('.'.join([*result_components, MIN_VERSION_COMPONENT_STR]))
        result.append('.'.join([*result_components, MAX_VERSION_COMPONENT_STR]))
    else:
        result.append('.'.join(result_components))

    result = [Version(version_string) for version_string in result]
    return result


def add_star_as_last_component(version):

    components = str(version).split('.')
    if components[-1] != '*':
        components = [*components[:-1], '*']
    version = '.'.join(components)

    return version


def get_url_info(url):
    url_parts = url.split('/')
    package = url_parts[-1]
    package_parts = package.split('-')

    package_name = package_parts[0]

    extensions = ('tar.gz', 'zip', 'whl')

    package_format = 'unknown'
    for extension in extensions:
        full_extension = f'.{extension}'
        if package_parts[1].endswith(full_extension):
            package_format = extension
            version = package_parts[1][:-len(full_extension)]

    return package_name, version, package_format


def guess_dependencies(directory, target_url):
    result = []
    for sub_directory in list_sub_directories(directory):
        try:
            result.extend(find_requirements(sub_directory))
        except RequirementsNotFound:
            pass
    _, version, _ = get_url_info(url)
    for elem in result:
        print("depends on(py-%s%s, type='run' when='%s')" % (elem.name, python_spec_to_spack(elem), version))
        # dependency_to_version_ranges(elem)
    return result


def extend_version_releases(version, length=3):
    version = Version(str(version))
    components = list(version.release)
    components.extend((0,) * (length - len(components)))
    components = [str(component) for component in components]
    return Version('.'.join(components))


def increment_version(version, increment=1, max_val=9999):
    version = extend_version_releases(version)
    components = list(version.release)

    current_component = -1
    finished = False
    while not finished and -current_component <= len(components):

        components[current_component] += increment

        if components[0] > MAX_VERSION_COMPONENT:
            components = MAX_VERSION_COMPONENT, MAX_VERSION_COMPONENT, MAX_VERSION_COMPONENT
            break
        elif components[0] < 0:
            components = MIN_VERSION_COMPONENT, MIN_VERSION_COMPONENT, MIN_VERSION_COMPONENT
            break

        if components[current_component] > max_val:
            components[current_component] = 0
            current_component -= 1
        elif components[current_component] < 0:
            components[current_component] = max_val
            current_component -= 1

        else:
            finished = True

    result = Version('.'.join([str(component) for component in components]))

    return result


def dependency_to_version_ranges(dependency):

    requirement = Requirement(str(dependency))

    version_ranges = []
    if not requirement.specifier:
        version_ranges.append(p.closed(MIN_VERSION, MAX_VERSION))
    else:
        for specifier_part in requirement.specifier:

            versions = expand_version_star(specifier_part.version)
            versions = [extend_version_releases(version) for version in versions]

            if specifier_part.operator == '>=':
                version_ranges.append(p.closed(versions[-1], MAX_VERSION))
            elif specifier_part.operator == '<=':
                version_ranges.append(p.closed(MIN_VERSION, versions[0]))
            elif specifier_part.operator == '<':
                version_ranges.append(p.open(MIN_VERSION, versions[0]))
            elif specifier_part.operator == '>':
                version_ranges.append(p.open(versions[-1], MAX_VERSION))
            elif specifier_part.operator == '==':
                version_ranges.append(p.closed(versions[0], versions[-1]))
            elif specifier_part.operator == '~=':
                star_version = add_star_as_last_component(versions[-1])
                upper_version = expand_version_star(star_version)[1]
                version_ranges.append(p.closed(versions[0], upper_version))
            elif specifier_part.operator == '!=':
                version_ranges.append(p.closedopen(MIN_VERSION, versions[0]) |
                                      p.openclosed(versions[-1], MAX_VERSION))

    result = list(reduce(and_, version_ranges))
    return result


def version_to_release_string(version):
    version = Version(str(version))
    return '.'.join([str(component) for component in version.release])


def trim_version_micros(version):
    version = Version(str(version))
    release = version.release

    len_release = len(release)
    if len_release > 2:
        for i in range(len_release):
            if release[-i-1] != 0:
                break

    to_trim = i
    max_trim = len_release - 2
    if to_trim > max_trim:
        to_trim = max_trim

    if to_trim > 0:
        release = release[:-to_trim]

    str_release = [str(elem) for elem in release]

    return Version('.'.join(str_release))


def trim_spec_version_micros(spec):

    result = []
    for elem in spec:

        new_elem = []
        result.append(new_elem)

        for item in elem:
            new_elem.append(trim_version_micros(item))

    return result


def format_version_ranges(ranges):

    result = []
    for elem in ranges:
        if elem[-1] == MAX_VERSION:
            spec_part = '@%s:' % version_to_release_string(elem[0])
        elif elem[0] == MIN_VERSION:
            spec_part = '@:%s' % version_to_release_string(elem[1])
        else:
            spec_part = '@%s' % ':'.join([version_to_release_string(item) for item in elem])
        result.append(spec_part)
    return result


def python_spec_to_spack(dependency):
    version_ranges = dependency_to_version_ranges(dependency)

    ranges = []
    for version_range in version_ranges:
        for interval in version_range:

            if (interval.left == p.CLOSED and interval.right == p.CLOSED) and (interval.lower == interval.upper):
                ranges.append((interval.lower,))
            else:
                lower_bound = interval.lower
                upper_bound = interval.upper
                if interval.left == p.OPEN and interval.lower != MIN_VERSION:
                    lower_bound = increment_version(interval.lower, 1)
                if interval.right == p.OPEN and interval.upper != MAX_VERSION:
                    upper_bound = increment_version(interval.upper, -1)
                ranges.append((lower_bound, upper_bound))

    ranges = trim_spec_version_micros(ranges)
    ranges = format_version_ranges(ranges)

    return ','.join(ranges)


def download_and_extract(directory, target_url):
    file_name = download(directory, target_url)
    extract(directory, file_name)
    guess_dependencies(directory, target_url)


def work_with_directory(directory, target_url):
    print(f'work with file://{directory} {target_url}')

    download_and_extract(directory, target_url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='calculate hashes from web links.')
    parser.add_argument('-n', '--no-cleanup', default=False, dest='no_cleanup', action=STORE_TRUE,
                        help='prevent cleanup of temporary files')
    parser.add_argument('urls', nargs='*')

    args = parser.parse_args()

    for url in args.urls:
        if args.no_cleanup:
            temp_directory = tempfile.mkdtemp()
            work_with_directory(temp_directory, url)
            print(f'WARNING: directory {temp_directory} will not be deleted on program termination')
        else:
            with tempfile.TemporaryDirectory() as temp_directory:
                work_with_directory(temp_directory, url)
