# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

# ----------------------------------------------------------------------------
# If you submit this package back to Spack as a pull request,
# please first remove this boilerplate and all FIXME comments.
#
# This is a template package file for Spack.  We've put "FIXME"
# next to all the things you'll want to change. Once you've handled
# them, you can save this file and test your package like this:
#
#     spack install nmrpipex-tz
#
# You can edit this file again by typing:
#
#     spack edit nmrpipex-tz
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------


from spack import *
import subprocess
import os
import shutil
import llnl.util.tty as tty

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

    _install_file='NMRPipeX.tZ'
    version('2020.219.15.07', md5='cb9ba746854132f88434064a00ffcf17', url=f"http://www.ibbr.umd.edu/nmrpipe/{_install_file}", expand=False)

    base_url = 'http://www.ibbr.umd.edu/nmrpipe/'

    # file_name : (parent_url md5)
    _resources = {
        's.tZ' : ('http://www.ibbr.umd.edu/nmrpipe', '3db6d675ae37f5160d90e5b4dd71da53'),
        'install.com' : ('http://www.ibbr.umd.edu/nmrpipe','8d9449de19992d8c2de8a646cce27d71'),
        'binval.com' : ('http://www.ibbr.umd.edu/nmrpipe','1b4c0998eeccb917dfa04932ae990dfb'),
        'dyn.tZ' : ('http://www.ibbr.umd.edu/nmrpipe', '91fb6633c6c1e9f632b4676d8162ba30'),

        # the urls for these resources must be from the niddk site not the ibbrsite
        # otherwise every download seems to be a different checksum...
        'talos_nmrPipe.tZ' :  ('https://spin.niddk.nih.gov/bax/software', '19dea8ed8301434ed0c7d9fdaa766670'),
        'plugin.smile.tZ' : ('https://spin.niddk.nih.gov/bax/software/SMILE', '044ce568d90227cc305e0cdf0be68298')
    }

    for file_name, (url,md5) in _resources.items():
        resource(name=file_name, url=f'{url}/{file_name}', md5=md5, expand=False, destination='',placement=f'tmp_{file_name}')

    def install(self, spec, prefix):

        for file_name in self._resources.keys():
            shutil.move(f'tmp_{file_name}/{file_name}', '.')

        items = [f for f in os.listdir('.')]
        for item in items:
            if not item.startswith('tmp_') or item in self._resources.keys():
                shutil.move(item, prefix)

        os.chdir(prefix)
        csh('./install.com')

        install_files = list(self._resources.keys())
        install_files.append(self._install_file)
        remove_local_files_no_error_but_warn(install_files)

    @run_after('install')
    @on_package_attributes(run_tests=True)
    def test(self):

        expected = '** NMRPipe System'
        expected2 = 'nmrPipe -fn fnName'

        prefix = os.getcwd()

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdirname = '/tmp'
            script = f"""
                source   {prefix}/example.cshrc
                nmrPipe -help >& {tmpdirname}/test_output.txt

                exit 0
            """
            with open(f"{tmpdirname}/test_pipe.csh", 'w') as file_handle:
                file_handle.write(script)

            csh(f"{tmpdirname}/test_pipe.csh")

            with open(f"{tmpdirname}/test_output.txt", 'r') as file_handle:
                result = file_handle.readlines()
                result = ''.join(result)

                if not ((expected in result) and (expected2 in result)):
                    tty.error(f"during testing strings {expected} and {expected2} not found in test output")
                    tty.error("")
                    tty.error(f" output was")
                    tty.error("")
                    for line in result:
                        tty.error(line.strip())


