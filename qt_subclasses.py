"""
=========================================================================
Extra functionality for PyQT classes.
=========================================================================
"""

# author : AC Chamberlain <alanphys@yahoo.co.uk>
# copyright: AC Chamberlain (c) 2023-2026
# SPDX-License-Identifier: Licence.txt:

from PyQt5.QtWidgets import (QApplication, QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QStatusBar)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QPalette
from linaqa_types import faint_red, faint_green, faint_yellow


class ColorStatusBar(QStatusBar):
    """Status bar to display and retain colour coded error, warn and good messages"""
    def status_clear(self):
        # Clear the status bar
        qsb_color = self.palette().color(QPalette.Base).getRgb()
        mystylesheet = f"background-color: {qsb_color}; border-top: 1px outset grey;"
        self.setStyleSheet(mystylesheet)
        self.showMessage('')

    def status_message(self, status_message):
        # Clear the status bar
        qsb_color = self.palette().color(QPalette.Base).getRgb()
        mystylesheet = f"background-color: {qsb_color}; border-top: 1px outset grey;"
        self.setStyleSheet(mystylesheet)
        # self.setToolTip(self.toolTip() + '\n' + status_message)
        self.showMessage(status_message)

    def status_warn(self, status_message):
        mystylesheet = f"background-color: {faint_yellow}; border-top: 1px outset grey;"
        self.setStyleSheet(mystylesheet)
        self.setToolTip(self.toolTip() + '\n' + status_message)
        self.showMessage(status_message)

    def status_good(self, status_message):
        mystylesheet = f"background-color: {faint_green}; border-top: 1px outset grey;"
        self.setStyleSheet(mystylesheet)
        self.setToolTip(self.toolTip() + '\n' + status_message)
        self.showMessage(status_message)

    def status_error(self, status_message):
        mystylesheet = f"background-color: {faint_red}; border-top: 1px outset grey;"
        self.setStyleSheet(mystylesheet)
        self.setToolTip(self.toolTip() + '\n' + status_message)
        self.showMessage(status_message)


class PopupToolbar(QFrame):
    """Custom popup widget that acts as a toolbar with controls"""

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(2)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(6)

        # Track if we're currently showing
        self._is_showing = False

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
        self.activateWindow()
        self.raise_()

        # Install event filter when showing
        if not self._is_showing:
            QApplication.instance().installEventFilter(self)
            self._is_showing = True

    def show_next_to(self, reference_widget):
        """Show the popup below the reference widget"""
        pos = reference_widget.mapToGlobal(reference_widget.rect().topRight())
        self.move(pos)
        self.show()
        self.activateWindow()
        self.raise_()

        # Install event filter when showing
        if not self._is_showing:
            QApplication.instance().installEventFilter(self)
            self._is_showing = True

    def eventFilter(self, obj, event):
        """Filter events to detect clicks outside the popup"""
        if event.type() == QEvent.MouseButtonPress and self._is_showing:
            # Check if click is outside this widget and its children
            if self.isVisible():
                click_pos = event.globalPos()
                popup_rect = self.rect()
                popup_rect.moveTopLeft(self.mapToGlobal(self.rect().topLeft()))

                if not popup_rect.contains(click_pos):
                    # Check if the click is on a child widget (like a combobox dropdown)
                    clicked_widget = QApplication.widgetAt(click_pos)

                    # Check if clicked widget is related to our popup
                    if clicked_widget is not None:
                        # Check if it's a child of this popup
                        if self.isAncestorOf(clicked_widget):
                            return False

                        # Check if it's a popup window related to our widgets (like combobox dropdown)
                        for child in self.findChildren(QWidget):
                            # Check for combobox dropdowns and other popups
                            if hasattr(child, 'view') and callable(child.view):
                                # This is likely a combobox
                                try:
                                    view = child.view()
                                    if view and (clicked_widget == view or view.isAncestorOf(clicked_widget)):
                                        return False
                                except:
                                    pass

                    # Click was outside the popup and not on a related widget
                    self.close()
                    return False  # Allow the click to propagate
        return False

    def closeEvent(self, event):
        """Clean up event filter when closing"""
        if self._is_showing:
            QApplication.instance().removeEventFilter(self)
            self._is_showing = False
        self.closed.emit()
        super().closeEvent(event)

    def hideEvent(self, event):
        """Clean up when hidden"""
        if self._is_showing:
            QApplication.instance().removeEventFilter(self)
            self._is_showing = False
        super().hideEvent(event)


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
