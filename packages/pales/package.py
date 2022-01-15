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

from spack import *

package_root = str(pathlib.Path(__file__).parents[3])
if not package_root in sys.path:
    sys.path.insert(0, package_root)

from nmrpack.lib.yaml_package import read_releases

class Pales(Package):
    """PALES - software for analysis of residual dipolar couplings. """

    homepage = "http://www3.mpibpc.mpg.de/groups/zweckstetter/_links/software_mars.htm"

    read_releases('pales')


    def install(self, _, prefix):

        mkdirp(prefix.bin)

        files = [item for item in pathlib.Path('.').glob('*') if item.is_file]
        for file in files:
            shutil.move(file, prefix.bin)






