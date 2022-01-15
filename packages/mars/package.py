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
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import os
import pathlib
import shutil
import sys
from llnl.util.filesystem import join_path

from spack import *

package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.yaml_package import read_releases

bash=which('bash')
import llnl.util.tty as tty

class Mars(Package):
    """MARS a powerful program for robust automatic backbone assignment of proteins. """

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "http://www3.mpibpc.mpg.de/groups/zweckstetter/_links/software_mars.htm"

    read_releases('mars')

    # variant('pales', default=False, description='include pales for assignment using RDCs')
    # variant('gui', default=False, description='install the gui')

    # FIXME: Add dependencies if required.
    # depends_on('pales', when="+pales")

    def install(self, spec, prefix):

        shutil.move('bin', prefix)
        shutil.move('examples', prefix)
        shutil.move('merge-peaklists-cutoff-screen.awk', prefix.bin)

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_dir_name:

                test_bash = f'''
                cd {tmp_dir_name}
                cp -r mars_prefix/examples/Input-1.2 test 
                runmars mars.inp  > mars.out  2>&1 
                '''

                with open(join_path(tmp_dir_name, 'test.bash'), 'w') as fp:
                    fp.write(test_bash)

            bash(join(tmp_dir_name, 'test.csh'))

            expected = 'MARS has been successfully finished !!'

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



