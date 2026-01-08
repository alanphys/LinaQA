"""
============================================
Linear Accelerator Quality Assurance Toolkit
============================================

Frontend GUI to pylinac and pydicom with some added functionality.
Usage: python LinaQA.pyw

"""
# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

import sys
import inspect
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
    phantom3D_list,
    vmat_list,
    phantom2D_list,
    spatial_res_list,
    mlc_list,
    MyDoubleSpinBox)
from aboutpackage import About
from aboutpackage.aboutform import version
from settingsunit import Settings, set_default_settings
from imageunit import Imager
from decorators import show_wait_cursor, check_valid_image, catch_nm_type_error
from misc_utils import (
    open_path,
    get_dot_attr,
    set_dot_attr,
    del_dot_attr,
    text_to_tag,
    dataset_to_stream,
    datasets_to_stream)
from qt_subclasses import PopupToolbar, LongPressToolButton
from popups import (
    create_3dphantom_popup,
    create_mlc_popup,
    create_vmat_popup,
    create_2dphantom_popup,
    create_scale_popup,
    create_spatialres_popup,
    create_tomouniformity_popup,
    create_simplesens_popup)
import pylinac_subclasses
from tablemodel import TableModel

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

        # create popups for tool buttons
        create_3dphantom_popup(self)
        create_mlc_popup(self)
        create_vmat_popup(self)
        create_2dphantom_popup(self)
        create_scale_popup(self)
        create_spatialres_popup(self)
        create_tomouniformity_popup(self)
        create_simplesens_popup(self)

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
        self.ui.action_LinaQAH.triggered.connect(self.linaqa_help)
        self.ui.action_PyDicomH.triggered.connect(self.pydicom_help)
        self.ui.action_PylinacH.triggered.connect(self.pylinac_help)
        action_close.triggered.connect(self.close)
        self.ui.action_Settings.triggered.connect(self.show_settings)
        # RX toolbar
        self.ui.action_CatPhan.triggered.connect(self.analyse_catphan)
        self.ui.action_Picket_Fence.triggered.connect(self.analyse_picket_fence)
        self.ui.action_Winston_Lutz.triggered.connect(self.analyse_winston_lutz)
        self.ui.action_2DPhantoms.triggered.connect(self.analyse_2d_phantoms)
        self.ui.action_Starshot.triggered.connect(self.analyse_star)
        self.ui.action_VMAT.triggered.connect(self.analyse_vmat)
        self.ui.action_Machine_Logs.triggered.connect(self.analyse_log)
        # DX toolbar
        self.ui.action_Invert.triggered.connect(self.invert)
        self.ui.action_Scale_LUT.triggered.connect(self.scale_lut)
        self.ui.action_Auto_Window.triggered.connect(self.auto_window)
        self.ui.action_Pixel_Data.triggered.connect(self.edit_pixel_data)
        self.ui.action_Scale_Image.triggered.connect(self.scale_image)
        self.ui.action_Gamma.triggered.connect(self.analyse_gamma)
        self.ui.action_Sum_Image.triggered.connect(self.sum_image)
        self.ui.action_Ave_Image.triggered.connect(self.avg_image)
        self.ui.action_Flip_UD.triggered.connect(self.flip_up_down)
        self.ui.action_Flip_LR.triggered.connect(self.flip_left_right)
        # NM toolbar
        self.ui.action_MCR.triggered.connect(self.max_count_rate)
        self.ui.action_Simple_Sens.triggered.connect(self.simple_sensitivity)
        self.ui.action_Spatial_Res.triggered.connect(self.spatial_resolution)
        self.ui.action_Uniformity.triggered.connect(self.planar_uniformity)
        self.ui.action_Tomo_Uni.triggered.connect(self.tomographic_uniformity)
        self.ui.action_Tomo_Res.triggered.connect(self.tomographic_resolution)
        self.ui.action_Tomo_Contrast.triggered.connect(self.tomographic_contrast)
        self.ui.action_COR.triggered.connect(self.centre_of_rotation)
        # DICOM toolbar
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
        self.ui.action_Rx_Toolbar.setChecked(self.settings.value('Window/Show Rx Toolbar', True, type=bool))
        self.show_rx_toolbar()
        self.ui.action_DICOM_tags.setChecked(self.settings.value('Window/Show DCM Toolbar', False, type=bool))
        self.show_dicom_toolbar()
        self.ui.action_Dx_Toolbar.setChecked(self.settings.value('Window/Show Dx Toolbar', False, type=bool))
        self.show_dx_toolbar()
        self.ui.action_NM_Toolbar.setChecked(self.settings.value('Window/Show NM Toolbar', False, type=bool))
        self.show_nm_toolbar()
        self.ui.statusbar.status_good('LinaQA initialised correctly. Open DICOM file or drag and drop')

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
        frames = 0
        sorted_method = 'None'

        # Clear non-dicom files
        datasets = []
        # we have to treat the first file separately to get the image modality
        try:
            ds = pydicom.dcmread(filenames[0], force=force_read)
            if 'TransferSyntaxUID' not in ds.file_meta:
                ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            if 'SpacingBetweenSlices' not in ds:
                ds.SpacingBetweenSlices = ds.SliceThickness if 'SliceThickness' in ds else 1
            if 'Modality' in ds:
                first_modality = ds.Modality
            frames = ds.NumberOfFrames if 'NumberOfFrames' in ds else 1
            if ds.file_meta.TransferSyntaxUID.is_compressed:
                ds.decompress()
            datasets.append(ds)
        except pydicom.errors.InvalidDicomError:
            num_bad += 1
            filenames.remove(filenames[0])
        num_ok = 1

        # continue reading if first image is a single frame image
        if frames <= 1 < num_total:
            for file in filenames[1:]:
                try:
                    ds = pydicom.dcmread(file, force=force_read)
                    if 'TransferSyntaxUID' not in ds.file_meta:
                        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                    if 'SpacingBetweenSlices' not in ds:
                        ds.SpacingBetweenSlices = ds.SliceThickness if hasattr(ds, 'SliceThickness') else 1
                    modality = ds.Modality
                    frames = ds.NumberOfFrames if 'NumberOfFrames' in ds else 1
                    # cannot mix modalities or multi frame images
                    if (modality != first_modality) or (frames > 1) or not hasattr(ds, 'PixelData'):
                        raise pydicom.errors.InvalidDicomError
                    if ds.file_meta.TransferSyntaxUID.is_compressed:
                        ds.decompress()
                    datasets.append(ds)
                    num_ok += 1

                except pydicom.errors.InvalidDicomError:
                    filenames.remove(file)

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
        self.imager = Imager(datasets, self.settings.value('PyDicom/Use rescale', False, type=bool))
        self.filenames = filenames
        num_bad = num_total - num_ok
        if num_bad == 0:
            self.ui.statusbar.status_message(f"Opened {num_ok} DICOM file(s) sorted on {sorted_method}. Rejected {num_bad} bad files.")
        else:
            self.ui.statusbar.status_warn(f"Opened {num_ok} DICOM file(s) sorted on {sorted_method}. Rejected {num_bad} bad files.")

    def open_file(self):
        # remove any previous images
        del self.imager
        self.imager = None
        self.ui.qlImage.clear()
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
                self.edit_pixel_data()
            else:
                self.ui.tabWidget.setTabVisible(0, False)
                self.ui.action_DICOM_tags.setChecked(True)
                self.tab_changed(1)
        else:
            the_image = QPixmap(self.filenames[0])
            if the_image.isNull():
                self.ui.statusbar.status_error("File is not a valid image file!")
            else:
                self.ui.qlImage.setPixmap(the_image)
                self.ui.qlImage.setScaledContents(True)

    def choose_file(self):
        # set up ui
        self.is_changed = False
        self.ui.statusbar.status_clear()

        # get filename(s)
        if len(self.filenames) > 0:
            dirpath = osp.dirname(osp.realpath(self.filenames[0]))
        else:
            dirpath = self.working_dir
        ostype = system()
        if ostype == 'Windows':
            file_filter = ('DICOM files (*.dcm *.2 *.img *.ima);;'
                           'ZIP files (*.zip);;'
                           'Machine log files (*.bin *.txt);;'
                           'All files (*.*)')
        else:
            file_filter = ('DICOM files (*.dcm *.2 *.img *.ima);;'
                           'ZIP files (*.zip);;'
                           'Machine log files (*.bin *.txt);;'
                           'All files (*)')
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
            self.ui.statusbar.status_message('File saved')

    def save_file_as(self):
        self.ui.statusbar.status_clear()
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
            self.ui.statusbar.status_message('File save as ' + filename)

    def save_all(self):
        self.ui.statusbar.status_clear()
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
            self.ui.statusbar.status_message(f'{i} images saved in ' + dirpath)

    @staticmethod
    def show_image(numpy_array, label: QLabel):
        if numpy_array is not None:
            # create a QImage from Numpy array and display it in a label
            qpimage = QImage(numpy_array, numpy_array.shape[1], numpy_array.shape[0], QImage.Format_ARGB32)
            label.setPixmap(QPixmap.fromImage(qpimage).
                            scaled(label.width(),
                            label.height(),
                            Qt.KeepAspectRatio))

    @staticmethod
    def show_about():
        about = About()
        about.exec()

    @staticmethod
    def linaqa_help():
        rel_path = 'html/index.html'
        abs_path = osp.abspath(rel_path)
        webbrowser.open(f'file://{abs_path}')

    @staticmethod
    def pydicom_help():
        webbrowser.open('https://pydicom.github.io/pydicom/stable/')

    @staticmethod
    def pylinac_help():
        webbrowser.open('https://pylinac.readthedocs.io/en/latest/')

    @staticmethod
    def show_settings():
        settings = Settings()
        settings.exec()

    def show_rx_toolbar(self):
        self.ui.toolBar_Rx.setVisible(self.ui.action_Rx_Toolbar.isChecked())

    def show_dx_toolbar(self):
        self.ui.toolBar_Dx.setVisible(self.ui.action_Dx_Toolbar.isChecked())

    def show_nm_toolbar(self):
        self.ui.toolBar_NM.setVisible(self.ui.action_NM_Toolbar.isChecked())

    def wheelEvent(self, event):
        tab_index = self.ui.tabWidget.currentIndex()
        mouse_pos = event.globalPosition().toPoint()
        if ((tab_index == 0) and self.ui.qlImage.rect().contains(mouse_pos) and
           self.imager is not None and hasattr(self.imager, "values")):
            self.imager.index += int(event.angleDelta().y()/120)
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)
            self.ui.statusbar.status_message(f"Current slice {self.imager.index}")
            event.accept()
        elif tab_index == 2:
            super().wheelEvent(event)
        elif ((tab_index == 2) and self.ui.qlRef.rect().contains(mouse_pos) and
              self.ref_imager is not None and hasattr(self.ref_imager, "values")):
            self.ref_imager.index += int(event.angleDelta().y()/120)
            self.show_image(self.ref_imager.get_current_image(), self.ui.qlRef)
            self.ui.statusbar.status_message(f"Current slice {self.ref_imager.index}")
            event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mouse_last_pos = event.globalPos()
            self.mouse_button_down = True
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mouse_last_pos = None
            self.mouse_button_down = False
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mouse_button_down:
            tab_index = self.ui.tabWidget.currentIndex()
            mouse_pos = event.globalPos()
            if ((tab_index == 0) and self.ui.qlImage.rect().contains(mouse_pos) and
               self.imager is not None and hasattr(self.imager, "values")):
                delta = (mouse_pos - self.mouse_last_pos) * (self.imager.window_width/1000)
                self.mouse_last_pos = mouse_pos
                self.imager.window_width += delta.x()
                self.imager.window_center += delta.y()
                self.show_image(self.imager.get_current_image(), self.ui.qlImage)
                self.ui.statusbar.status_message(f"Window center {self.imager.window_center}, Window width {self.imager.window_width}")
                event.accept()
            if ((tab_index == 2) and self.ui.qlRef.rect().contains(mouse_pos) and
               self.ref_imager is not None and hasattr(self.ref_imager, "values")):
                delta = (mouse_pos - self.mouse_last_pos) * (self.ref_imager.window_width/1000)
                self.mouse_last_pos = mouse_pos
                self.ref_imager.window_width += delta.x()
                self.ref_imager.window_center += delta.y()
                self.show_image(self.ref_imager.get_current_image(), self.ui.qlRef)
                self.ui.statusbar.status_message(f"Window center {self.ref_imager.window_center}, Window width {self.ref_imager.window_width}")
                event.accept()

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
        if index != 1:
            self.ui.action_DICOM_tags.setChecked(False)
            self.show_dicom_toolbar()
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
            elif (index == 3) and (self.imager is not None):
                self.edit_pixel_data()
        self.old_tab = index

    def show_notes(self):
        if self.ui.action_Notes.isChecked():
            self.ui.tabWidget.setTabVisible(4, True)
            self.ui.tabWidget.setCurrentIndex(4)
        else:
            self.ui.tabWidget.setTabVisible(4, False)

    def show_results(self, test, filename=''):
        if filename == '':
            if len(self.filenames) == 1:
                filename = osp.splitext(self.filenames[0])[0] + '.pdf'
            elif len(self.filenames) > 1:
                filename = test._model + ' Analysis.pdf' if hasattr(test, '_model') else '3D Analysis.pdf'
                filename = osp.join(self.working_dir, filename)
        if osp.exists(filename):
            QApplication.restoreOverrideCursor()
            filename = QFileDialog.getSaveFileName(self, "File exists, save file as:", filename, "PDF files (*.pdf)")[0]
        if len(filename) > 0:
            notes = self.ui.pte_notes.toPlainText().split('\n') if self.ui.pte_notes.toPlainText() != '' else None
            test.publish_pdf(filename,
                             notes=notes,
                             metadata=self.settings.value('General/Metadata'),
                             logo=self.settings.value('General/Logo'))
            if open_path(filename):
                self.ui.statusbar.status_message('Results displayed in PDF')
            else:
                self.ui.statusbar.status_error('No reader to open document')
        else:
            self.ui.statusbar.status_warn("Results not saved.")

    def on_cbcatphan_changed(self, index_value: str):
        cb_text = self.ui.cbCatPhan.currentText()
        self.ui.action_CatPhan.setToolTip(f"Analyse {cb_text} Phantom. Long or right click to change phantom.")
        if cb_text.find("ACR") >= 0:
            self.ui.action_CatPhan.setIcon(QIcon(":/Icons/Icons/ACRPhantoms.png"))
        elif cb_text.find("Quart") >= 0:
            self.ui.action_CatPhan.setIcon(QIcon(":/Icons/Icons/Quart.png"))
        else:
            self.ui.action_CatPhan.setIcon(QIcon(":/Icons/Icons/Catphan.png"))

    def on_cbmlc_changed(self, index_value: str):
        cb_text = self.ui.cbMLC.currentText()
        self.ui.action_Picket_Fence.setToolTip(f"Analyse {cb_text} MLC. Long or right click to change MLC.")

    def on_cbvmat_changed(self, index_value: str):
        cb_text = self.ui.cbVMAT.currentText()
        self.ui.action_VMAT.setToolTip(f"Analyse {cb_text} test. Long or right click to change test.")

    def on_2dphantom_changed(self, index_value: str):
        cb_text = self.ui.cbPhan2D.currentText()
        self.ui.action_2DPhantoms.setToolTip(f"Analyse {cb_text} Phantom. Long or right click to change phantom.")

    def on_spatialres_changed(self, index_value: str):
        cb_text = self.ui.cbSpatialRes.currentText()
        self.ui.action_Spatial_Res.setToolTip(f"Analyse {cb_text} test. Long or right click to change test.")

