"""
============================================
Linear Accelerator Quality Assurance Toolkit
============================================

Frontend GUI to pylinac and pydicom with some added functionality.
Usage: python LinaQA.pyw

"""
# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2025

import sys
import os.path as osp
import os
import io
from pylinac.core.io import TemporaryZipDirectory
from platform import system
from PyQt5.QtWidgets import (
     QApplication,
     QMainWindow,
     QFileDialog,
     QMessageBox,
     QComboBox,
     QLabel,
     QAction,
     QInputDialog,
     QHeaderView)
from PyQt5.QtGui import (
     QGuiApplication,
     QPixmap,
     QImage,
     QIcon,
     QFont,
     QMouseEvent,
     QStandardItemModel,
     QStandardItem,
     QPalette)
from PyQt5.QtCore import Qt, QSettings, QSortFilterProxyModel
import matplotlib.pyplot as plt
import numpy as np
import webbrowser

from LinaQAForm import Ui_LinaQAForm
from linaqa_types import (
    supported_modalities,
    catphan_list,
    vmat_list,
    phantom2D_list,
    faint_red,
    faint_green,
    faint_yellow,
    MyDoubleSpinBox)
from aboutpackage import About
from aboutpackage.aboutform import version
from settingsunit import Settings, set_default_settings
from imageunit import Imager
from decorators import show_wait_cursor
from misc_utils import (
    open_path,
    get_dot_attr,
    set_dot_attr,
    del_dot_attr,
    text_to_tag,
    dataset_to_stream,
    datasets_to_stream)
from pylinac_subclasses import MyMaxCountRate, MyPlanarUniformity

from tablemodel import TableModel
from pydicom import compat
import pydicom
from pylinac.core import pdf
from pylinac.core.image import DicomImageStack
from pylinac import (
    image,
    picketfence,
    ct,
    winston_lutz,
    planar_imaging,
    vmat,
    starshot,
    log_analyzer,
    QuartDVT,
    ACRCT,
    ACRMRILarge)


