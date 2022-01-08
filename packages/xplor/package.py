#
# NMRPack copyright 2020 G.S.Thompson & the University of Kent
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

import sys
import os
import pathlib
import shutil
from os import listdir
from os.path import isfile, join
from spack import *
from spack.package import Package
from spack.directives import variant,patch, version, resource
from spack.util.executable import which
from llnl.util.filesystem import filter_file, install_tree, working_dir, join_path

package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.yaml_package import read_releases

# this triggers
from nmrpack.packages.xplor import xplor_fetcher

import llnl.util.tty as tty
import spack.error as error

tar = which('tar')
bash = which('bash')


def check_config_file(*args,**kwargs):

    value = args[-1][0]

    if value == 'none':
        msg = 'the configuration flag is required and needs a configuration file ' \
              'as an argument [configuration=<FILE_NAME>]'
        raise error.SpecError(msg)
    else:
        result = xplor_fetcher.XPLOR_URL_Fetch_Strategy.check_configuration_file(value)
        if result != xplor_fetcher.XPLOR_URL_Fetch_Strategy.OK:
            raise error.SpecError(f'Error with configuration {value} {result}')



class Xplor(Package):
    """XPLOR-NIH is a structure determination program which builds on the X-PLOR program, including additional tools developed at the NIH."""

    homepage = "https://nmr.cit.nih.gov/xplor-nih"

    url='https://nmr.cit.nih.gov/xplor-nih/packages/xplor-nih-3.4-db.tar.gz'
    variant('configuration', default='none', description='where to find the configuration file', validator=check_config_file)


    read_releases('xplor')

    def installable_resource_filenames(self, spec):
        resource_filenames = set(self.get_resource_names(spec))

        for variant_name in self.variants:
            if not f'+{variant_name}' in self.spec:
                if hasattr(self, 'variant_files'):
                    for variant_file in self.variant_files[variant_name]:
                        resource_filenames.remove(variant_file)
        return resource_filenames

    def get_resource_names(self, spec):
        result = []
        for resource_spec, resources in self.resources.items():
            if spec.satisfies(resource_spec):
                result = [resource.name for resource in resources]
                break

        return result

    def install(self, spec, prefix):

        resource_filenames = self.installable_resource_filenames(spec)
        all_filenames = [pathlib.Path(self.stage.archive_file).name, *resource_filenames]

        for file_name in resource_filenames:
            shutil.move(f'tmp_{file_name}/{file_name}', '.')

        items = [f for f in os.listdir('.')]
        for item in items:
            if not item.startswith('tmp_') or item in all_filenames:
                shutil.move(item, prefix)

        os.chdir(prefix)

        for file_name in all_filenames:
            if file_name.endswith('tar.gz'):
                tar('--strip-components', '1', '-zxvf', file_name)
                os.remove(file_name)

        bash('./configure')

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):

        test_inp = '''
        stop
        '''

        test_sh = '''
        bin/xplor < %(tmp_dir_name)s/test.inp >& %(tmp_dir_name)s/test_output.txt
        '''

        expected = ['http://nmr.cit.nih.gov/xplor-nih        based on X-PLOR 3.851 by A.T. Brunger']

        self.run_test(test_inp, test_sh, expected, name='xplor')

        test_inp = '''
        print('hello world')
        '''
        test_inp =  test_inp.strip()

        test_sh = '''
        bin/pyXplor %(tmp_dir_name)s/test.inp >& %(tmp_dir_name)s/test_output.txt
        '''

        expected = ['hello world']

        self.run_test(test_inp, test_sh, expected, name="pyXplor")

    def run_test(self, test_inp, test_sh, expected, name):

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_dir_name = '/tmp'

            with open(join_path(tmp_dir_name, 'test.inp'), 'w') as fp:
                fp.write(test_inp)

            test_sh = test_sh % {'tmp_dir_name': tmp_dir_name}

            with open(join_path(tmp_dir_name, 'test.sh'), 'w') as fp:
                fp.write(test_sh)

        Exception(test_sh)
        bash(join(tmp_dir_name, 'test.sh'))

        ok = True

        with open(f"{tmp_dir_name}/test_output.txt", 'r') as file_handle:
            result = file_handle.readlines()
            result = [line.strip() for line in result if len(line)]
            for line in expected:
                if not line in result:
                    tty.error(f'line --{line}-- not in result')
                    ok = False
                    break
        if ok:
            tty.msg(f'test {name} passed!')
        else:
            tty.error(f'''during testing strings
                          {expected}
                          not found in test output")
                       ''')
            tty.error("")
            tty.error(f" output was")
            tty.error("")
            for line in result:
                tty.error(line.strip())

    def setup_run_environment(self, env):

        bin_path = pathlib.Path(self.prefix) / 'bin'
        env.prepend_path('PATH', str(bin_path.resolve()))