# ---------------------------------------------------------------------------------------------------------------------
# Show DICOM tag section
# ---------------------------------------------------------------------------------------------------------------------
    def show_dicom_toolbar(self):
        self.ui.toolBar_DCM.setVisible(self.ui.action_DICOM_tags.isChecked())
        # create new tab
        if self.ui.action_DICOM_tags.isChecked():
            self.ui.tabWidget.setTabVisible(1, True)
            self.ui.tabWidget.setCurrentIndex(1)
            if self.imager:
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
            # enable the tag operations on the edit menu
            self.ui.action_Find_tag.setVisible(True)
            self.ui.action_Insert_tag.setVisible(True)
            self.ui.action_Edit_tag.setVisible(True)
            self.ui.action_Delete_tag.setVisible(True)
            # self.ui.action_Find_tag.setChecked(False)
            self.find_tag()
            self.filter_tag()
            self.show_tree()
        else:
            self.ui.tabWidget.setTabVisible(1, False)
            self.ui.action_Find_tag.setVisible(False)
            self.ui.action_Insert_tag.setVisible(False)
            self.ui.action_Edit_tag.setVisible(False)
            self.ui.action_Delete_tag.setVisible(False)

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
            item = QStandardItem(str(data_element))
            parent.appendRow(item)

    def recurse_tree(self, ds, parent):
        # order the dicom tags
        # write data elements
        pydicom.config.convert_wrong_length_to_UN = True
        for data_element in ds:
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
        indexes = self.ui.treeView.selectedIndexes()

        # Sort indexes by row to maintain order
        def get_hierarchical_path(index):
            path = []
            current = index
            while current.isValid():
                path.append(current.row())
                current = current.parent()
            return path[::-1]  # Reverse to get root-to-leaf order

        sorted_indexes = sorted(indexes, key=get_hierarchical_path)
        for index in sorted_indexes:
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
        self.ui.statusbar.status_warn('Inserting a DICOM tag may corrupt the file!')

        # get path for tag insertion
        proxy_index = self.ui.treeView.currentIndex()
        source_index = self.proxy_model.mapToSource(proxy_index)
        tag_parent = source_index
        tag_group, _, _, _, _ = text_to_tag(tag_parent.data(Qt.DisplayRole))
        if tag_group != '':                 # tag is leaf and we must select parent
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
                self.ui.statusbar.status_message('Inserted ' + tag_path + ' (' + tag_group + ', ' + tag_element + ') '
                                    + tag_keyword + ' ' + tag_vr + ':' + tag_value)
            except AttributeError:
                self.ui.statusbar.status_error('Could not insert ' + tag_path + '.')

            except TypeError:
                self.ui.statusbar.status_error('You may not insert a tag as a sequence.')

    def edit_tag(self):
        # get current tag
        self.ui.statusbar.status_warn('Editing a DICOM tag may corrupt the file!')
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
                    self.ui.statusbar.status_message('Changed ' + tag_path + ' to ' + tag_text)
                except AttributeError:
                    self.ui.statusbar.status_error('Could not change ' + tag_path)
        else:
            self.ui.statusbar.status_warn('No tag selected!')

    @show_wait_cursor
    def del_tag(self):
        self.ui.statusbar.status_warn('Editing a DICOM tag may corrupt the file!')
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
                self.ui.statusbar.status_message('Deleted ' + tag_path)
            except AttributeError:
                self.ui.statusbar.status_error('Could not delete ' + tag_path)
        else:
            self.ui.statusbar.status_warn('No tag selected!')