class LinaQA(QMainWindow):

    def __init__(self, parent=None):
        super(LinaQA, self).__init__()
        self.imager = None
        self.ref_imager = None
        self.mouse_button_down = False
        self.changed = False
        self.mouse_last_pos = None
        self.filenames = []
        self.ref_filename = ''
        self.working_dir = ''
        self.zip_dir = None
        self.source_model = None
        self.proxy_model = None
        self.table_model = None
        self.is_changed = False
        self.old_tab = 0
        self.ui = Ui_LinaQAForm()
        self.ui.setupUi(self)
        self.settings = QSettings()
        if self.settings.contains('Window/Size'):
            self.resize(self.settings.value('Window/Size'))
        if self.settings.contains('Window/Position'):
            self.move(self.settings.value('Window/Position'))
        set_default_settings(self.settings)

        # we have to insert a Combox for the CatPhan manually into the toolbar
        self.ui.cbCatPhan = QComboBox()
        self.ui.cbCatPhan.setFixedWidth(120)
        self.ui.toolBar_Rx.insertWidget(self.ui.action_Picket_Fence, self.ui.cbCatPhan)
        self.ui.cbCatPhan.addItems(catphan_list)
        self.ui.toolBar_Rx.insertSeparator(self.ui.action_Picket_Fence)
        self.ui.cbCatPhan.currentIndexChanged.connect(self.on_cbcatphan_changed)
        catphan_type = self.settings.value('3D Phantom/Type')
        index = self.ui.cbCatPhan.findText(catphan_type)
        if index >= 0:
            self.ui.cbCatPhan.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in 3D Phantom/Type')
        self.ui.cbCatPhan.currentIndexChanged.connect(self.on_cbcatphan_changed)

        # we have to insert a Combox for the MLC manually into the toolbar
        self.ui.cbMLC = QComboBox()
        self.ui.cbMLC.setFixedWidth(120)
        self.ui.toolBar_Rx.insertWidget(self.ui.action_VMAT, self.ui.cbMLC)
        for mlc in picketfence.MLC:
            self.ui.cbMLC.insertItem(0, mlc.value.get("name"))
        self.ui.toolBar_Rx.insertSeparator(self.ui.action_VMAT)
        mlc_type = self.settings.value('Picket Fence/MLC Type')
        index = self.ui.cbMLC.findText(mlc_type)
        if index >= 0:
            self.ui.cbMLC.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in Picket Fence/MLC Type')

        # we have to insert a Combox for the VMAT test manually into the toolbar
        self.ui.cbVMAT = QComboBox()
        self.ui.cbVMAT.setFixedWidth(120)
        self.ui.toolBar_Rx.insertWidget(self.ui.action_2DPhantoms, self.ui.cbVMAT)
        self.ui.cbVMAT.addItems(vmat_list)
        self.ui.toolBar_Rx.insertSeparator(self.ui.action_2DPhantoms)
        vmat_type = self.settings.value('VMAT/Test type')
        index = self.ui.cbVMAT.findText(vmat_type)
        if index >= 0:
            self.ui.cbVMAT.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in VMAT/Test type')

        # we have to insert a Combox for the 2D phantoms test manually into the toolbar
        self.ui.cbPhan2D = QComboBox()
        self.ui.cbPhan2D.setFixedWidth(120)
        self.ui.toolBar_Rx.insertWidget(self.ui.action_Machine_Logs, self.ui.cbPhan2D)
        self.ui.cbPhan2D.addItems(phantom2D_list)
        self.ui.toolBar_Rx.insertSeparator(self.ui.action_Machine_Logs)
        phan2d_type = self.settings.value('2D Phantom/Type')
        index = self.ui.cbPhan2D.findText(phan2d_type)
        if index >= 0:
            self.ui.cbPhan2D.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in 2D Phantom/Type')

        # we have to insert a double spinbox for the image scaling manually into the toolbar
        self.ui.toolBar_Dx.insertSeparator(self.ui.action_Scale_Image)
        self.ui.lScaleFactor = QLabel('Scale Factor:')
        self.ui.toolBar_Dx.insertWidget(self.ui.action_Gamma, self.ui.lScaleFactor)
        self.ui.dsbScaleFactor = MyDoubleSpinBox()
        self.ui.dsbScaleFactor.setFixedWidth(120)
        self.ui.dsbScaleFactor.setSingleStep(0.01)
        self.ui.toolBar_Dx.insertWidget(self.ui.action_Gamma, self.ui.dsbScaleFactor)
        self.ui.toolBar_Dx.insertSeparator(self.ui.action_Gamma)
        self.ui.dsbScaleFactor.setValue(self.settings.value('PyDicom/Scale factor', 1.0, type=float))

        # we have to insert the Exit action into the main menu manually
        action_close = QAction("action_menu_Exit", self.ui.menubar)
        action_close.setText("E&xit")
        self.ui.menubar.addAction(action_close)

        # add actions to treeView
        self.ui.treeView.addAction(self.ui.action_Copy)
        self.ui.treeView.addAction(self.ui.action_Select_all)
        self.ui.treeView.addAction(self.ui.action_Clear_selection)
        self.ui.treeView.addAction(self.ui.action_Find_tag)
        self.ui.treeView.addAction(self.ui.action_Expand_all)
        self.ui.treeView.addAction(self.ui.action_Collapse_all)

        # connect menu and toolbar actions
        self.ui.action_Open.triggered.connect(self.choose_file)
        self.ui.action_Open_Ref.triggered.connect(self.open_ref)
        self.ui.action_Save.triggered.connect(self.save_file)
        self.ui.action_Save_as.triggered.connect(self.save_file_as)
        self.ui.action_Save_all.triggered.connect(self.save_all)
        self.ui.action_About.triggered.connect(self.show_about)
        self.ui.action_Rx_Toolbar.triggered.connect(self.show_rx_toolbar)
        self.ui.action_Dx_Toolbar.triggered.connect(self.show_dx_toolbar)
        self.ui.action_NM_Toolbar.triggered.connect(self.show_nm_toolbar)
        self.ui.action_DICOM_tags.triggered.connect(self.show_dicom_toolbar)
        self.ui.action_PyDicomH.triggered.connect(self.pydicom_help)
        self.ui.action_PylinacH.triggered.connect(self.pylinac_help)
        action_close.triggered.connect(self.close)
        self.ui.action_Settings.triggered.connect(self.show_settings)
        self.ui.action_Invert.triggered.connect(self.invert)
        self.ui.action_Auto_Window.triggered.connect(self.auto_window)
        self.ui.action_CatPhan.triggered.connect(self.analyse_catphan)
        self.ui.action_Picket_Fence.triggered.connect(self.analyse_picket_fence)
        self.ui.action_Winston_Lutz.triggered.connect(self.analyse_winston_lutz)
        self.ui.action_2DPhantoms.triggered.connect(self.analyse_2d_phantoms)
        self.ui.action_Starshot.triggered.connect(self.analyse_star)
        self.ui.action_VMAT.triggered.connect(self.analyse_vmat)
        self.ui.action_Machine_Logs.triggered.connect(self.analyse_log)
        self.ui.action_Pixel_Data.triggered.connect(self.edit_pixel_data)
        self.ui.action_Scale_Image.triggered.connect(self.scale_image)
        self.ui.action_Gamma.triggered.connect(self.analyse_gamma)
        self.ui.action_Sum_Image.triggered.connect(self.sum_image)
        self.ui.action_Ave_Image.triggered.connect(self.avg_image)
        self.ui.action_MCR.triggered.connect(self.max_count_rate)
        self.ui.action_Uniformity.triggered.connect(self.planar_uniformity)
        self.ui.action_Find_tag.triggered.connect(self.find_tag)
        self.ui.qle_filter_tag.textChanged.connect(self.filter_tag)
        self.ui.action_Insert_tag.triggered.connect(self.insert_tag)
        self.ui.action_Edit_tag.triggered.connect(self.edit_tag)
        self.ui.action_Delete_tag.triggered.connect(self.del_tag)
        self.ui.action_Notes.triggered.connect(self.show_notes)

        # connect treeView actions
        self.ui.action_Copy.triggered.connect(self.copy_tag)
        self.ui.action_Select_all.triggered.connect(self.selectall_tags)
        self.ui.action_Clear_selection.triggered.connect(self.clearall_tags)
        self.ui.action_Expand_all.triggered.connect(self.expandall_tags)
        self.ui.action_Collapse_all.triggered.connect(self.collapseall_tags)
        self.ui.tabWidget.tabCloseRequested.connect(lambda index: self.ui.tabWidget.setTabVisible(index, False))
        self.ui.tabWidget.currentChanged.connect(self.tab_changed)

        # prepare ui
        self.setWindowTitle(f'LinaQA v{version}')
        self.ui.treeView.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui.tabWidget.setTabVisible(1, False)
        self.ui.tabWidget.setTabVisible(2, False)
        self.ui.tabWidget.setTabVisible(3, False)
        self.ui.tabWidget.setTabVisible(4, False)
        self.show_rx_toolbar()
        self.show_dicom_toolbar()
        self.show_dx_toolbar()
        self.show_nm_toolbar()
        self.status_good('LinaQA initialised correctly. Open DICOM file or drag and drop')

