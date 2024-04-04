"""
============================================
Linear Accelerator Quality Assurance Toolkit
============================================

Frontend GUI to pylinac and pydicom with some added functionality.
Usage: python LinaQA.pyw

"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023, 2024

import sys
import os.path as osp
import os
import subprocess
from platform import system
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox, QComboBox, QLabel, QTreeView
from PyQt5.QtGui import QPixmap, QImage, QFont, QMouseEvent, QStandardItemModel, QStandardItem
from PyQt5.QtCore import pyqtSignal as SIGNAL, QObject, Qt, QSettings, QSortFilterProxyModel, QSize
import matplotlib.pyplot as plt

from LinaQAForm import Ui_LinaQAForm
from aboutpackage import About
from aboutpackage.aboutform import version
from settingsunit import Settings
from imageunit import Imager
from decorators import show_wait_cursor
from pydicom import compat
import pydicom
from pylinac import image, picketfence, ct, winston_lutz, planar_imaging, vmat, starshot, log_analyzer

catphan_list = ["CatPhan503", "CatPhan504", "CatPhan600", "CatPhan604"]
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


def open_path(path: str) -> None:
    """Open the specified path in the system default viewer."""

    if os.name == 'darwin':
        launcher = "open"
    elif os.name == 'posix':
        launcher = "xdg-open"
    elif os.name == 'nt':
        launcher = "explorer"
    subprocess.call([launcher, path])


class LinaQA(QMainWindow):

    def __init__(self, parent=None):
        super(LinaQA, self).__init__()
        self.imager = None
        self.ref_imager = None
        self.mouse_button_down = False
        self.changed = False
        self.mouse_last_pos = None
        self.filenames = []
        self.ref_filename = []
        self.source_model = None
        self.proxy_model = None
        self.ui = Ui_LinaQAForm()
        self.ui.setupUi(self)
        self.settings = QSettings()
        self.set_default_settings(self.settings)

        # we have to insert a Combox for the CatPhan manually into the toolbar
        self.ui.cbCatPhan = QComboBox()
        self.ui.cbCatPhan.setFixedWidth(120)
        self.ui.toolBar_Side.insertWidget(self.ui.action_Picket_Fence, self.ui.cbCatPhan)
        self.ui.cbCatPhan.addItems(catphan_list)
        self.ui.toolBar_Side.insertSeparator(self.ui.action_Picket_Fence)
        catphan_type = self.settings.value('CatPhan/Type')
        index = self.ui.cbCatPhan.findText(catphan_type)
        if index >= 0:
            self.ui.cbCatPhan.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in CatPhan/Type')

        # we have to insert a Combox for the MLC manually into the toolbar
        self.ui.cbMLC = QComboBox()
        self.ui.cbMLC.setFixedWidth(120)
        self.ui.toolBar_Side.insertWidget(self.ui.action_VMAT, self.ui.cbMLC)
        for mlc in picketfence.MLC:
            self.ui.cbMLC.insertItem(0, mlc.value.get("name"))
        self.ui.toolBar_Side.insertSeparator(self.ui.action_VMAT)
        mlc_type = self.settings.value('Picket Fence/MLC Type')
        index = self.ui.cbMLC.findText(mlc_type)
        if index >= 0:
            self.ui.cbMLC.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in Picket Fence/MLC Type')

        # we have to insert a Combox for the VMAT test manually into the toolbar
        self.ui.cbVMAT = QComboBox()
        self.ui.cbVMAT.setFixedWidth(120)
        self.ui.toolBar_Side.insertWidget(self.ui.action_2DPhantoms, self.ui.cbVMAT)
        self.ui.cbVMAT.addItems(vmat_list)
        self.ui.toolBar_Side.insertSeparator(self.ui.action_VMAT)
        vmat_type = self.settings.value('VMAT/Test type')
        index = self.ui.cbVMAT.findText(vmat_type)
        if index >= 0:
            self.ui.cbVMAT.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in VMAT/Test type')

        # we have to insert a Combox for the 2D phantoms test manually into the toolbar
        self.ui.cbPhan2D = QComboBox()
        self.ui.cbPhan2D.setFixedWidth(120)
        self.ui.toolBar_Side.insertWidget(self.ui.action_Machine_Logs, self.ui.cbPhan2D)
        self.ui.cbPhan2D.addItems(phantom2D_list)
        self.ui.toolBar_Side.insertSeparator(self.ui.action_Machine_Logs)
        phan2d_type = self.settings.value('2D Phantom/Type')
        index = self.ui.cbPhan2D.findText(phan2d_type)
        if index >= 0:
            self.ui.cbPhan2D.setCurrentIndex(index)
        else:
            raise Exception('Invalid setting in 2D Phantom/Type')

        self.ui.statusbar.showMessage('Open DICOM file or drag and drop')
        self.ui.action_Open.triggered.connect(self.openfile)
        self.ui.action_Open_Ref.triggered.connect(self.open_ref)
        self.ui.action_About.triggered.connect(self.showabout)
        self.ui.action_Settings.triggered.connect(self.showsettings)
        self.ui.action_Invert.triggered.connect(self.invert)
        self.ui.action_Auto_Window.triggered.connect(self.auto_window)
        self.ui.action_DICOM_tags.triggered.connect(self.show_dicom_tags)
        self.ui.action_CatPhan.triggered.connect(self.analyse_catphan)
        self.ui.action_Picket_Fence.triggered.connect(self.analyse_picket_fence)
        self.ui.action_Winston_Lutz.triggered.connect(self.analyse_winston_lutz)
        self.ui.action_2DPhantoms.triggered.connect(self.analyse_2d_phantoms)
        self.ui.action_Starshot.triggered.connect(self.analyse_star)
        self.ui.action_VMAT.triggered.connect(self.analyse_vmat)
        self.ui.action_Machine_Logs.triggered.connect(self.analyse_log)
        self.ui.action_Gamma.triggered.connect(self.analyse_gamma)
        self.ui.tabWidget.tabCloseRequested.connect(lambda index: self.ui.tabWidget.setTabVisible(index, False))
        self.setWindowTitle(f'LinaQA v{version}')
        self.ui.tabWidget.setTabVisible(1, False)
        self.ui.tabWidget.setTabVisible(2, False)

    def set_default_settings(self, settings):
        settings.beginGroup('CatPhan')
        if not settings.contains('Type'):
            settings.setValue('Type', 'CatPhan604')
        if not settings.contains('HU Tolerance'):
            settings.setValue('HU Tolerance', '40')
        if not settings.contains('Thickness Tolerance'):
            settings.setValue('Thickness Tolerance', '0.2')
        if not settings.contains('Scaling Tolerance'):
            settings.setValue('Scaling Tolerance', '1')
        settings.endGroup()

        settings.beginGroup('Picket Fence')
        if not settings.contains('MLC Type'):
            settings.setValue('MLC Type', 'HD Millennium')
        if not settings.contains('Leaf Tolerance'):
            settings.setValue('Leaf Tolerance', '0.5')
        if not settings.contains('Leaf Action'):
            settings.setValue('Leaf Action', '0.25')
        if not settings.contains('Number of pickets'):
            settings.setValue('Number of pickets', '10')
        if not settings.contains('Apply median filter'):
            settings.setValue('Apply median filter', 'False')
        settings.endGroup()

        settings.beginGroup('Star shot')
        if not settings.contains('DPI'):
            settings.setValue('DPI', '76')
        if not settings.contains('SID'):
            settings.setValue('SID', '1000')
        if not settings.contains('Normalised analysis radius'):
            settings.setValue('Normalised analysis radius', '0.85')
        if not settings.contains('Tolerance'):
            settings.setValue('Tolerance', '1')
        if not settings.contains('Recursive analysis'):
            settings.setValue('Recursive analysis', 'False')
        settings.endGroup()

        settings.beginGroup('VMAT')
        if not settings.contains('Test type'):
            settings.setValue('Test type', 'DRGS')
        if not settings.contains('Tolerance'):
            settings.setValue('Tolerance', '1.5')
        settings.endGroup()

        settings.beginGroup('2D Phantom')
        if not settings.contains('Type'):
            settings.setValue('Type', 'Leeds TOR')
        if not settings.contains('Low contrast threshold'):
            settings.setValue('Low contrast threshold', '0.1')
        if not settings.contains('High contrast threshold'):
            settings.setValue('High contrast threshold', '0.5')
        if not settings.contains('Force image inversion'):
            settings.setValue('Force image inversion', 'False')
        settings.endGroup()

        settings.beginGroup('Gamma Analysis')
        if not settings.contains('Dose to agreement'):
            settings.setValue('Dose to agreement', '2')
        if not settings.contains('Distance to agreement'):
            settings.setValue('Distance to agreement', '2')
        if not settings.contains('Gamma cap'):
            settings.setValue('Gamma cap', '2')
        if not settings.contains('Global dose'):
            settings.setValue('Global dose', 'True')
        if not settings.contains('Dose threshold'):
            settings.setValue('Dose threshold', '5')
        settings.endGroup()

    def closeEvent(self, event):
        if self.changed:
            reply = QMessageBox.question(self, 'Quit', 'Are you sure you want to quit?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    def open_image(self, filenames):
        num_total = len(filenames)
        num_bad = 0

        # Clear non-dicom files
        datasets = []
        for file in filenames:
            try:
                ds = pydicom.dcmread(file, force=True)
                if 'TransferSyntaxUID' not in ds.file_meta:
                    ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                datasets.append(ds)
            except pydicom.errors.InvalidDicomError:
                num_bad += 1
                filenames.remove(file)
        num_ok = num_total - num_bad

        # Try to sort based on instance number then SOPInstanceUID
        sorted_method = "filenames"
        try:
            datasets.sort(key=lambda x: x.InstanceNumber)
            sorted_method = "instance number"
        except TypeError:
            try:
                datasets.sort(key=lambda x: x.SOPInstanceUID)
                sorted_method = "SOP instance UID"
            except TypeError:
                pass

        self.imager = Imager(datasets)

        self.ui.statusbar.showMessage("Opened %d DICOM file(s) sorted on %s. Rejected %d bad files" %
                                      (num_ok, sorted_method, num_bad))

    def openfile(self):
        self.ui.qlImage.clear()
        self.ui.tabWidget.setTabVisible(0, True)
        self.ui.tabWidget.setCurrentIndex(0)
        if len(self.filenames) == 0:
            if len(sys.argv) > 1:
                self.filenames = [sys.argv[1]]
            else:
                self.filenames = [osp.expanduser("~")]
        dirpath = osp.dirname(osp.realpath(self.filenames[0]))
        ostype = system()
        if ostype == 'Windows':
            self.filenames = QFileDialog.getOpenFileNames(self, 'Open DICOM file', dirpath,
                                                                'DICOM files (*.dcm);;All files (*.*)')[0]
        else:
            self.filenames = QFileDialog.getOpenFileNames(self, 'Open DICOM file', dirpath,
                                                                'DICOM files (*.dcm);;All files (*)')[0]
        if pydicom.misc.is_dicom(self.filenames[0]):
            self.open_image(self.filenames)
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)
            self.ui.qlImage.show()
            self.show_dicom_tags()
        else:
            the_image = QPixmap(self.filenames[0])
            if the_image.isNull():
                self.ui.statusbar.showMessage("File is not an image file!")
            else:
                self.ui.qlImage.setPixmap(the_image)
                self.ui.qlImage.setScaledContents(True)


    def show_image(self, numpy_array, label: QLabel):
        if numpy_array is not None:
            # create a QImage from Numpy array and display it in a label
            qpimage = QImage(numpy_array, numpy_array.shape[1], numpy_array.shape[0], QImage.Format_ARGB32)
            label.setPixmap(QPixmap.fromImage(qpimage).
                            scaled(label.width(),
                            label.height(),
                            Qt.KeepAspectRatio))

    def showabout(self):
        about = About()
        about.exec()

    def showsettings(self):
        settings = Settings()
        settings.exec()

    def auto_window(self):
        self.imager.auto_window()
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.ui.statusbar.showMessage(
            "Window center %d, Window width %d" % (self.imager.window_center, self.imager.window_width))

    def wheelEvent(self, e):
        self.imager.index += int(e.angleDelta().y()/120)
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)
        self.ui.statusbar.showMessage("Current slice %d" % self.imager.index)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mouse_last_pos = event.globalPos()
            self.mouse_button_down = True

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.mouse_last_pos = None
            self.mouse_button_down = False

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mouse_button_down:
            delta = (event.globalPos() - self.mouse_last_pos) * (self.imager.window_width/1000)
            self.mouse_last_pos = event.globalPos()

            self.imager.window_width += delta.x()
            self.imager.window_center += delta.y()

            self.show_image(self.imager.get_current_image(), self.ui.qlImage)
            self.ui.statusbar.showMessage("Window center %d, Window width %d" %
                                          (self.imager.window_center, self.imager.window_width))

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            urls = event.mimeData().text().split("\n")
            filenames = []
            for url in urls:
                if url != "":
                    filename = url.split('/', 2)[2]
                    if filename != "":
                        filenames.append(filename)
            if filenames:
                self.open_image(filenames)

    def resizeEvent(self, event):
        if self.imager is not None:
            self.show_image(self.imager.get_current_image(), self.ui.qlImage)

    def invert(self):
        if self.imager.invflag:
            self.imager.invflag = False
        else:
            self.imager.invflag = True
        self.show_image(self.imager.get_current_image(), self.ui.qlImage)

# ---------------------------------------------------------------------------------------------------------------------
# Show DICOM tag section
# ---------------------------------------------------------------------------------------------------------------------
    def show_dicom_tags(self):
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
                self.ui.fsearchbar.setVisible(False)
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
        model_header.append(self.filenames[self.imager.index])
        self.source_model.setHorizontalHeaderLabels(model_header)
        parent_item = self.source_model.invisibleRootItem()
        self.write_header(self.source_model, self.imager.datasets[self.imager.index], parent_item)
        self.recurse_tree(self.source_model, self.imager.datasets[self.imager.index], parent_item)
        return

    def write_header(self, model, ds, parent):
        # write meta data
        fm = ds.file_meta
        for data_element in fm:
            if isinstance(data_element.value, compat.text_type):
                item = QStandardItem(compat.text_type(data_element))
            else:
                item = QStandardItem(str(data_element))
            parent.appendRow(item)

    def recurse_tree(self, model, ds, parent):
        # order the dicom tags
        # write data elements
        for data_element in ds:
            if isinstance(data_element.value, compat.text_type):
                item = QStandardItem(compat.text_type(data_element))
            else:
                item = QStandardItem(str(data_element))
            parent.appendRow(item)
            if data_element.VR == "SQ":   # a sequence
                for i, ds in enumerate(data_element.value):
                    sq_item_description = data_element.name.replace(" Sequence", "")  # XXX not i18n
                    item_text = "{0:s} {1:d}".format(sq_item_description, i + 1)
                    item = QStandardItem(item_text)
                    parent.appendRow(item)
                    self.recurse_tree(model, ds, item)

# ---------------------------------------------------------------------------------------------------------------------
# Analyse section
# ---------------------------------------------------------------------------------------------------------------------
    @show_wait_cursor
    def analyse_catphan(self):
        dirname = os.path.dirname(self.filenames[0])
        cat = getattr(ct, self.ui.cbCatPhan.currentText())(dirname)
        filename = osp.join(dirname, 'CBCT Analysis.pdf')
        cat.analyze(hu_tolerance=int(self.settings.value('CatPhan/HU Tolerance')),
                    thickness_tolerance=float(self.settings.value('CatPhan/Thickness Tolerance')),
                    scaling_tolerance=float(self.settings.value('CatPhan/Scaling Tolerance')))
        cat.publish_pdf(filename)
        open_path(filename)

    @show_wait_cursor
    def analyse_picket_fence(self):
        if self.settings.value('Picket Fence/Apply median filter') == 'True':
            pf = picketfence.PicketFence(self.filenames[0], mlc=self.ui.cbMLC.currentText(), filter=3)
        else:
            pf = picketfence.PicketFence(self.filenames[0], mlc=self.ui.cbMLC.currentText())
        pf.analyze(tolerance=float(self.settings.value('Picket Fence/Leaf Tolerance')),
                   action_tolerance=float(self.settings.value('Picket Fence/Leaf Action')),
                   num_pickets=int(self.settings.value('Picket Fence/Number of pickets')))
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        pf.publish_pdf(filename)
        open_path(filename)

    @show_wait_cursor
    def analyse_winston_lutz(self):
        dirname = os.path.dirname(self.filenames[0])
        wl = winston_lutz.WinstonLutz(dirname)
        wl.analyze()
        filename = osp.join(dirname, 'W-L Analysis.pdf')
        wl.publish_pdf(filename)
        open_path(filename)

    @show_wait_cursor
    def analyse_2d_phantoms(self):
        phan = getattr(planar_imaging, self.ui.cbPhan2D.currentText().replace(' ', ''))(self.filenames[0])
        phan.analyze(low_contrast_threshold=float(self.settings.value('2D Phantom/Low contrast threshold')),
                     high_contrast_threshold=float(self.settings.value('2D Phantom/High contrast threshold')),
                     invert=self.ui.action_Invert.isChecked())
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        phan.publish_pdf(filename)
        open_path(filename)

    @show_wait_cursor
    def analyse_vmat(self):
        images = (self.filenames[0], self.ref_filename[0])
        if self.ui.cbVMAT.currentText() == 'DRGS':
            v = vmat.DRGS(image_paths=images)
        else:
            v = vmat.DRMLC(image_paths=images)
        v.analyze(tolerance=float(self.settings.value('VMAT/Tolerance')))
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        v.publish_pdf(filename)
        open_path(filename)

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
                     recursive=self.settings.value('Star shot/Recursive analysis'))
        filename = filename + '.pdf'
        star.publish_pdf(filename)
        open_path(filename)

    @show_wait_cursor
    def analyse_log(self):
        log = log_analyzer.load_log(self.filenames[0])
        filename = osp.splitext(self.filenames[0])[0] + '.pdf'
        log.publish_pdf(filename)
        open_path(filename)

    @show_wait_cursor
    def analyse_gamma(self):
        if len(self.ref_filename) >> 0:
            eval_img = image.load(self.filenames[0])
            ref_img = image.load(self.ref_filename[0])
            eval_img.normalize()
            ref_img.normalize()
            gamma = image.gamma_2d(reference=ref_img.array,
                                   evaluation=eval_img.array,
                                   dose_to_agreement=float(self.settings.value('Gamma Analysis/Dose to agreement')),
                                   distance_to_agreement=int(self.settings.value('Gamma Analysis/Distance to agreement')),
                                   gamma_cap_value=float(self.settings.value('Gamma Analysis/Gamma cap')),
                                   global_dose=self.settings.value('Gamma Analysis/Global dose'),
                                   dose_threshold=float(self.settings.value('Gamma Analysis/Dose threshold')))
            gamma_plot = plt.imshow(gamma)
            gamma_plot.set_cmap('bwr')
            plt.title(f'Gamma Analysis ({self.settings.value("Gamma Analysis/Dose to agreement")}'
                      f'%/{self.settings.value("Gamma Analysis/Distance to agreement")}mm)')
            plt.ylabel('Distance (pixels)')
            plt.xlabel('Distance (pixels)')
            plt.colorbar()
            plt.show()
        else:
            self.ui.tabWidget.setTabVisible(3, False)

    # ---------------------------------------------------------------------------------------------------------------------
    # Reference image section
    # ---------------------------------------------------------------------------------------------------------------------
    def open_ref(self):
        self.ui.qlRef.clear()
        self.ui.tabWidget.setTabVisible(2, True)
        self.ui.tabWidget.setCurrentIndex(2)
        if len(self.ref_filename) == 0:
            if len(self.filenames) == 0:
                dirpath = osp.expanduser("~")
            else:
                dirpath = osp.realpath(self.filenames[0])
        else:
            dirpath = osp.realpath(self.ref_filename[0])
        ostype = system()
        if ostype == 'Windows':
            self.ref_filename = QFileDialog.getOpenFileNames(self, 'Open DICOM file', dirpath,
                                                             'DICOM files (*.dcm);;All files (*.*)')[0]
        else:
            self.ref_filename = QFileDialog.getOpenFileNames(self, 'Open DICOM file', dirpath,
                                                             'DICOM files (*.dcm);;All files (*)')[0]
        if self.ref_filename:
            self.open_ref_image(self.ref_filename)
            self.show_image(self.ref_imager.get_current_image(), self.ui.qlRef)
            self.ui.qlRef.show()

    def open_ref_image(self, filenames):
        num_total = len(filenames)
        num_bad = 0

        # Clear non-dicom files
        datasets = []
        for file in filenames:
            try:
                ds = pydicom.dcmread(file, force=True)
                if 'TransferSyntaxUID' not in ds.file_meta:
                    ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
                datasets.append(ds)
            except pydicom.errors.InvalidDicomError:
                num_bad += 1
                filenames.remove(file)
        num_ok = num_total - num_bad

        # Try to sort based on instance number then SOPInstanceUID
        sorted_method = "filenames"
        try:
            datasets.sort(key=lambda x: x.InstanceNumber)
            sorted_method = "instance number"
        except AttributeError:
            try:
                datasets.sort(key=lambda x: x.SOPInstanceUID)
                sorted_method = "SOP instance UID"
            except AttributeError:
                pass
        self.ref_imager = Imager(datasets)
        self.ui.statusbar.showMessage("Opened %d DICOM file(s) sorted on %s. Rejected %d bad files" %
                                      (num_ok, sorted_method, num_bad))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LinaQA")
    app.setOrganizationName("YenzakahleMPI")
    window = LinaQA()
    window.show()
    if len(sys.argv) > 1:
        filenames = sys.argv[1:]
        if filenames:
            window.open_image(filenames)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
