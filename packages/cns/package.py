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

from os.path import join
from spack import *
from spack.package import Package
from spack.directives import variant,patch, version, resource
from spack.util.executable import which
from llnl.util.filesystem import filter_file, install_tree, working_dir, join_path

package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.yaml_package import read_releases

# this triggers these fetchers
from nmrpack.packages.cns import cns_fetcher
from nmrpack.packages.aria import aria_fetcher

from nmrpack.lib.environment import get_environment_change,PREPEND,NEW

import llnl.util.tty as tty

CNS_SOLVE_ENV = 'cns_solve_env'

csh = which('csh')

class Cns(Package):
    """CNS The Crystallography & NMR System for structure calculation (1.2 for ARIA + aria patches)"""

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "http://cns-online.org"

    read_releases('cns')

    resource(name='aria2.3.2', aria_url='http://aria.pasteur.fr/archives/aria2.3.2.tar.gz',
             sha256='13a41f8916e895e2edeec1dd0eb84eb632f10b0fef9558e195d8876801daa4fa', destination='.')

    # patch to make SETFPEPS (set floating point epsilon work)
    # see https://ask.bioexcel.eu/t/cns-errors-before-after-recompilation/54
    # main patch courtesy of Brian Smith U of Glasgow
    variant('configuration', default='none', description='where to find the configuration file', validator=cns_fetcher.check_cns_config_file)
    variant('fp_epsilon', default=True, description='SETFPEPS required for modern compilers')
    variant('aria', default=True, description='patches required to run aria', validator=aria_fetcher.check_aria_config_file)

    patch('getarch_darwin_x86_64.patch', when='@1.21',
          sha256='42a0d10d7684000d5c4cf1114e14d5549cc19c84b19df4d42419abd7187cf887')
    patch('machvar_fpeps.patch', when='@1.21+fp_epsilon',
          sha256='a00db99086c63961abe4e19d253590421973a80a9e104ac85dbcc07d472b6485')

    def install(self, _, prefix):

        # edit cns_solve_environment to allow a build
        shutil.copy('cns_solve_env','cns_solve_env.back')
        filter_file(r"setenv CNS_SOLVE '_CNSsolve_location_'", f"setenv CNS_SOLVE '{self.stage.source_path}'", 'cns_solve_env')

        # copy over an almost right machine make file we could have got it from v1.3 but this is simpler
        src_file = 'instlib/machine/supported/intel-x86_64bit-linux/Makefile.header.2.gfortran'
        dest_file = 'instlib/machine/supported/mac-intel-darwin/Makefile.header.5.gfortran'
        shutil.move(src_file, dest_file)


        if not self.spec.satisfies('%fortran@:10.0.0'):
            # patch the machine make file, can't be done with a patch statement it doesn't exists till we copy it
            # tried just copying the file from the package directory but it caused a lockup
            patch = which('patch')
            patch_file = join_path(package_root,'nmrpack/packages/cns', 'gfortran_10_allow_argument_mismatch.patch')
            patch('-p1', '-i',patch_file)

        if '+aria' in self.spec:
            from_path=pathlib.Path('aria2.3/cns/src')
            to_path='source'

            for target_file in from_path.iterdir():
                if target_file.is_file() and target_file.suffix in ('.f','.inc'):
                    print(f'copying {target_file} to {to_path}')
                    shutil.copy(target_file,to_path)
                if target_file.is_dir():
                    print(f'copying {target_file} to {to_path}')
                    shutil.copytree(target_file, join_path(to_path, target_file.name))

            shutil.copytree(from_path,'aria2.3_patches_applied')
            shutil.rmtree('aria2.3')

        make('install')

        install_tree('.',prefix)

        with working_dir(prefix):
            shutil.move('cns_solve_env.back', 'cns_solve_env')


            replacement_env = f" setenv CNS_SOLVE  '{prefix}'"
            filter_file(r"setenv CNS_SOLVE '_CNSsolve_location_'", replacement_env, 'cns_solve_env')

        # remove a leftover from our previous edits
        os.remove(pathlib.Path(prefix)  / pathlib.Path('cns_solve_env' + '~'))

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_dir_name:
                tmp_dir_name = '/tmp'

                test_inp = f'''
                stop
                '''

                with open(join_path(tmp_dir_name,'test.inp'),'w') as fp:
                    fp.write(test_inp)


                test_csh = f'''
                source  {self.prefix}/cns_solve_env
        
                cns_solve < {tmp_dir_name}/test.inp >& {tmp_dir_name}/test_output.txt 
                '''

                with open(join_path(tmp_dir_name,'test.csh'), 'w') as fp:
                    fp.write(test_csh)

            csh(join(tmp_dir_name,'test.csh'))


            expected = '''
            ============================================================
            |                                                          |
            |            Crystallography & NMR System (CNS)            |
            |                         CNSsolve                         |
            |                                                          |
            ============================================================
             Version: 1.2 at patch level 1
             Status: General release with ARIA enhancements
            ============================================================
            '''.split("\n")
            expected = [line.strip() for line in expected if len(line)]

            ok = True
            result= ''
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
            tty.error('there was an error',e)


    def setup_run_environment(self, env):

        environment_changes = get_environment_change(self.prefix, CNS_SOLVE_ENV)

        # print('** environment_changes **', environment_changes)
        #
        for name,type, value in environment_changes:
            if type == PREPEND:
                env.prepend_path(name, value)
            elif type == NEW:
                env.set(name, value)
            else:
                raise Exception(f'unexpected change type {type}')