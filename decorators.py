from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QApplication


def show_wait_cursor(function):
    def new_function(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            return function(self)
        except Exception as e:
            raise e
            print("Error {}".format(e.args[0]))
        finally:
            QApplication.restoreOverrideCursor()
    return new_function