# ---------------------------------------------------------------------------------------------------------------------
# Status bar routines
# ---------------------------------------------------------------------------------------------------------------------
    def status_clear(self):
        # Clear the status bar
        qsb_color = self.ui.statusbar.palette().color(QPalette.Base).getRgb()
        mystylesheet = f"background-color: {qsb_color}; border-top: 1px outset grey;"
        self.ui.statusbar.setStyleSheet(mystylesheet)
        self.ui.statusbar.showMessage('')

    def status_message(self, status_message):
        # Clear the status bar
        qsb_color = self.ui.statusbar.palette().color(QPalette.Base).getRgb()
        mystylesheet = f"background-color: {qsb_color}; border-top: 1px outset grey;"
        self.ui.statusbar.setStyleSheet(mystylesheet)
        # self.ui.statusbar.setToolTip(self.ui.statusbar.toolTip() + '\n' + status_message)
        self.ui.statusbar.showMessage(status_message)

    def status_warn(self, status_message):
        mystylesheet = f"background-color: {faint_yellow}; border-top: 1px outset grey;"
        self.ui.statusbar.setStyleSheet(mystylesheet)
        self.ui.statusbar.setToolTip(self.ui.statusbar.toolTip() + '\n' + status_message)
        self.ui.statusbar.showMessage(status_message)

    def status_good(self, status_message):
        mystylesheet = f"background-color: {faint_green}; border-top: 1px outset grey;"
        self.ui.statusbar.setStyleSheet(mystylesheet)
        self.ui.statusbar.setToolTip(self.ui.statusbar.toolTip() + '\n' + status_message)
        self.ui.statusbar.showMessage(status_message)

    def status_error(self, status_message):
        mystylesheet = f"background-color: {faint_red}; border-top: 1px outset grey;"
        self.ui.statusbar.setStyleSheet(mystylesheet)
        self.ui.statusbar.setToolTip(self.ui.statusbar.toolTip() + '\n' + status_message)
        self.ui.statusbar.showMessage(status_message)

