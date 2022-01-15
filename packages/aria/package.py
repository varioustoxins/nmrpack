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

import sys
import os
import pathlib
import shutil
from os import listdir
from os.path import isfile, join
from textwrap import dedent

from spack import *
from spack.package import Package
from spack.directives import variant, version, resource,depends_on
from spack.util.executable import which
from llnl.util.filesystem import filter_file, install_tree, working_dir, join_path

import llnl.util.tty as tty


package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.yaml_package import read_releases

# this triggers
from nmrpack.packages.aria import aria_fetcher
from nmrpack.lib.fetchers import find_configuration_file_in_args

CNS_SOLVE_ENV = 'cns_solve_env'

csh = which('csh')

def get_configuration_variant_if_found():
    configuration =  find_configuration_file_in_args()
    result = ''
    if configuration is not None:
        configuration = os.path.expanduser(configuration)
        result = f'configuration={configuration}'
    return result




class Aria(Package):
    """ARIA (Ambiguous Restraints for Iterative Assignment) a software for automated NOE assignment and NMR structure calculation. """


    homepage = "http://http://aria.pasteur.fr"
    url      = "http://aria.pasteur.fr/archives/aria2.3.2.tar.gz"

    read_releases('aria')

    variant('configuration', default='none', description='where to find the configuration file', validator=aria_fetcher.check_aria_config_file)

    depends_on('python@2.7.18+tkinter+tix')
    depends_on('py-numpy@1.15.4')
    depends_on('py-nmrstarlib')
    depends_on('py-matplotlib@2.2.5')

    depends_on(f'cns {get_configuration_variant_if_found()}', type='run')

    def install(self, spec, prefix):

        # # edit cns_solve_environment to allow a build
        # shutil.copy('cns_solve_env','cns_solve_env.back')
        # filter_file(r"setenv CNS_SOLVE '_CNSsolve_location_'", f"setenv CNS_SOLVE '{self.stage.source_path}'", 'cns_solve_env')
        #
        # # copy over an almost right machine make file we could have got it from v1.3 but this is simpler
        # src_file = 'instlib/machine/supported/intel-x86_64bit-linux/Makefile.header.2.gfortran'
        # dest_file = 'instlib/machine/supported/mac-intel-darwin/Makefile.header.5.gfortran'
        # shutil.move(src_file, dest_file)
        #
        #
        # if not self.spec.satisfies('%fortran@:10.0.0'):
        #     # patch the machine make file, can't be done with a patch statement it doesn't exists till we copy it
        #     # tried just copying the file from the package directory but it caused a lockup
        #     patch = which('patch')
        #     patch_file = join_path(package_root,'nmrpack/packages/cns', 'gfortran_10_allow_argument_mismatch.patch')
        #     patch('-p1', '-i',patch_file)
        #
        # if '+aria' in self.spec:
        #     from_path=pathlib.Path('aria2.3/cns/src')
        #     to_path='source'
        #
        #     for target_file in from_path.iterdir():
        #         if target_file.is_file() and target_file.suffix in ('.f','.inc'):
        #             print(f'copying {target_file} to {to_path}')
        #             shutil.copy(target_file,to_path)
        #         if target_file.is_dir():
        #             print(f'copying {target_file} to {to_path}')
        #             shutil.copytree(target_file, join_path(to_path, target_file.name))
        #
        #     shutil.copytree(from_path,'aria2.3_patches_applied')
        #     shutil.rmtree('aria2.3')
        #
        # make('install')
        #
        install_tree('.',prefix)


        with working_dir(self.prefix):
            os.mkdir('bin')



        for d in spec.traverse():
            if d.name == 'python':
                python_exec = join_path(d.prefix, 'bin', 'python')
                break

        for d in spec.traverse():
            if d.name == 'cns':
                cns_path=join_path(d.prefix, 'bin')
                break

        ARIA2_TEMPLATE = f'''
            #!/bin/bash
            export ARIA2="{prefix}"
            echo Note: nmrpack installed cns in {cns_path}
            %(command)s
        '''

        ARIA2_TEMPLATE = dedent(ARIA2_TEMPLATE)
        ARIA2_FILE = ARIA2_TEMPLATE % {'command' : f'"{python_exec}" -O $ARIA2/aria2.py "$@"'}
        ARIA_PYTHON = ARIA2_TEMPLATE % {'command' : f'"{python_exec}" "$@"'}
        with working_dir(self.prefix.bin):
            print(os.getcwd())
            with open('aria2', 'w') as fh:
                fh.write(ARIA2_FILE)
            set_executable('aria2')

            with open('a2python', 'w') as fh:
                fh.write(ARIA_PYTHON)
            set_executable('a2python')


    def setup_run_environment(self, env):
        env.prepend_path('PATH', join_path(self.prefix,'bin'))

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):
        try:
            import tempfile
            with tempfile.TemporaryDirectory() as tmp_dir_name:

                test_csh = f'''
                

                aria2 >& {tmp_dir_name}/test_output.txt
                '''

                with open(join_path(tmp_dir_name,'test.csh'), 'w') as fp:
                    fp.write(test_csh)

            csh(join(tmp_dir_name,'test.csh'))


            expected = ['ARIA Version',
                        'If you use this software, please quote the following reference(s):',
                        'Usage: aria2 [options] [project XML file]'
            ]
            expected = [line.strip() for line in expected]

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
            tty.error('there was an error',e)
