"""
=========================================================================
Define popup dialogs for toolbar buttons
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

from linaqa_types import (
    phantom3D_list,
    vmat_list,
    phantom2D_list,
    spatial_res_list,
    mlc_list)
from qt_subclasses import MyDoubleSpinBox, PopupToolbar, LongPressToolButton

from PyQt5.QtWidgets import QComboBox, QSpinBox, QTimeEdit
from PyQt5.QtCore import QPoint, QTime


def replace_action_with_long_press(toolbar, action, popup_widget):
    """
    Replace a toolbar action with a LongPressToolButton

    Args:
        toolbar: The QToolBar containing the action
        action: The QAction to replace
        popup_widget: The PopupToolbar to show on long press
    """
    # Find the widget for this action
    widget = toolbar.widgetForAction(action)

    # Create new long-press button
    button = LongPressToolButton()
    button.setDefaultAction(action)
    button.set_popup_widget(popup_widget)

    # Replace the action with our custom button
    toolbar.insertWidget(action, button)
    toolbar.removeAction(action)

    return button


def create_popups(form):
    create_3dphantom_popup(form)
    create_mlc_popup(form)
    create_vmat_popup(form)
    create_2dphantom_popup(form)
    create_scale_popup(form)
    create_spatialres_popup(form)
    create_tomouniformity_popup(form)
    create_simplesens_popup(form)
    create_suv_uptake_popup(form)


def initialize_popups(form):
    initialize_3dphantom_popup(form)
    initialize_mlc_popup(form)
    initialize_vmat_popup(form)
    initialize_2dphantom_popup(form)
    initialize_scale_popup(form)
    initialize_spatialres_popup(form)
    initialize_tomouniformity_popup(form)
    initialize_simplesens_popup(form)
    # initialize_suv_uptake_popup(form)


def update_popups(form):
    if form.imager.datasets[0].Modality == "PT":
        update_suv_uptake_popup(form)


def create_3dphantom_popup(form):
    # create popup for the 3D phantom analysis
    form.ui.phantom3d_popup = PopupToolbar()
    form.ui.cbCatPhan = QComboBox()
    form.ui.cbCatPhan.setFixedWidth(120)
    form.ui.phantom3d_popup.add_vcontrol("Select phantom:", form.ui.cbCatPhan)
    form.ui.cbCatPhan.addItems(phantom3D_list)
    form.ui.cbCatPhan.currentIndexChanged.connect(form.on_cbcatphan_changed)
    replace_action_with_long_press(form.ui.toolBar_Rx, form.ui.action_CatPhan, form.ui.phantom3d_popup)
    replace_action_with_long_press(form.ui.toolBar_Dx, form.ui.action_CatPhan, form.ui.phantom3d_popup)


def initialize_3dphantom_popup(form):
    catphan_type = form.settings.value("3D Phantoms/3D Type")
    index = form.ui.cbCatPhan.findText(catphan_type)
    if index >= 0:
        form.ui.cbCatPhan.setCurrentIndex(index)
    else:
        raise Exception("Invalid setting in 3D Phantoms/3D Type")


def create_mlc_popup(form):
    # create popup for the mlc analysis
    form.ui.mlc_popup = PopupToolbar()
    form.ui.cbMLC = QComboBox()
    form.ui.cbMLC.setFixedWidth(120)
    form.ui.mlc_popup.add_vcontrol("Select MLC:", form.ui.cbMLC)
    form.ui.cbMLC.addItems(mlc_list)
    form.ui.cbMLC.currentIndexChanged.connect(form.on_cbmlc_changed)
    replace_action_with_long_press(form.ui.toolBar_Rx, form.ui.action_Picket_Fence, form.ui.mlc_popup)


def initialize_mlc_popup(form):
    mlc_type = form.settings.value("Picket Fence/MLC Type")
    index = form.ui.cbMLC.findText(mlc_type)
    if index >= 0:
        form.ui.cbMLC.setCurrentIndex(index)
    else:
        raise Exception("Invalid setting in Picket Fence/MLC Type")


def create_vmat_popup(form):
    # create popup for the VMAT analysis
    form.ui.vmat_popup = PopupToolbar()
    form.ui.cbVMAT = QComboBox()
    form.ui.cbVMAT.setFixedWidth(120)
    form.ui.vmat_popup.add_vcontrol("Select VMAT test:", form.ui.cbVMAT)
    form.ui.cbVMAT.addItems(vmat_list)
    form.ui.cbVMAT.currentIndexChanged.connect(form.on_cbvmat_changed)
    replace_action_with_long_press(form.ui.toolBar_Rx, form.ui.action_VMAT, form.ui.vmat_popup)
    form.on_cbvmat_changed(form.ui.cbVMAT.currentIndex())


def initialize_vmat_popup(form):
    vmat_type = form.settings.value("VMAT/VMAT test")
    index = form.ui.cbVMAT.findText(vmat_type)
    if index >= 0:
        form.ui.cbVMAT.setCurrentIndex(index)
    else:
        raise Exception("Invalid setting in VMAT/VMAT test")


def create_2dphantom_popup(form):
    # create popup for the 2D phantom analysis
    form.ui.phantom2d_popup = PopupToolbar()

    # add select phantom listbox
    form.ui.cbPhan2D = QComboBox()
    form.ui.phantom2d_popup.add_vcontrol("Select phantom:", form.ui.cbPhan2D)
    form.ui.cbPhan2D.addItems(phantom2D_list)
    form.ui.cbPhan2D.currentIndexChanged.connect(form.on_2dphantom_changed)

    # add angle override spinbox
    form.ui.sbAngle = QSpinBox()
    form.ui.sbAngle.setRange(-180, 360)
    form.ui.phantom2d_popup.add_vcontrol("Angle Override:", form.ui.sbAngle)

    # add centre override spinboxes
    form.ui.sbCentreX = QSpinBox()
    form.ui.sbCentreY = QSpinBox()
    form.ui.sbCentreX.setRange(0, 2048)
    form.ui.sbCentreY.setRange(0, 2048)
    form.ui.phantom2d_popup.add_vcontrol("Center Override:")
    form.ui.phantom2d_popup.add_hcontrol("X", form.ui.sbCentreX)
    form.ui.phantom2d_popup.add_hcontrol("Y", form.ui.sbCentreY)

    replace_action_with_long_press(form.ui.toolBar_Rx, form.ui.action_2DPhantoms, form.ui.phantom2d_popup)
    replace_action_with_long_press(form.ui.toolBar_Dx, form.ui.action_2DPhantoms, form.ui.phantom2d_popup)


def initialize_2dphantom_popup(form):
    phan2d_type = form.settings.value("2D Phantoms/2D Type")
    index = form.ui.cbPhan2D.findText(phan2d_type)
    if index >= 0:
        form.ui.cbPhan2D.setCurrentIndex(index)
    else:
        raise Exception("Invalid setting in 2D Phantoms/2D Type")
    form.ui.sbAngle.setValue(form.settings.value("2D Phantoms/Angle override", 0, type=int))
    point = form.settings.value("2D Phantoms/Center override", QPoint(0, 0), type=QPoint)
    form.ui.sbCentreX.setValue(point.x())
    form.ui.sbCentreY.setValue(point.y())


def create_scale_popup(form):
    # create a popup for the scale factor
    form.ui.scale_popup = PopupToolbar()
    form.ui.dsbScaleFactor = MyDoubleSpinBox()
    form.ui.dsbScaleFactor.setSingleStep(0.01)
    form.ui.scale_popup.add_hcontrol("Scale Factor:", form.ui.dsbScaleFactor)
    replace_action_with_long_press(form.ui.toolBar_Dx, form.ui.action_Scale_Image, form.ui.scale_popup)


def initialize_scale_popup(form):
    form.ui.dsbScaleFactor.setValue(form.settings.value("PyDicom/Scale factor", 1.0, type=float))


def create_spatialres_popup(form):
    # we have to insert a Combox for the spatial resolution test manually into the toolbar
    form.ui.spatialres_popup = PopupToolbar()
    form.ui.cbSpatialRes = QComboBox()
    form.ui.spatialres_popup.add_vcontrol("Select spatial resolution test:", form.ui.cbSpatialRes)
    form.ui.cbSpatialRes.addItems(spatial_res_list)
    form.ui.cbSpatialRes.currentIndexChanged.connect(form.on_spatialres_changed)
    replace_action_with_long_press(form.ui.toolBar_NM, form.ui.action_Spatial_Res, form.ui.spatialres_popup)


def initialize_spatialres_popup(form):
    spatial_res_type = form.settings.value("Spatial Resolution/Resolution test", "Four Bar", type=str)
    index = form.ui.cbSpatialRes.findText(spatial_res_type)
    if index >= 0:
        form.ui.cbSpatialRes.setCurrentIndex(index)
    else:
        raise Exception("Invalid setting in Spatial Resolution/Resolution test")


def create_tomouniformity_popup(form):
    # create a popup for the scale factor
    form.ui.tomouniformity_popup = PopupToolbar()
    form.ui.sbFirstFrame = QSpinBox()
    form.ui.tomouniformity_popup.add_hcontrol("First frame", form.ui.sbFirstFrame)
    form.ui.sbLastFrame = QSpinBox()
    form.ui.tomouniformity_popup.add_hcontrol("Last frame", form.ui.sbLastFrame)
    replace_action_with_long_press(form.ui.toolBar_NM, form.ui.action_Tomo_Uni, form.ui.tomouniformity_popup)


def initialize_tomouniformity_popup(form):
    form.ui.sbFirstFrame.setValue(form.settings.value("Tomographic Uniformity/First frame", 0, type=int))
    form.ui.sbLastFrame.setValue(form.settings.value("Tomographic Uniformity/Last frame", -1, type=int))


def create_simplesens_popup(form):
    # create a popup for the simple sensitivity analysis
    form.ui.simplesens_popup = PopupToolbar()
    form.ui.dsbSimpleSensActivity = MyDoubleSpinBox()
    form.ui.dsbSimpleSensActivity.setSingleStep(0.01)
    form.ui.simplesens_popup.add_hcontrol("Activity (MBq):", form.ui.dsbSimpleSensActivity)
    replace_action_with_long_press(form.ui.toolBar_NM, form.ui.action_Simple_Sens, form.ui.simplesens_popup)


def initialize_simplesens_popup(form):
    form.ui.dsbSimpleSensActivity.setValue(form.settings.value("Simple Sensitivity/Activity MBq", 40.0, type=float))


def create_suv_uptake_popup(form):
    # create a popup for the EARL contrast analysis
    form.ui.earl_popup = PopupToolbar()

    form.ui.earl_popup.add_hcontrol("Background compartment")
    form.ui.sbBgndVol = QSpinBox()
    form.ui.sbBgndVol.setRange(0, 10000)
    form.ui.earl_popup.add_hcontrol("Volume (ml):", form.ui.sbBgndVol)

    form.ui.dsbBgndDose = MyDoubleSpinBox()
    form.ui.dsbBgndDose.setRange(0.0, 200.0)
    form.ui.earl_popup.add_hcontrol("Dose (MBq):", form.ui.dsbBgndDose)

    form.ui.teBgndDoseTime = QTimeEdit()
    form.ui.teBgndDoseTime.setDisplayFormat("hh:mm:ss")
    form.ui.earl_popup.add_hcontrol("Measured at:", form.ui.teBgndDoseTime)

    form.ui.sbBgndRes = QSpinBox()
    form.ui.earl_popup.add_hcontrol("Residual Dose (MBq)", form.ui.sbBgndRes)

    form.ui.teBgndResTime = QTimeEdit()
    form.ui.teBgndResTime.setDisplayFormat("hh:mm:ss")
    form.ui.earl_popup.add_hcontrol("Measured at:", form.ui.teBgndResTime)

    form.ui.earl_popup.add_hcontrol("Stock solution (spheres)")
    form.ui.sbStockVol = QSpinBox()
    form.ui.sbStockVol.setRange(0, 10000)
    form.ui.earl_popup.add_hcontrol("Volume (ml):", form.ui.sbStockVol)

    form.ui.dsbStockDose = MyDoubleSpinBox()
    form.ui.dsbStockDose.setRange(0, 200)
    form.ui.earl_popup.add_hcontrol("Dose (spheres) (MBq):", form.ui.dsbStockDose)

    form.ui.teStockDoseTime = QTimeEdit()
    form.ui.teStockDoseTime.setDisplayFormat("hh:mm:ss")
    form.ui.earl_popup.add_hcontrol("Measured at:", form.ui.teStockDoseTime)

    form.ui.sbStockRes = QSpinBox()
    form.ui.earl_popup.add_hcontrol("Residual Dose (MBq)", form.ui.sbStockRes)

    form.ui.teStockResTime = QTimeEdit()
    form.ui.teStockResTime.setDisplayFormat("hh:mm:ss")
    form.ui.earl_popup.add_hcontrol("Measured at:", form.ui.teStockResTime)

    form.ui.teSeriesTime = QTimeEdit()
    form.ui.teSeriesTime.setDisplayFormat("hh:mm:ss")
    form.ui.earl_popup.add_hcontrol("Acquisition time:", form.ui.teSeriesTime)

    button = replace_action_with_long_press(form.ui.toolBar_NM, form.ui.action_SUV_Uptake, form.ui.earl_popup)
    # button.set_popup_initializer(lambda: initialize_suv_uptake_popup(form))


def update_suv_uptake_popup(form):
    """Load values according to
    https://qibawiki.rsna.org/images/6/62/SUV_vendorneutral_pseudocode_happypathonly_20180626_DAC.pdf"""
    if form.imager is not None:
        # pull values from current image
        ds = form.imager.datasets[form.imager.index]
        try:
            # get volume if not defined in settings
            vol = form.settings.value("SUV Uptake/Background vol", 0, type=int)
            if vol == 0:
                # TODO: check if volume tag exists and use that otherwise estimate from patient weight
                vol = ds[0x0010, 0x1030].value * 1000
            form.ui.sbBgndVol.setValue(int(vol))

            # Get Radiopharmaceutical Information Sequence
            seq = ds[0x0054, 0x0016][0]

            # get Radionuclide Total Dose
            backgnd_dose = form.settings.value("SUV Uptake/Background dose", 0, type=float)
            if backgnd_dose == 0:
                backgnd_dose = int(seq[0x0018, 0x1074].value) / 1000000            # convert to megabequerel
            form.ui.dsbBgndDose.setValue(backgnd_dose)
            stock_dose = form.settings.value("SUV Uptake/Stock dose", 0, type=float)
            if stock_dose == 0:
                stock_dose = backgnd_dose
            form.ui.dsbStockDose.setValue(stock_dose)

            # get Radionuclide measurement time
            measure_time = seq[0x0018, 0x1072].value
            time = QTime.fromString(measure_time.split(".")[0], "HHmmss")
            form.ui.teBgndDoseTime.setTime(time)
            form.ui.teBgndResTime.setTime(time)
            form.ui.teStockDoseTime.setTime(time)
            form.ui.teStockResTime.setTime(time)

            # Stock solution for spheres is 1L
            form.ui.sbStockVol.setValue(form.settings.value("SUV Uptake/Stock vol", 0, type=int))

            # get series time
            series_time = ds[0x0008, 0x0031].value
            form.ui.teSeriesTime.setTime(QTime.fromString(series_time.split(".")[0], "HHmmss"))
        except KeyError:
            form.ui.statusbar.status_error("Missing DICOM tag(s)")