# ---------------------------------------------------------------------------------------------------------------------
# User interface routines
# ---------------------------------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.settings.setValue('Window/Size', self.size())
        self.settings.setValue('Window/Position', self.pos())
        if self.is_changed:
            reply = QMessageBox.question(self, 'Quit', 'You have made changes. Are you sure you want to quit?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    def open_image(self, filenames, force_read: bool = False):
        num_total = len(filenames)
        num_bad = 0
        first_modality = ''

        # Clear non-dicom files
        datasets = []
        # we have to treat the first file separately to get the image modality
        try:
            ds = pydicom.dcmread(filenames[0], force=force_read)
            if 'TransferSyntaxUID' not in ds.file_meta:
                ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            first_modality = ds.Modality
            if ds.file_meta.TransferSyntaxUID.is_compressed:
                ds.decompress()
            datasets.append(ds)
        except pydicom.errors.InvalidDicomError:
            num_bad += 1
            filenames.remove(filenames[0])

        for file in filenames[1:]:
            try:
                ds = pydicom.dcmread(file, force=force_read)
                if 'TransferSyntaxUID' not in ds.file_meta:
                    ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                modality = ds.Modality
                frames = 1
                if hasattr(ds, "NumberOfFrames"):
                    frames = ds.NumberOfFrames
                # cannot mix modalities or multi frame images
                if (modality != first_modality) or (frames > 1) or not hasattr(ds, 'PixelData'):
                    raise pydicom.errors.InvalidDicomError
                if ds.file_meta.TransferSyntaxUID.is_compressed:
                    ds.decompress()
                datasets.append(ds)

            except pydicom.errors.InvalidDicomError:
                num_bad += 1
                filenames.remove(file)
        num_ok = num_total - num_bad

        # Try to sort based on instance number then SOPInstanceUID
        sorted_method = "filenames"
        try:
            order = sorted(range(len(datasets)), key=lambda i: datasets[i].InstanceNumber)
            datasets = [datasets[i] for i in order]
            filenames = [filenames[i] for i in order]
            sorted_method = "instance number"
        except (TypeError, AttributeError):
            try:
                order = sorted(range(len(datasets)), key=lambda i: datasets[i].SOPInstanceUID)
                datasets = [datasets[i] for i in order]
                filenames = [filenames[i] for i in order]
                sorted_method = "SOP instance UID"
            except (TypeError, AttributeError):
                pass
        self.imager = Imager(datasets)
        self.filenames = filenames
        if num_bad == 0:
            self.status_message(f"Opened {num_ok} DICOM file(s) sorted on {sorted_method}. Rejected {num_bad} bad files.")
        else:
            self.status_warn(f"Opened {num_ok} DICOM file(s) sorted on {sorted_method}. Rejected {num_bad} bad files.")

    def open_file(self):
        # is the filename a directory or archive
        if len(self.filenames) == 1:
            if os.path.isdir(self.filenames[0]):
                # get list of files in directory
                dir_path = osp.realpath(self.filenames[0])
                self.filenames = [os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path)
                                  if os.path.isfile(os.path.join(dir_path, file_name))]
            # check if file is archive
            elif osp.splitext(self.filenames[0])[1] == '.zip':
                self.zip_dir = TemporaryZipDirectory(self.filenames[0], delete=False)
                dir_path = self.zip_dir.name
                self.filenames = [os.path.join(dir_path, file_name) for file_name in os.listdir(dir_path)
                                  if os.path.isfile(os.path.join(dir_path, file_name))]
        # is the file a DICOM file?
        force_open = self.settings.value('PyDicom/Force', False, type=bool)
        if pydicom.misc.is_dicom(self.filenames[0]) or force_open:
            self.open_image(self.filenames, force_open)
            # does the file have a recognised image format?
            if ((self.imager.datasets[0].Modality in supported_modalities)
                    and hasattr(self.imager.datasets[0], 'PixelData')):
                self.tab_changed(0)
                # self.show_image(self.imager.get_current_image(), self.ui.qlImage)
                # self.ui.qlImage.show()
            else:
                self.ui.tabWidget.setTabVisible(0, False)
                self.ui.action_DICOM_tags.setChecked(True)
                self.tab_changed(1)
                # self.ui.tabWidget.setTabVisible(0, False)
            # self.show_dicom_toolbar()
            self.edit_pixel_data()
        else:
            the_image = QPixmap(self.filenames[0])
            if the_image.isNull():
                self.status_error("File is not a valid image file!")
            else:
                self.ui.qlImage.setPixmap(the_image)
                self.ui.qlImage.setScaledContents(True)

    def choose_file(self):
        # set up ui
        self.ui.qlImage.clear()
        self.ui.tabWidget.setTabVisible(0, True)
        self.ui.tabWidget.setCurrentIndex(0)

        self.is_changed = False
        self.status_clear()
        del self.imager
        self.imager = None

        # get filename(s)
        if len(self.filenames) > 0:
            dirpath = osp.dirname(osp.realpath(self.filenames[0]))
        else:
            dirpath = self.working_dir
        ostype = system()
        if ostype == 'Windows':
            file_filter = 'DICOM files (*.dcm);;ZIP files (*.zip);;All files (*.*)'
        else:
            file_filter = 'DICOM files (*.dcm);;ZIP files (*.zip);;All files (*)'
        self.filenames = QFileDialog.getOpenFileNames(self, 'Open DICOM file', dirpath, file_filter)[0]
        if len(self.filenames) > 0:
            self.working_dir = osp.dirname(osp.realpath(self.filenames[0]))
            self.open_file()

    def save_file(self):
        if self.imager:
            ds = self.imager.datasets[self.imager.index]
            if hasattr(ds, 'pixel_array'):
                arr = ds.pixel_array
                ds.PixelData = arr.tobytes()
            ds.save_as(ds.filename, True)
            self.is_changed = False
            self.status_message('File saved')

    def save_file_as(self):
        self.status_clear()
        dirpath = osp.dirname(osp.realpath(self.filenames[self.imager.index]))
        ostype = system()
        if ostype == 'Windows':
            filename = QFileDialog.getSaveFileName(self, 'Save DICOM file', dirpath,
                                                         'DICOM files (*.dcm);;All files (*.*)')[0]
        else:
            filename = QFileDialog.getSaveFileName(self, 'Save DICOM file', dirpath,
                                                         'DICOM files (*.dcm);;All files (*)')[0]
        if self.imager and filename != '':
            ds = self.imager.datasets[self.imager.index]
            if hasattr(ds, 'pixel_array'):
                arr = ds.pixel_array
                ds.PixelData = arr.tobytes()
            ds.save_as(filename, True)
            self.is_changed = False
            self.status_message('File save as ' + filename)

    def save_all(self):
        self.status_clear()
        dirpath = osp.dirname(osp.realpath(self.filenames[self.imager.index]))
        ostype = system()
        dirpath = QFileDialog.getExistingDirectory(self, 'Choose directory to save files to', dirpath)
        if self.imager and dirpath != '':
            for i, ds in enumerate(self.imager.datasets):
                if hasattr(ds, 'pixel_array'):
                    arr = ds.pixel_array
                    ds.PixelData = arr.tobytes()
                filename = osp.basename(self.filenames[i])
                filename = osp.splitext(filename)[0] + '_un.dcm'
                ds.save_as(osp.join(dirpath, filename), True)
            self.is_changed = False
            self.status_message(f'{i} images saved in ' + dirpath)

    def show_image(self, numpy_array, label: QLabel):
        if numpy_array is not None:
            # create a QImage from Numpy array and display it in a label
            qpimage = QImage(numpy_array, numpy_array.shape[1], numpy_array.shape[0], QImage.Format_ARGB32)
            label.setPixmap(QPixmap.fromImage(qpimage).
                            scaled(label.width(),
                            label.height(),
                            Qt.KeepAspectRatio))

    def show_about(self):
        about = About()
        about.exec()

    def pydicom_help(self):
        webbrowser.open('https://pydicom.github.io/pydicom/stable/')

    def pylinac_help(self):
        webbrowser.open('https://pylinac.readthedocs.io/en/latest/')

    def show_settings(self):
        settings = Settings()
        settings.exec()

    def show_rx_toolbar(self):
        self.ui.toolBar_Rx.setVisible(self.ui.action_Rx_Toolbar.isChecked())

    def show_dx_toolbar(self):
        self.ui.toolBar_Dx.setVisible(self.ui.action_Dx_Toolbar.isChecked())

    def show_nm_toolbar(self):
        self.ui.toolBar_NM.setVisible(self.ui.action_NM_Toolbar.isChecked())

    def wheelEvent(self, e):
        if self.imager is not None and hasattr(self.imager, "values"):
            self.imager.index += int(e.angleDelta().y()/120)
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)
            self.status_message(f"Current slice {self.imager.index}")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mouse_last_pos = event.globalPos()
            self.mouse_button_down = True

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mouse_last_pos = None
            self.mouse_button_down = False

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mouse_button_down and self.imager is not None and hasattr(self.imager, "values"):
            delta = (event.globalPos() - self.mouse_last_pos) * (self.imager.window_width/1000)
            self.mouse_last_pos = event.globalPos()
            self.imager.window_width += delta.x()
            self.imager.window_center += delta.y()
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)
            self.status_message(f"Window center {self.imager.window_center}, Window width {self.imager.window_width}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            urls = event.mimeData().text().split("\n")
            self.filenames = []
            for url in urls:
                if url != "":
                    filename = url.split('/', 2)[2]
                    if filename != "":
                        self.filenames.append(filename)
            if self.filenames:
                self.open_file()

    def resizeEvent(self, event):
        if self.imager is not None and hasattr(self.imager, "values"):
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)

    def tab_changed(self, index):
        # self.ui.action_DICOM_tags.setChecked(self.ui.tabWidget.isTabVisible(1))
        if self.imager:
            if (index == 0) and (self.imager is not None):
                if self.old_tab == 3:
                    if hasattr(self.imager.datasets[self.imager.index], 'pixel_array'):
                        self.imager.datasets[self.imager.index].PixelData = (
                            self.imager.datasets[self.imager.index].pixel_array.tobytes())
                        self.imager.load_pixel_data(self.imager.datasets)
                self.show_image(self.imager.get_current_image(), self.ui.qlImage)
                self.ui.tabWidget.setTabVisible(0, True)
                self.ui.tabWidget.setCurrentIndex(0)
            elif index == 1:
                self.ui.action_DICOM_tags.setChecked(True)
                self.show_dicom_toolbar()
            elif (index == 2) and (self.ref_imager is not None):
                self.show_image(self.ref_imager.get_current_image(), self.ui.qlRef)
                self.ui.tabWidget.setTabVisible(2, True)
                self.ui.tabWidget.setCurrentIndex(2)
            elif (index ==3) and (self.imager is not None):
                self.edit_pixel_data()
        self.old_tab = index

    def show_notes(self):
        if self.ui.action_Notes.isChecked():
            self.ui.tabWidget.setTabVisible(4, True)
            self.ui.tabWidget.setCurrentIndex(4)
        else:
            self.ui.tabWidget.setTabVisible(4, False)

    def show_results(self, test, filename):
        if osp.exists(filename):
            QApplication.restoreOverrideCursor()
            filename = QFileDialog.getSaveFileName(self, "File exists, save file as:", filename, "PDF files (*.pdf)")[0]
        if len(filename) > 0:
            test.publish_pdf(filename,
                             notes=self.ui.pte_notes.toPlainText() if self.ui.pte_notes.toPlainText() != '' else None,
                             metadata=self.settings.value('General/Metadata'),
                             logo=self.settings.value('General/Logo'))
            if open_path(filename):
                self.status_message('Results displayed in PDF')
            else:
                self.status_error('No reader to open document')
        else:
            self.status_warn("Results not saved.")

    def on_cbcatphan_changed(self, index_value: str):
        cb_text = self.ui.cbCatPhan.currentText()
        if cb_text.find("ACR") >= 0:
            self.ui.action_CatPhan.setIcon(QIcon(":/Icons/Icons/ACRPhantoms.png"))
        elif cb_text.find("Quart") >= 0:
            self.ui.action_CatPhan.setIcon(QIcon(":/Icons/Icons/Quart.png"))
        else:
            self.ui.action_CatPhan.setIcon(QIcon(":/Icons/Icons/Catphan.png"))

