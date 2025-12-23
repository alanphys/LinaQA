"""
=========================================================================
Extra functionality for PyQT classes.
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2025
# SPDX-License-Identifier: Licence.txt:

from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QAction,
                             QToolButton, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QLabel, QPushButton, QSpinBox,
                             QComboBox, QFrame)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal


class PopupToolbar(QFrame):
    """Custom popup widget that acts as a toolbar with controls"""

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(2)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)

    def add_hcontrol(self, label, widget):
        """Add a labeled control to the popup toolbar"""
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        row.addWidget(widget)
        self.main_layout.addLayout(row)

    def add_vcontrol(self, label, widget):
        """Add a labeled control to the popup toolbar"""
        col = QVBoxLayout()
        col.addWidget(QLabel(label))
        col.addWidget(widget)
        self.main_layout.addLayout(col)

    def add_widget(self, widget):
        """Add a widget directly to the popup toolbar"""
        self.main_layout.addWidget(widget)

    def add_toolbar(self, toolbar):
        """Add a QToolBar to the popup"""
        self.main_layout.addWidget(toolbar)

    def show_below(self, reference_widget):
        """Show the popup below the reference widget"""
        pos = reference_widget.mapToGlobal(reference_widget.rect().bottomLeft())
        self.move(pos)
        self.show()
        self.setFocus()

    def show_next_to(self, reference_widget):
        """Show the popup below the reference widget"""
        pos = reference_widget.mapToGlobal(reference_widget.rect().topRight())
        self.move(pos)
        self.show()
        self.setFocus()

    def focusOutEvent(self, event):
        """Close popup when focus is lost"""
        self.close()
        self.closed.emit()
        super().focusOutEvent(event)


class LongPressToolButton(QToolButton):
    """Custom QToolButton that detects long press and shows popup toolbar"""

    longPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.on_long_press)
        self.long_press_duration = 500  # milliseconds
        self.is_long_press = False
        self.popup_widget = None

    def set_popup_widget(self, widget):
        """Set the popup widget that will appear on long press"""
        self.popup_widget = widget

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_long_press = False
            self.long_press_timer.start(self.long_press_duration)
            event.accept()
        elif event.button() == Qt.RightButton:
            if self.popup_widget:
                self.popup_widget.show_next_to(self)
                event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.long_press_timer.stop()
            if not self.is_long_press:
                # Short click - trigger default action
                if self.defaultAction():
                    self.defaultAction().trigger()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def on_long_press(self):
        """Called when long press is detected"""
        self.is_long_press = True
        self.longPressed.emit()

        if self.popup_widget:
            self.popup_widget.show_next_to(self)
