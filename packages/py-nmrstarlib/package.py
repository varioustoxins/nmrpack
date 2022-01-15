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