# ---------------------------------------------------------------------------------------------------------------------
# Show DICOM tag section
# ---------------------------------------------------------------------------------------------------------------------
    def show_dicom_toolbar(self):
        self.ui.toolBar_DCM.setVisible(self.ui.action_DICOM_tags.isChecked())
        # create new tab
        if self.imager:
            if self.ui.action_DICOM_tags.isChecked():
                self.ui.tabWidget.setTabVisible(1, True)
                self.ui.tabWidget.setCurrentIndex(1)
                self.source_model = QStandardItemModel()
                self.proxy_model = QSortFilterProxyModel()
                font = QFont()
                if os == 'Linux':
                    font.setFamily("Monospace")
                elif os == 'Windows':
                    font.setFamily("Courier New")
                else:
                    font.setFamily("Courier")
                self.ui.treeView.setFont(font)
                # self.ui.action_Find_tag.setChecked(False)
                self.find_tag()
                self.filter_tag()
                self.show_tree()
            else:
                self.ui.tabWidget.setTabVisible(1, False)

    def show_tree(self):
        self.dataset_to_model()
        self.proxy_model.setSourceModel(self.source_model)
        self.ui.treeView.setModel(self.proxy_model)
        self.ui.treeView.show()

    def dataset_to_model(self):
        self.source_model.clear()
        model_header = list()
        idx = self.imager.index if len(self.imager.datasets) > 1 else 0
        model_header.append(self.filenames[idx])
        self.source_model.setHorizontalHeaderLabels(model_header)
        parent_item = self.source_model.invisibleRootItem()
        self.write_header(self.imager.datasets[idx], parent_item)
        self.recurse_tree(self.imager.datasets[idx], parent_item)
        return

    def write_header(self, ds, parent):
        # write meta data
        fm = ds.file_meta
        for data_element in fm:
            if isinstance(data_element.value, compat.text_type):
                item = QStandardItem(compat.text_type(data_element))
            else:
                item = QStandardItem(str(data_element))
            parent.appendRow(item)

    def recurse_tree(self, ds, parent):
        # order the dicom tags
        # write data elements
        pydicom.config.convert_wrong_length_to_UN = True
        for data_element in ds:
            if isinstance(data_element.value, compat.text_type):
                item = QStandardItem(compat.text_type(data_element))
            else:
                item = QStandardItem(str(data_element))
            parent.appendRow(item)
            if data_element.VR == "SQ":   # a sequence
                for i, ds in enumerate(data_element.value):
                    sub_item_text = "{0:s} [{1:d}]".format(data_element.name, i + 1)
                    sub_item = QStandardItem(sub_item_text)
                    item.appendRow(sub_item)
                    self.recurse_tree(ds, sub_item)

    def copy_tag(self):
        clipboard = QApplication.clipboard()
        selected_tags = ''
        for index in self.ui.treeView.selectedIndexes():
            selected_tags = selected_tags + self.ui.treeView.model().itemData(index)[0] + '\n'
        clipboard.setText(selected_tags)

    def selectall_tags(self):
        self.ui.treeView.selectAll()

    def clearall_tags(self):
        self.ui.treeView.clearSelection()

    def expandall_tags(self):
        self.ui.treeView.expandAll()

    def collapseall_tags(self):
        self.ui.treeView.collapseAll()

    def find_tag(self):
        if self.ui.action_Find_tag.isChecked():
            self.ui.fsearchbar.setVisible(True)
            self.ui.fsearchbar.setEnabled(True)
            self.ui.fsearchbar.activateWindow()
            self.ui.qle_filter_tag.setFocus()
            self.ui.action_Find_tag.setText('Hide &Filter bar')
        else:
            self.ui.qle_filter_tag.setText('')
            self.ui.fsearchbar.setVisible(False)
            self.ui.fsearchbar.setEnabled(False)
            self.ui.action_Find_tag.setText('Show &Filter bar')

    def filter_tag(self):
        """Select tags that contain requested text"""
        tag_to_find = self.ui.qle_filter_tag.text()
        if tag_to_find != '':
            self.proxy_model.setFilterKeyColumn(-1)
            self.proxy_model.setRecursiveFilteringEnabled(True)
            self.proxy_model.setFilterRegularExpression(tag_to_find)
        else:
            self.proxy_model.setFilterRegularExpression('')

    def insert_tag(self):
        self.status_warn('Inserting a DICOM tag may corrupt the file!')

        # get path for tag insertion
        proxy_index = self.ui.treeView.currentIndex()
        source_index = self.proxy_model.mapToSource(proxy_index)
        tag_parent = source_index.parent()
        tag_path = ''
        while tag_parent.data(Qt.DisplayRole) is not None:
            _, _, parent_lable, _, _ = text_to_tag(tag_parent.data(Qt.DisplayRole))
            tag_path = parent_lable + '.' + tag_path
            tag_parent = tag_parent.parent()
        tag_path = tag_path.replace(" ", "")

        ds = self.imager.datasets[self.imager.index]

        # get new tag
        input_dlg = QInputDialog(self)
        input_dlg.setInputMode(QInputDialog.TextInput)
        input_dlg.resize(500, 100)
        input_dlg.setLabelText('Create new tag as: (Group, Element) Keyword VR: Value')
        input_dlg.setTextValue('')
        input_dlg.setWindowTitle('Insert DICOM tag')
        ok = input_dlg.exec_()
        tag_text = input_dlg.textValue()

        if ok and tag_text != '':
            tag_group, tag_element, tag_keyword, tag_vr, tag_value = text_to_tag(tag_text)
            if tag_group == '0x0002':
                tag_header = 'file_meta.'
            else:
                tag_header = ''
            tag_path = (tag_header + tag_path.replace(" ", "") +
                        tag_keyword.replace(" ", "").replace("'s", "").replace("s'", "").replace("-", ""))
            if tag_vr == 'DS':
                if tag_text[0] == '[':
                    tag_text = tag_text.translate({ord(i): None for i in "[]'"}).split(',')
            try:
                set_dot_attr(ds, tag_path, tag_value)
                self.show_tree()
                self.is_changed = True
                self.status_message('Inserted ' + tag_path + ' (' + tag_group + ', ' + tag_element + ') '
                                    + tag_keyword + ' ' + tag_vr + ':' + tag_value)
            except AttributeError:
                self.status_error('Could not insert ' + tag_path)

    def edit_tag(self):
        # get current tag
        self.status_warn('Editing a DICOM tag may corrupt the file!')
        proxy_index = self.ui.treeView.currentIndex()
        source_index = self.proxy_model.mapToSource(proxy_index)
        tag_text = source_index.data(Qt.DisplayRole)
        if tag_text is not None:
            tag_group, tag_element, tag_keyword, tag_vr, _ = text_to_tag(tag_text)

            # get tag parents if any
            tag_path = ''
            tag_parent = source_index.parent()
            while tag_parent.data(Qt.DisplayRole) is not None:
                _, _, parent_lable, _, _ = text_to_tag(tag_parent.data(Qt.DisplayRole))
                tag_path = parent_lable + '.' + tag_path
                tag_parent = tag_parent.parent()
            if tag_group == '0x0002':
                tag_header = 'file_meta.'
            else:
                tag_header = ''
            label = 'Change value for ' + tag_path + '(' + tag_group + ', ' + tag_element + ') ' + tag_keyword + ' ' + tag_vr + ':'
            tag_path = (tag_header + tag_path.replace(" ", "") +
                        tag_keyword.replace(" ", "").replace("'s", "").replace("s'", "").replace("-", ""))

            # get tag value
            ds = self.imager.datasets[self.imager.index]
            orig_tag_value = get_dot_attr(ds, tag_path)

            # display in dialog for editing
            input_dlg = QInputDialog(self)
            input_dlg.setInputMode(QInputDialog.TextInput)
            input_dlg.resize(500, 100)
            input_dlg.setLabelText(label)
            input_dlg.setTextValue(str(orig_tag_value))
            input_dlg.setWindowTitle('Change DICOM tag')
            ok = input_dlg.exec_()
            tag_text = input_dlg.textValue()

            # store changed tag
            if ok and tag_text != '':
                if tag_vr == 'DS':
                    if tag_text[0] == '[':
                        tag_text = tag_text.translate({ord(i): None for i in "[]'"}).split(',')
                try:
                    set_dot_attr(ds, tag_path, tag_text)
                    self.show_tree()
                    self.is_changed = True
                    self.status_message('Changed ' + tag_path + ' to ' + tag_text)
                except AttributeError:
                    self.status_error('Could not change ' + tag_path)
        else:
            self.status_warn('No tag selected!')

    @show_wait_cursor
    def del_tag(self):
        self.status_warn('Editing a DICOM tag may corrupt the file!')
        proxy_index = self.ui.treeView.currentIndex()
        source_index = self.proxy_model.mapToSource(proxy_index)
        tag_text = source_index.data(Qt.DisplayRole)
        if tag_text is not None:
            tag_group, _, tag_keyword, _, _ = text_to_tag(tag_text)

            # get tag parents if any
            tag_path = ''
            tag_parent = source_index.parent()
            while tag_parent.data(Qt.DisplayRole) is not None:
                _, _, parent_lable, _, _ = text_to_tag(tag_parent.data(Qt.DisplayRole))
                tag_path = parent_lable + '.' + tag_path
                tag_parent = tag_parent.parent()
            if tag_group == '0x0002':
                tag_header = 'file_meta.'
            else:
                tag_header = ''
            tag_path = (tag_header + tag_path.replace(" ", "") +
                        tag_keyword.replace(" ", "").replace("'s", "").replace("s'", "")).replace("-", "")

            # delete attribute
            try:
                ds = self.imager.datasets[self.imager.index]
                del_dot_attr(ds, tag_path)
                self.show_tree()
                self.is_changed = True
                self.status_message('Deleted ' + tag_path)
            except AttributeError:
                self.status_error('Could not delete ' + tag_path)
        else:
            self.status_warn('No tag selected!')

