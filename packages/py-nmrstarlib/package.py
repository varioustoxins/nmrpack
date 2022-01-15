#
# NMRPack copyright 2020-2022 G.S.Thompson & the University of Kent
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
# Inc., 51 Franklin St reet, Fifth Floor, Boston, MA  02110-1301, USA.
#

import pathlib
import sys
from spack import *

package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.yaml_package import read_releases

class PyNmrstarlib(Package):
    """Python library for parsing data from NMR-STAR format files"""

    homepage = "https://github.com/MoseleyBioinformaticsLab/nmrstarlib"

    read_releases('py-nmrstarlib')

    extends('python@:3.6')
    depends_on('py-pip', type='build')

    def install(self, _, prefix):
        pip = which('pip')
        pip('install', self.stage.archive_file, '--prefix={0}'.format(prefix))

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_dir_name:

                test_bash = f'''
                python -c "import pynmstar ; nmrstarlib"
                '''

                with open(join_path(tmp_dir_name, 'test.bash'), 'w') as fp:
                    fp.write(test_bash)

            bash(join(tmp_dir_name, 'test.bash'))

            expected = "module 'nmrstarlib'!"

            ok = True
            with open(f"{tmp_dir_name}/test_output.txt", 'r') as file_handle:
                result = file_handle.readlines()
                result = [line.strip() for line in result if len(line)]
                for line in expected:
                    if not line in result:
                        tty.error(f'line --{line}-- not in result')
                        ok = False
                        break
            if not ok:
                tty.error(f'''during testing strings 
                              {expected} 
                              not found in test output")
                           ''')
                tty.error("")
                tty.error(f" output was")
                tty.error("")
                for line in result:
                    tty.error(line.strip())
        except Exception as e:
            tty.error('there was an error', e)
