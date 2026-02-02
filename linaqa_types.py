"""
===========================
Type definitions for LinaQA
===========================
"""
# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

import inspect
from PyQt5.QtWidgets import QDoubleSpinBox
from pylinac.picketfence import MLC
from pylinac.nuclear import Nuclide
from pylinac import planar_imaging

supported_modalities = ['RTIMAGE', 'RTDOSE', 'CT', 'NM', 'PT', 'MR', 'OT', 'XA']
# TODO pull these directly from class def
phantom3D_list = ['CatPhan503', 'CatPhan504', 'CatPhan600', 'CatPhan604', 'CatPhan700', 'QuartDVT', 'ACR CT', 'ACR MRI']

vmat_list = ['DRGS', 'DRMLC', 'DRCS']

phantom2D_list = [obj.common_name for name, obj in inspect.getmembers(planar_imaging) if hasattr(obj, 'common_name')]

spatial_res_list = ['Four Bar', 'Quadrant']

mlc_list = [mlc.value.get('name') for mlc in MLC]

nuclide_list = [str(name) for name, value in vars(Nuclide).items() if not name.startswith('__')]

# colours for status bar messages
faint_red = '#ff7979'
faint_yellow = '#fffccf'
faint_green = '#d3ffe4'


class MyDoubleSpinBox(QDoubleSpinBox):
    def validate(self, text: str, pos: int) -> object:
        text = text.replace(".", ",")
        return QDoubleSpinBox.validate(self, text, pos)

    def valueFromText(self, text: str) -> float:
        text = text.replace(",", ".")
        return float(text)