# ---------------------------------------------------------------------------------------------------------------------
# Radiotherapy analysis
# ---------------------------------------------------------------------------------------------------------------------
    @show_wait_cursor
    def analyse_catphan(self):
        try:
            # see if we have a new version of pylinac that can create direct from the dataset
            streams = DicomImageStack(self.imager.datasets)
        except TypeError:
            # if not fall back to stream
            streams = datasets_to_stream(self.imager.datasets)
        param_list = {}
        if self.ui.cbCatPhan.currentText() == 'QuartDVT':
            cat = QuartDVT(streams)
        elif self.ui.cbCatPhan.currentText() == 'ACR CT':
            cat = ACRCT(streams)
        elif self.ui.cbCatPhan.currentText() == 'ACR MRI':
            cat = ACRMRILarge(streams)
        else:
            cat = getattr(ct, self.ui.cbCatPhan.currentText())(streams)
            param_list = {"hu_tolerance": int(self.settings.value('3D Phantom/HU Tolerance')),
                          "thickness_tolerance": float(self.settings.value('3D Phantom/Thickness Tolerance')),
                          "scaling_tolerance": float(self.settings.value('3D Phantom/Scaling Tolerance'))}
        if self.imager.invflag:
            for im in cat.dicom_stack.images:
                im.invert()
        cat.analyze(**param_list)
        filename = osp.join(self.working_dir, '3D Analysis.pdf')
        self.show_results(cat, filename)

    @show_wait_cursor
    def analyse_picket_fence(self):
        stream = dataset_to_stream(self.imager.datasets[self.imager.index])
        if self.settings.value('Picket Fence/Apply median filter', False, type=bool):
            pf = picketfence.PicketFence(stream, mlc=self.ui.cbMLC.currentText(), filter=3)
        else:
            pf = picketfence.PicketFence(stream, mlc=self.ui.cbMLC.currentText())
        try:
            pf.analyze(tolerance=float(self.settings.value('Picket Fence/Leaf Tolerance')),
                       action_tolerance=float(self.settings.value('Picket Fence/Leaf Action')),
                       num_pickets=int(self.settings.value('Picket Fence/Number of pickets')),
                       invert=self.imager.invflag)
        except ValueError:
            # if it throws an exception fall back to this as per issue #470
            pf.analyze(tolerance=float(self.settings.value('Picket Fence/Leaf Tolerance')),
                       action_tolerance=float(self.settings.value('Picket Fence/Leaf Action')),
                       num_pickets=int(self.settings.value('Picket Fence/Number of pickets')),
                       invert=self.imager.invflag,
                       required_prominence=0.1)
            self.status_warn('Could not analyze picket fence as is. Trying fallback method.')
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        self.show_results(pf, filename)

    @show_wait_cursor
    def analyse_winston_lutz(self):
        streams = datasets_to_stream(self.imager.datasets)
        wl = winston_lutz.WinstonLutz(streams)
        if self.imager.invflag:
            for im in wl.images:
                im.invert()
        wl.analyze(bb_size_mm=float(self.settings.value('Winston-Lutz/BB Size')),
                   open_field=self.settings.value('Winston-Lutz/Open field', False, type=bool),
                   low_density_bb=self.settings.value('Winston-Lutz/Low density BB', False, type=bool))
        filename = osp.join(self.working_dir, 'W-L Analysis.pdf')
        self.show_results(wl, filename)

    @show_wait_cursor
    def analyse_2d_phantoms(self):
        stream = dataset_to_stream(self.imager.datasets[self.imager.index])
        phan = getattr(planar_imaging, self.ui.cbPhan2D.currentText().replace(' ', ''))(stream)
        phan.analyze(low_contrast_threshold=float(self.settings.value('2D Phantom/Low contrast threshold')),
                     high_contrast_threshold=float(self.settings.value('2D Phantom/High contrast threshold')),
                     invert=self.imager.invflag,
                     angle_override=(None if self.settings.value('2D Phantom/Angle override') == '0'
                          else float(self.settings.value('2D Phantom/Angle override'))),
                     ssd=('auto' if self.settings.value('2D Phantom/SSD') == '1000'
                          else float(self.settings.value('2D Phantom/SSD'))))
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        self.show_results(phan, filename)

    @show_wait_cursor
    def analyse_vmat(self):
        stream = dataset_to_stream(self.imager.datasets[self.imager.index])
        ref_stream = dataset_to_stream(self.ref_imager.datasets[self.imager.index])
        images = (stream, ref_stream)
        if self.ui.cbVMAT.currentText() == 'DRGS':
            v = vmat.DRGS(image_paths=images)
        else:
            v = vmat.DRMLC(image_paths=images)
        v.analyze(tolerance=float(self.settings.value('VMAT/Tolerance')))
        v.open_image.base_path = self.filenames[0]
        v.dmlc_image.base_path = self.ref_filename
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        self.show_results(v, filename)

    @show_wait_cursor
    def analyse_star(self):
        filename, ext = osp.splitext(self.filenames[0])
        if len(self.filenames) == 1:
            if ext == '.zip':
                star = starshot.Starshot.from_zip(self.filenames[0],
                                                  sid=float(self.settings.value('Star shot/SID')),
                                                  dpi=float(self.settings.value('Star shot/DPI')))
            else:
                star = starshot.Starshot(self.filenames[0],
                                         sid=float(self.settings.value('Star shot/SID')),
                                         dpi=float(self.settings.value('Star shot/DPI')))
        else:
            star = starshot.Starshot.from_multiple_images(self.filenames,
                                                          sid=float(self.settings.value('Star shot/SID')),
                                                          dpi=float(self.settings.value('Star shot/DPI')))
        star.analyze(radius=float(self.settings.value('Star shot/Normalised analysis radius')),
                     tolerance=float(self.settings.value('Star shot/Tolerance')),
                     recursive=self.settings.value('Star shot/Recursive analysis', False, type=bool))
        filename = filename + '.pdf'
        self.show_results(star, filename)

    @show_wait_cursor
    def analyse_log(self):
        log = log_analyzer.load_log(self.filenames[0])
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        self.show_results(log, filename)

    @show_wait_cursor
    def analyse_gamma(self):
        if len(self.ref_filename) >> 0:
            stream = dataset_to_stream(self.imager.datasets[self.imager.index])
            ref_stream = dataset_to_stream(self.ref_imager.datasets[self.imager.index])
            eval_img = image.load(stream)
            if self.imager.invflag:
                eval_img.invert()
            ref_img = image.load(ref_stream)
            eval_img.normalize()
            ref_img.normalize()
            gamma = eval_img.gamma(comparison_image=ref_img,
                                   doseTA=self.settings.value('Gamma Analysis/Dose to agreement', 2.0, type=float),
                                   distTA=self.settings.value('Gamma Analysis/Distance to agreement', 2.0, type=float),
                                   threshold=self.settings.value('Gamma Analysis/Dose threshold', 0.05, type = float))
            gamma_plot = plt.imshow(gamma)
            gamma_plot.set_cmap('bwr')
            plt.title(f'Gamma Analysis ({self.settings.value("Gamma Analysis/Dose to agreement")}'
                      f'%/{self.settings.value("Gamma Analysis/Distance to agreement")}mm)')
            plt.ylabel('Distance (pixels)')
            plt.xlabel('Distance (pixels)')
            plt.colorbar()
            plt.clim(0, self.settings.value('Gamma Analysis/Gamma cap', 2.0, type=float))
