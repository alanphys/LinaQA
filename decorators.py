"""
=========================================================================
Decorators for various functions
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication


def show_wait_cursor(function):
    def new_function(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QApplication.processEvents()
        try:
            return function(self)
        except Exception as e:
            print("Error {}".format(e.args[0]))
            raise e
        finally:
            QApplication.restoreOverrideCursor()
            QApplication.processEvents()
    return new_function


def check_valid_image(function):
    # check if the imager has been created
    def _valid_image(self):
        if (self.imager is not None) and hasattr(self.imager, 'values') and (self.imager.values is not None):
            try:
                return function(self)
            except Exception as e:
                self.ui.statusbar.status_error(f'Could not analyze image(s). Reason: {repr(e)}')
        else:
            self.ui.statusbar.status_error('No image open. Please open an image!')
    return _valid_image


def check_values_exist(function):
    # check if image pixel values exist
    def _values_exist(*args, **kwargs):
        self = args[0]
        if hasattr(self, 'values') and self.values is not None:
            return function(*args, **kwargs)
    return _values_exist


def catch_nm_type_error(function):
    # display error if image is not nuclear medicine (NM or PET)
    def _catch_nm_error(*args, **kwargs):
        self = args[0]
        try:
            return function(*args, **kwargs)
        except TypeError:
            self.ui.statusbar.status_error('The file is not a nuclear medicine or PET image.')
    return _catch_nm_error