# ---------------------------------------------------------------------------------------------------------------------
# Radiotherapy analysis
# ---------------------------------------------------------------------------------------------------------------------
    @check_valid_image
    @show_wait_cursor
    def analyse_catphan(self):
        try:
            # see if we have a new version of pylinac that can create direct from the dataset
            streams = DicomImageStack(self.imager.datasets)
        except TypeError:
            # if not fall back to stream
            streams = datasets_to_stream(self.imager.datasets)
        param_list = {}
        try:
            if self.ui.cbCatPhan.currentText() == 'QuartDVT':
                cat = QuartDVT(streams)
            elif self.ui.cbCatPhan.currentText() == 'ACR CT':
                cat = ACRCT(streams)
            elif self.ui.cbCatPhan.currentText() == 'ACR MRI':
                cat = ACRMRILarge(streams)
            else:
                cat = getattr(ct, self.ui.cbCatPhan.currentText())(streams)
                param_list = {"hu_tolerance": int(self.settings.value('3D Phantoms/HU Tolerance')),
                              "thickness_tolerance": float(self.settings.value('3D Phantoms/Thickness Tolerance')),
                              "scaling_tolerance": float(self.settings.value('3D Phantoms/Scaling Tolerance'))}
            if self.imager.invflag:
                for im in cat.dicom_stack.images:
                    im.invert()
            cat.analyze(**param_list)
            self.show_results(cat)
        except Exception as e:
            self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')

    @check_valid_image
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
            self.show_results(pf)
        except ValueError:
            # if it throws an exception fall back to this as per issue #470
            try:
                self.ui.statusbar.status_warn('Could not analyze picket fence as is. Trying fallback method.')
                pf.analyze(tolerance=float(self.settings.value('Picket Fence/Leaf Tolerance')),
                           action_tolerance=float(self.settings.value('Picket Fence/Leaf Action')),
                           num_pickets=int(self.settings.value('Picket Fence/Number of pickets')),
                           invert=self.imager.invflag,
                           required_prominence=0.1)
                self.show_results(pf)
            except Exception as e:
                self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')

    @check_valid_image
    @show_wait_cursor
    def analyse_winston_lutz(self):
        streams = datasets_to_stream(self.imager.datasets)
        wl = winston_lutz.WinstonLutz(streams)
        if self.imager.invflag:
            for im in wl.images:
                im.invert()
        try:
            wl.analyze(bb_size_mm=float(self.settings.value('Winston-Lutz/BB Size')),
                       open_field=self.settings.value('Winston-Lutz/Open field', False, type=bool),
                       low_density_bb=self.settings.value('Winston-Lutz/Low density BB', False, type=bool))
            self.show_results(wl)
        except Exception as e:
            self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')

    @check_valid_image
    @show_wait_cursor
    def analyse_2d_phantoms(self):
        stream = dataset_to_stream(self.imager.datasets[self.imager.index])
        phantom_class = [obj for name, obj in inspect.getmembers(planar_imaging)
                         if hasattr(obj, 'common_name') and obj.common_name == self.ui.cbPhan2D.currentText()]
        phan = phantom_class[0](stream)
        try:
            phan.analyze(low_contrast_threshold=float(self.settings.value('2D Phantoms/Low contrast threshold')),
                         high_contrast_threshold=float(self.settings.value('2D Phantoms/High contrast threshold')),
                         invert=self.imager.invflag,
                         angle_override=(None if self.settings.value('2D Phantoms/Angle override') == '0'
                              else float(self.settings.value('2D Phantoms/Angle override'))),
                         center_override=(None if self.settings.value('2D Phantoms/Center override') == '0'
                              else float(self.settings.value('2D Phantoms/Center override'))),
                         size_override=(None if self.settings.value('2D Phantoms/Size override') == '0'
                              else float(self.settings.value('2D Phantoms/Size override'))),
                         ssd=('auto' if self.settings.value('2D Phantoms/SSD') == '1000'
                              else float(self.settings.value('2D Phantoms/SSD'))))
            self.show_results(phan)
        except Exception as e:
            self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')

    @check_valid_image
    @show_wait_cursor
    def analyse_vmat(self):
        stream = dataset_to_stream(self.imager.datasets[self.imager.index])
        try:
            ref_stream = dataset_to_stream(self.ref_imager.datasets[self.imager.index])
            images = (stream, ref_stream)
            if self.ui.cbVMAT.currentText() == 'DRGS':
                v = vmat.DRGS(image_paths=images)
            else:
                v = vmat.DRMLC(image_paths=images)
            v.analyze(tolerance=float(self.settings.value('VMAT/Tolerance')))
            v.open_image.base_path = self.filenames[0]
            v.dmlc_image.base_path = self.ref_filename
            self.show_results(v)
        except AttributeError:
            self.ui.statusbar.status_error('No reference image defined. Please open a reference image.')
        except Exception as e:
            self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')

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
        try:
            star.analyze(radius=float(self.settings.value('Star shot/Normalised analysis radius')),
                         tolerance=float(self.settings.value('Star shot/Tolerance')),
                         recursive=self.settings.value('Star shot/Recursive analysis', False, type=bool),
                         invert=self.imager.invflag if self.imager is not None else None)
            filename = filename + '.pdf'
            self.show_results(star, filename)
        except Exception as e:
            self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')

    @show_wait_cursor
    def analyse_log(self):
        try:
            log = log_analyzer.load_log(self.filenames[0])
            self.show_results(log)
        except Exception as e:
            self.ui.statusbar.status_error(f'Could not analyze log. Reason: {repr(e)}')

    @check_valid_image
    @show_wait_cursor
    def analyse_gamma(self):
        if len(self.ref_filename) >> 0:
            stream = dataset_to_stream(self.imager.datasets[self.imager.index])
            try:
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
                                       threshold=self.settings.value('Gamma Analysis/Dose threshold', 0.05, type=float))
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
                    self.ui.statusbar.status_message('Results displayed in PDF')
                else:
                    self.ui.statusbar.status_error('No reader to open document')
            except Exception as e:
                self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')
        else:
            self.ui.tabWidget.setTabVisible(3, False)
            self.ui.statusbar.status_error('No reference image defined. Please open a reference image.')