#            plt.show()
            filename = osp.splitext(self.filenames[0])[0] + '.pdf'
            canvas = pdf.PylinacCanvas(filename,
                                       page_title='Gamma analysis',
                                       metadata=self.settings.value('General/Metadata'),
                                       logo=self.settings.value('General/Logo'))
            notes = self.ui.pte_notes.toPlainText() if self.ui.pte_notes.toPlainText() != '' else None,
            if notes is not None:
                canvas.add_text(text="Notes:", location=(1, 4.5), font_size=14)
                canvas.add_text(text=notes, location=(1, 4))
            img = io.BytesIO()
            plt.savefig(img)
            canvas.add_image(img, location=(1, 5), dimensions=(18, 18))
            canvas.finish()
            if open_path(filename):
                self.status_message('Results displayed in PDF')
            else:
                self.status_error('No reader to open document')
        else:
            self.ui.tabWidget.setTabVisible(3, False)

# ---------------------------------------------------------------------------------------------------------------------
# Reference image section
# ---------------------------------------------------------------------------------------------------------------------
    def open_ref(self):
        self.status_clear()
        self.ui.qlRef.clear()
        self.ui.tabWidget.setTabVisible(2, True)
        self.ui.tabWidget.setCurrentIndex(2)
        if len(self.ref_filename) == 0:
            if len(self.filenames) == 0:
                dirpath = osp.expanduser("~")
            else:
                dirpath = osp.realpath(self.filenames[0])
        else:
            dirpath = osp.realpath(self.ref_filename)
        ostype = system()
        if ostype == 'Windows':
            self.ref_filename = QFileDialog.getOpenFileName(self, 'Open DICOM file', dirpath,
                                                            'DICOM files (*.dcm);;All files (*.*)')[0]
        else:
            self.ref_filename = QFileDialog.getOpenFileName(self, 'Open DICOM file', dirpath,
                                                            'DICOM files (*.dcm);;All files (*)')[0]
        if self.ref_filename:
            if pydicom.misc.is_dicom(self.ref_filename):
                self.open_ref_image(self.ref_filename)
                # self.show_image(self.ref_imager.get_current_image(), self.ui.qlRef)
                # self.ui.qlRef.show()
                self.tab_changed(2)
            else:
                self.status_error('Not a DICOM image file.')

    def open_ref_image(self, filename):
        # Clear non-dicom files
        datasets = []
        try:
            ds = pydicom.dcmread(filename, force=True)
            if 'TransferSyntaxUID' not in ds.file_meta:
                ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            datasets.append(ds)
            self.ref_imager = Imager(datasets)
        except pydicom.errors.InvalidDicomError:
            self.status_error('Error reading DICOM image file.')

