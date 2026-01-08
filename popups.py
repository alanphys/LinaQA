"""
=========================================================================
Define popup dialogs for toolbar buttons
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

from linaqa_types import (
    supported_modalities,
    phantom3D_list,
    vmat_list,
    phantom2D_list,
    spatial_res_list,
    mlc_list,
    MyDoubleSpinBox)
from qt_subclasses import PopupToolbar, LongPressToolButton

from PyQt5.QtWidgets import QComboBox, QSpinBox


def create_3dphantom_popup(self):
    # create popup for the 3D phantom analysis
    self.ui.phantom3d_popup = PopupToolbar()
    self.ui.cbCatPhan = QComboBox()
    self.ui.cbCatPhan.setFixedWidth(120)
    self.ui.phantom3d_popup.add_vcontrol('Select phantom:', self.ui.cbCatPhan)
    self.ui.cbCatPhan.addItems(phantom3D_list)
    self.ui.cbCatPhan.currentIndexChanged.connect(self.on_cbcatphan_changed)
    catphan_type = self.settings.value('3D Phantoms/3D Type')
    index = self.ui.cbCatPhan.findText(catphan_type)
    if index >= 0:
        self.ui.cbCatPhan.setCurrentIndex(index)
    else:
        raise Exception('Invalid setting in 3D Phantoms/3D Type')
    self.replace_action_with_long_press(self.ui.toolBar_Rx, self.ui.action_CatPhan, self.ui.phantom3d_popup)
    self.replace_action_with_long_press(self.ui.toolBar_Dx, self.ui.action_CatPhan, self.ui.phantom3d_popup)


def create_mlc_popup(self):
    # create popup for the mlc analysis
    self.ui.mlc_popup = PopupToolbar()
    self.ui.cbMLC = QComboBox()
    self.ui.cbMLC.setFixedWidth(120)
    self.ui.mlc_popup.add_vcontrol('Select MLC:', self.ui.cbMLC)
    self.ui.cbMLC.addItems(mlc_list)
    self.ui.cbMLC.currentIndexChanged.connect(self.on_cbmlc_changed)
    mlc_type = self.settings.value('Picket Fence/MLC Type')
    index = self.ui.cbMLC.findText(mlc_type)
    if index >= 0:
        self.ui.cbMLC.setCurrentIndex(index)
    else:
        raise Exception('Invalid setting in Picket Fence/MLC Type')
    self.replace_action_with_long_press(self.ui.toolBar_Rx, self.ui.action_Picket_Fence, self.ui.mlc_popup)


def create_vmat_popup(self):
    # create popup for the VMAT analysis
    self.ui.vmat_popup = PopupToolbar()
    self.ui.cbVMAT = QComboBox()
    self.ui.cbVMAT.setFixedWidth(120)
    self.ui.vmat_popup.add_vcontrol('Select VMAT test:', self.ui.cbVMAT)
    self.ui.cbVMAT.addItems(vmat_list)
    self.ui.cbVMAT.currentIndexChanged.connect(self.on_cbvmat_changed)
    vmat_type = self.settings.value('VMAT/VMAT test')
    index = self.ui.cbVMAT.findText(vmat_type)
    if index >= 0:
        self.ui.cbVMAT.setCurrentIndex(index)
    else:
        raise Exception('Invalid setting in VMAT/VMAT test')
    self.replace_action_with_long_press(self.ui.toolBar_Rx, self.ui.action_VMAT, self.ui.vmat_popup)
    self.on_cbvmat_changed(self.ui.cbVMAT.currentIndex())


def create_2dphantom_popup(self):
    # create popup for the 3D phantom analysis
    self.ui.phantom2d_popup = PopupToolbar()
    self.ui.cbPhan2D = QComboBox()
    self.ui.cbPhan2D.setFixedWidth(120)
    self.ui.phantom2d_popup.add_vcontrol('Select phantom:', self.ui.cbPhan2D)
    self.ui.cbPhan2D.addItems(phantom2D_list)
    self.ui.cbPhan2D.currentIndexChanged.connect(self.on_2dphantom_changed)
    phan2d_type = self.settings.value('2D Phantoms/2D Type')
    index = self.ui.cbPhan2D.findText(phan2d_type)
    if index >= 0:
        self.ui.cbPhan2D.setCurrentIndex(index)
    else:
        raise Exception('Invalid setting in 2D Phantoms/2D Type')
    self.replace_action_with_long_press(self.ui.toolBar_Rx, self.ui.action_2DPhantoms, self.ui.phantom2d_popup)
    self.replace_action_with_long_press(self.ui.toolBar_Dx, self.ui.action_2DPhantoms, self.ui.phantom2d_popup)


def create_scale_popup(self):
    # create a popup for the scale factor
    self.ui.scale_popup = PopupToolbar()
    self.ui.dsbScaleFactor = MyDoubleSpinBox()
    self.ui.dsbScaleFactor.setSingleStep(0.01)
    self.ui.scale_popup.add_hcontrol('Scale Factor:', self.ui.dsbScaleFactor)
    self.ui.dsbScaleFactor.setValue(self.settings.value('PyDicom/Scale factor', 1.0, type=float))
    self.replace_action_with_long_press(self.ui.toolBar_Dx, self.ui.action_Scale_Image, self.ui.scale_popup)


def create_spatialres_popup(self):
    # we have to insert a Combox for the spatial resolution test manually into the toolbar
    self.ui.spatialres_popup = PopupToolbar()
    self.ui.cbSpatialRes = QComboBox()
    self.ui.spatialres_popup.add_vcontrol('Select spatial resolution test:', self.ui.cbSpatialRes)
    self.ui.cbSpatialRes.addItems(spatial_res_list)
    self.ui.cbSpatialRes.currentIndexChanged.connect(self.on_spatialres_changed)
    spatial_res_type = self.settings.value('Spatial Resolution/Resolution test', 'Four Bar', type=str)
    index = self.ui.cbSpatialRes.findText(spatial_res_type)
    if index >= 0:
        self.ui.cbSpatialRes.setCurrentIndex(index)
    else:
        raise Exception('Invalid setting in Spatial Resolution/Resolution test')
    self.replace_action_with_long_press(self.ui.toolBar_NM, self.ui.action_Spatial_Res, self.ui.spatialres_popup)


def create_tomouniformity_popup(self):
    # create a popup for the scale factor
    self.ui.tomouniformity_popup = PopupToolbar()
    self.ui.sbFirstFrame = QSpinBox()
    self.ui.tomouniformity_popup.add_hcontrol('First frame', self.ui.sbFirstFrame)
    self.ui.sbFirstFrame.setValue(self.settings.value('Tomographic Uniformity/First frame', 0, type=int))
    self.ui.sbLastFrame = QSpinBox()
    self.ui.tomouniformity_popup.add_hcontrol('Last frame', self.ui.sbLastFrame)
    self.ui.sbLastFrame.setValue(self.settings.value('Tomographic Uniformity/Last frame', -1, type=int))
    self.replace_action_with_long_press(self.ui.toolBar_NM, self.ui.action_Tomo_Uni, self.ui.tomouniformity_popup)