# ---------------------------------------------------------------------------------------------------------------------
# Reference image section
# ---------------------------------------------------------------------------------------------------------------------
    def open_ref(self):
        self.ui.statusbar.status_clear()
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
                self.ui.statusbar.status_error('Not a DICOM image file.')

    def open_ref_image(self, filename):
        # Assumes only one file to be loaded
        # Clear non-dicom files
        datasets = []
        try:
            ds = pydicom.dcmread(filename, force=True)
            if 'TransferSyntaxUID' not in ds.file_meta:
                ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
            datasets.append(ds)
            self.ref_imager = Imager(datasets, self.settings.value('PyDicom/Use rescale', False, type=bool))
        except pydicom.errors.InvalidDicomError:
            self.ui.statusbar.status_error('Error reading DICOM image file.')

# ---------------------------------------------------------------------------------------------------------------------
# Image processing and editing
# ---------------------------------------------------------------------------------------------------------------------
    @check_valid_image
    def invert(self):
        if self.imager.invflag:
            self.imager.invflag = False
        else:
            self.imager.invflag = True
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)

    @check_valid_image
    def scale_lut(self):
        if self.imager.rescale:
            self.imager.rescale = False
        else:
            self.imager.rescale = True
        self.auto_window()

    @check_valid_image
    def flip_left_right(self):
        self.imager.flip_lr()
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.ui.statusbar.status_message(f"Image(s) have been flipped left-right")

    @check_valid_image
    def flip_up_down(self):
        self.imager.flip_ud()
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.ui.statusbar.status_message(f"Image(s) have been flipped up-down")

    @check_valid_image
    def auto_window(self):
        self.imager.auto_window()
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.ui.statusbar.status_message(f"Window center {self.imager.window_center:.1f}, Window width {self.imager.window_width:.1f}")

    @check_valid_image
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

    @check_valid_image
    def sum_image(self):
        # We can't simply sum the images as it can give an integer overflow.
        # We must sum and rescale.
        num_images = self.imager.size[2]
        self.imager.sum_images()
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.is_changed = True
        self.ui.statusbar.status_message(f'{num_images} images were summed. Image has been rescaled.')

    @check_valid_image
    def avg_image(self):
        num_images = self.imager.size[2]
        self.imager.avg_images()
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.is_changed = True
        self.ui.statusbar.status_message(f'{num_images} images were averaged')

    @check_valid_image
    def scale_image(self):
        num_images = self.imager.size[2]
        self.imager.scale_images(self.ui.dsbScaleFactor.value())
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.is_changed = True
        self.ui.statusbar.status_message(f'{num_images} images were scaled')

