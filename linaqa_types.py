"""
===========================
Type definitions for LinaQA
===========================
"""
# Author: AC Chamberlain

from PyQt5.QtWidgets import QDoubleSpinBox

supported_modalities = ['RTIMAGE', 'RTDOSE', 'CT', 'NM', 'PT', 'MR', 'OT', 'XA']
# TODO pull these directly from class def
catphan_list = ["CatPhan503", "CatPhan504", "CatPhan600", "CatPhan604", "QuartDVT", "ACR CT", "ACR MRI"]
vmat_list = ["DRGS", "DRMLC"]

phantom2D_list = ["Doselab MC2 MV",
                  "Doselab MC2 kV",
                  "Las Vegas",
                  "Elekta Las Vegas",
                  "Leeds TOR",
                  "PTW EPID QC",
                  "SNC MV-QA",
                  "SNC kV-QA",
                  "SI FC-2",
                  "SI QC-3",
                  "SI QC-kV",
                  "IBA Primus A"]

spatial_res_list = ['Four Bar', 'Quadrant']

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