# ---------------------------------------------------------------------------------------------------------------------
# Image processing and editing
# ---------------------------------------------------------------------------------------------------------------------
    def invert(self):
        if self.imager.invflag:
            self.imager.invflag = False
        else:
            self.imager.invflag = True
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)

    def auto_window(self):
        if self.imager is not None and hasattr(self.imager, "values"):
            self.imager.auto_window()
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)
            self.status_message(f"Window center {self.imager.window_center}, Window width {self.imager.window_width}")

    def edit_pixel_data(self):
        if self.imager:
            if self.ui.action_Pixel_Data.isChecked():
                self.ui.tabWidget.setTabVisible(3, True)
                self.ui.tabWidget.setCurrentIndex(3)
                ds = self.imager.datasets[self.imager.index]
                self.table_model = TableModel(ds.pixel_array)
                self.ui.qtvPixelData.setModel(self.table_model)
                self.is_changed = True
            else:
                self.ui.tabWidget.setTabVisible(3, False)

    def sum_image(self):
        num_images = self.imager.size[2]
        try:
            self.imager.avg_images(avg=False)
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)
            self.status_message(f'{num_images} images were summed')
        except OverflowError as e:
            self.status_error('Image sum is resulting in integer overflow')

    def avg_image(self):
        num_images = self.imager.size[2]
        self.imager.avg_images()
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.status_message(f'{num_images} images were averaged')

    def scale_image(self):
        num_images = self.imager.size[2]
        self.imager.scale_images(self.ui.dsbScaleFactor.value())
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.status_message(f'{num_images} images were scaled')

# ---------------------------------------------------------------------------------------------------------------------
# Nuclear medicine analysis
# ---------------------------------------------------------------------------------------------------------------------

    @show_wait_cursor
    def max_count_rate(self):
        mcr = MyMaxCountRate(self.filenames[0])
        mcr.analyze()
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        self.show_results(mcr, filename)

    @show_wait_cursor
    def planar_uniformity(self):
        pu = MyPlanarUniformity(self.filenames[0])
        pu.analyze()
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        self.show_results(pu, filename)


# ---------------------------------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------------------------------


def main():
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setApplicationName("LinaQA")
    app.setOrganizationName("YenzakahleMPI")
    platform = QGuiApplication.platformName()
    if "wayland" in platform:
        QGuiApplication.setDesktopFileName("LinaQA")
    else:
        app.setWindowIcon(QIcon(":/icons/icons/LinacToolKit.png"))
    window = LinaQA()
    window.show()
    if len(sys.argv) > 1:
        window.filenames = sys.argv[1:]
        if window.filenames:
            window.open_file()
    else:
        window.working_dir = osp.expanduser("~")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
