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
import pathlib


package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.environment import get_environment_change,PREPEND,NEW
from nmrpack.lib.yaml import read_releases

import spack.util.spack_yaml as syaml
import os
import shutil
import llnl.util.tty as tty



EXAMPLE_FILE = 'example.cshrc'



csh = which('csh')


def remove_local_files_no_error_but_warn(files):
    for file_name in files:
        try:
            os.remove(f'./{file_name}')
        except Exception:
            tty.warn(f"couldn't remove installation file {file_name}")

class Nmrpipe(Package):
    """NMRPipe an extensive software system for processing, analyzing,
       and exploiting multidimensional NMR spectroscopic data"""

    homepage = "https://www.ibbr.umd.edu/nmrpipe/install.html"

    releases = read_releases('nmrpipe')

    variant('dyn', default=False, description='install the dyn molecular dynamics library')
    variant('talos', default=False, description='install the talos chemical shift based dihedral angle predictor')
    variant('smile', default=True, description='install the smile nus processing module')

    def install(self, spec, prefix):

        version_key = str(spec.version)
        installed_release = self.releases[version_key]
        installed_resources = installed_release['resources']
        file_name_variants = [(file_name, variant_name) for file_name, (_, _, variant_name)
                              in installed_resources.items()]
        file_name_variants = [(file_name, variant_name) for file_name, variant_name in file_name_variants
                              if not variant_name or f'+{variant_name}' in self.spec]

        for file_name, variant_name in file_name_variants:
            shutil.move(f'tmp_{file_name}/{file_name}', '.')

        items = [f for f in os.listdir('.')]
        for item in items:
            if not item.startswith('tmp_') or item in installed_resources.keys():
                shutil.move(item, prefix)

        os.chdir(prefix)
        csh('./install.com')

        install_files = []
        for file_name, variant_name in file_name_variants:
            install_files.append(file_name)
        install_files.append(installed_release['install_file'])
        remove_local_files_no_error_but_warn(install_files)

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):

        expected = '** NMRPipe System'
        expected2 = 'nmrPipe -fn fnName'

        prefix = os.getcwd()

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            script = f"""
                source   {prefix}/example.cshrc
                nmrPipe -help >& {tmp_dir_name}/test_output.txt

                exit 0
            """
            with open(f"{tmp_dir_name}/test_pipe.csh", 'w') as file_handle:
                file_handle.write(script)

            csh(f"{tmp_dir_name}/test_pipe.csh")

            with open(f"{tmp_dir_name}/test_output.txt", 'r') as file_handle:
                result = file_handle.readlines()
                result = ''.join(result)

                if not ((expected in result) and (expected2 in result)):
                    tty.error(f"during testing strings {expected} and {expected2} not found in test output")
                    tty.error("")
                    tty.error(f" output was")
                    tty.error("")
                    for line in result:
                        tty.error(line.strip())

    def setup_run_environment(self, env):


        environment_changes = get_environment_change(self.prefix, EXAMPLE_FILE)


        for name,type, value in environment_changes:
            if type == PREPEND:
                env.prepend_path(name, value)
            elif type == NEW:
                env.set(name, value)
            else:
                raise Exception(f'unexpected change type {type}')