# ---------------------------------------------------------------------------------------------------------------------
# Nuclear medicine analysis
# ---------------------------------------------------------------------------------------------------------------------

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def max_count_rate(self):
        mcr = pylinac_subclasses.LinaQAMaxCountRate(self.imager.datasets)
        mcr.analyze()
        self.show_results(mcr)

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def simple_sensitivity(self):
        phantom_image = self.imager.datasets[self.imager.index]
        background_image = self.ref_imager.datasets[0] if self.ref_imager is not None else None
        ss = pylinac_subclasses.LinaQASimpleSensitivity(phantom_image, background_image)
        ss.analyze(
            activity_mbq=float(self.ui.dsbSimpleSensActivity.value()),
            nuclide=getattr(pylinac_subclasses.Nuclide,
                            self.settings.value('Simple Sensitivity/Nuclide', 'Tc99m', type=str)))
        self.show_results(ss)

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def planar_uniformity(self):
        pu = pylinac_subclasses.LinaQAPlanarUniformity(self.imager.datasets)
        pu.analyze()
        self.show_results(pu)

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def spatial_resolution(self):
        # four bar test
        if self.ui.cbSpatialRes.currentText() == spatial_res_list[0]:
            sr = pylinac_subclasses.LinaQAFourBarRes(self.imager.datasets)
            sr.analyze(
                separation_mm=self.settings.value('Spatial Resolution/Separation mm', 100, type=float),
                roi_width_mm=self.settings.value('Spatial Resolution/ROI width mm', 10, type=float))
        # quadrant test
        elif self.ui.cbSpatialRes.currentText() == spatial_res_list[1]:
            sr = pylinac_subclasses.LinaQAQuadrantRes(self.imager.datasets)
            widths_str = self.settings.value('Spatial Resolution/Bar widths mm', '(4.23, 3.18, 2.54, 2.12)', type=str)
            widths = tuple(float(w.strip()) for w in widths_str.strip('()').split(','))
            sr.analyze(
                bar_widths=widths,
                roi_diameter_mm=self.settings.value('Spatial Resolution/ROI diameter mm', 70.0, type=float),
                distance_from_center_mm=self.settings.value('Spatial Resolution/Distance from center mm',
                                                            130.0,
                                                            type=float))
        self.show_results(sr)

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def tomographic_uniformity(self):
        tu = pylinac_subclasses.LinaQATomoUniformity(self.imager.datasets)
        tu.analyze(
            first_frame=int(self.ui.sbFirstFrame.value()),
            last_frame=int(self.ui.sbLastFrame.value()),
            ufov_ratio=self.settings.value('Tomographic Uniformity/UFOV ratio', 0.80, type=float),
            cfov_ratio=self.settings.value('Tomographic Uniformity/CFOV ratio', 0.75, type=float),
            center_ratio=self.settings.value('Tomographic Uniformity/Center ratio', 0.4, type=float),
            threshold=self.settings.value('Tomographic Uniformity/Threshold', 0.75, type=float),
            window_size=self.settings.value('Tomographic Uniformity/Window size', 5, type=int))
        self.show_results(tu)

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def tomographic_resolution(self):
        tr = pylinac_subclasses.LinaQATomoResolution(self.imager.datasets)
        tr.analyze()
        self.show_results(tr)

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def tomographic_contrast(self):
        tc = pylinac_subclasses.LinaQATomoContrast(self.imager.datasets)
        sphere_diam_str = self.settings.value('Tomographic Contrast/Sphere diameters mm',
                                              '(38, 31.8, 25.4, 19.1, 15.9, 12.7)',
                                              type=str)
        sphere_diam = tuple(float(s.strip()) for s in sphere_diam_str.strip('()').split(','))
        sphere_ang_str = self.settings.value('Tomographic Contrast/Sphere angles',
                                             '(-10, -70, -130, -190, 110, 50)',
                                             type=str)
        sphere_ang = tuple(float(s.strip()) for s in sphere_ang_str.strip('()').split(','))
        tc.analyze(
            sphere_diameters_mm=sphere_diam,
            sphere_angles=sphere_ang,
            ufov_ratio=self.settings.value('Tomographic Contrast/UFOV ratio', 0.8, type=float))
        self.show_results(tc)

    @check_valid_image
    @catch_nm_type_error
    @show_wait_cursor
    def centre_of_rotation(self):
        cor = pylinac_subclasses.LinaQACenterOfRotation(self.imager.datasets)
        cor.analyze()
        self.show_results(cor)


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
