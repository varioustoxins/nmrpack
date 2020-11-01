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
#     spack install nmrpipe
#
# You can edit this file again by typing:
#
#     spack edit nmrpipe
#
# See the Spack documentation for more information on packaging.
# ----------------------------------------------------------------------------


from spack import *
import spack.util.spack_yaml as syaml
import os
import shutil
import llnl.util.tty as tty

import pathlib


csh = which('csh')


def remove_local_files_no_error_but_warn(files):
    for file_name in files:
        try:
            os.remove(f'./{file_name}')
        except Exception:
            tty.warn(f"couldn't remove installation file {file_name}")


def read_releases():
    parent_directory = pathlib.Path(__file__).parent.absolute()
    file_name = f'{parent_directory}/package.yaml'

    return syaml.load(open(file_name))


class Nmrpipe(Package):
    """NMRPipe an extensive software system for processing, analyzing,
       and exploiting multidimensional NMR spectroscopic data"""

    homepage = "https://www.ibbr.umd.edu/nmrpipe/install.html"

    releases = read_releases()
    for release_id, release in releases.items():
        url = f"{release['root_url']}/{release['install_file']}"
        version_number = release['version']
        version(version_number, url=url, md5=release['md5'], expand=False)

        # NOTE: we could be downloading resources we don't need because a variant is marked as not required
        # however, how to access variants from the spec at this point...
        for file_name, (url, md5, variant_name) in release['resources'].items():
            resource(name=file_name, url=f'{url}/{file_name}', md5=md5, expand=False, destination='',
                     placement=f'tmp_{file_name}', when=f'@{version_number}')

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
