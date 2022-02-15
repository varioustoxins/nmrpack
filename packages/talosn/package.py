#
# NMRPack copyright 2020-2022 G.S.Thompson, H.H. Thompson & the University of Kent
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

from spack import *
import llnl.util.tty as tty
import pathlib
import sys

import shutil
import os

package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.environment import get_environment_change,PREPEND,NEW

csh = which('csh')
chmod = which('chmod')


class Talosn(Package):
    "TALOS-N is an artificial neural network (ANN) based hybrid system for empirical prediction of protein backbone φ/ψ torsion angles, sidechain χ1 torsion angles and secondary structure using a combination of six kinds (HN, Hα, Cα, Cβ, CO, N) of chemical shift assignments for a given residue sequence."

    homepage = "https://spin.niddk.nih.gov/bax/software/TALOS-N/"
    url = "http://spin.niddk.nih.gov/bax/software/TALOS-N/install.com"

    version('4.12', 'revision=2015.147.15.40',
            sha256='49d5406a2645d682bf1ae2a7a47b60804814d354743bef33ddca5772e552176c', expand=False)

    resource(name='talosn.tZ', url='http://spin.niddk.nih.gov/bax/software/TALOS-N/talosn.tZ',
             sha256='ae9b9b94c15b57255bd1e1a734b577fe1ccdfd605ba1e1e0152fea43d7cc966a', destination='.',
             placement='tmp_talosn.tZ', expand=False)

    def get_resource_names(self, spec):
        result = []
        for resource_spec, resources in self.resources.items():
            if spec.satisfies(resource_spec):
                result = [resource.name for resource in resources]
                break

        return result

    # FIXME: Add dependencies if required.
    # depends_on('example')

    def install(self, spec, prefix):

        resource_filenames = self.get_resource_names(spec)

        for file_name in resource_filenames:
            shutil.move(f'tmp_{file_name}/{file_name}', prefix)
        shutil.move('install.com', prefix)

        os.chdir(prefix)
        chmod('u+x', './install.com')
        csh('./install.com')

        os.remove('./install.com')
        os.remove('./talosn.tZ')
        os.remove('./tar.log')

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):

        expected = 'TALOS-N Version'
        expected2 = 'Input Options'

        prefix = os.getcwd()

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            script = f"""
                
                bin/TALOSN.mac.10.15 -help >& {tmp_dir_name}/test_output.txt

                exit 0
            """
            with open(f"{tmp_dir_name}/test_talosn.csh", 'w') as file_handle:
                file_handle.write(script)

            csh(f"{tmp_dir_name}/test_talosn.csh")

            tty.error('error error error')

            raise Exception('failed')

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


        INIT_FILE=f'{self.prefix}/talosn_init.com'
        environment_changes = get_environment_change(self.prefix, INIT_FILE)

        tty.msg(environment_changes)
        for name,type, value in environment_changes:
            if type == PREPEND:
                env.prepend_path(name, value)
                tty.msg("prepend", name, value)
            elif type == NEW:
                env.set(name, value)
                tty.msg("new", name, value)
            else:
                raise Exception(f'unexpected change type {type}')
