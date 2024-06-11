# Copyright (C) 2013 Riverbank Computing Limited.
# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

"""PySide6 port of the widgets/tools/settingseditor example from Qt v5.x
   Back ported to PyQt5 and adapted by AC Chamberlain"""

import sys

from PyQt5.QtCore import (QByteArray, QDate, QDateTime, QDir, QEvent, QPoint,
     QRect, QRegularExpression, QSettings, QSize, QTime, QTimer, Qt, pyqtSlot as Slot)
from PyQt5.QtGui import (QColor, QIcon, QIntValidator, QDoubleValidator, QRegularExpressionValidator, QValidator)
from PyQt5.QtWidgets import (QAbstractItemView, QCheckBox, QDialog, QDialogButtonBox, QGridLayout,
     QHeaderView, QItemDelegate, QLineEdit, QStyle, QSpinBox, QStyleOptionViewItem,
     QTableWidgetItem, QTreeWidget, QTreeWidgetItem)


def set_default_settings(settings):
    settings.beginGroup('General')
    if not settings.contains('Logo'):
        settings.setValue('Logo', '')
    settings.endGroup()

    settings.beginGroup('3D Phantom')
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
        settings.setValue('Apply median filter', 'false')
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

    settings.beginGroup('Window')
    if not settings.contains('Position'):
        settings.setValue('Position', QPoint(100, 200))
    if not settings.contains('Size'):
        settings.setValue('Size', QSize(678, 682))
    settings.endGroup()


class TypeChecker:
    def __init__(self, parent=None):
        self.bool_exp = QRegularExpression('^(true)|(false)$')
        assert self.bool_exp.isValid()
        self.bool_exp.setPatternOptions(QRegularExpression.CaseInsensitiveOption)

        self.byteArray_exp = QRegularExpression(r'^[\x00-\xff]*$')
        assert self.byteArray_exp.isValid()

        self.char_exp = QRegularExpression('^.$')
        assert self.char_exp.isValid()

        pattern = r'^[+-]?\d+$'
        self.int_exp = QRegularExpression(pattern)
        assert self.int_exp.isValid()

        pattern = r'^\(([0-9]*),([0-9]*),([0-9]*),([0-9]*)\)$'
        self.color_exp = QRegularExpression(pattern)
        assert self.color_exp.isValid()

        pattern = r'^\((-?[0-9]*),(-?[0-9]*)\)$'
        self.point_exp = QRegularExpression(pattern)
        assert self.point_exp.isValid()

        pattern = r'^\((-?[0-9]*),(-?[0-9]*),(-?[0-9]*),(-?[0-9]*)\)$'
        self.rect_exp = QRegularExpression(pattern)
        assert self.rect_exp.isValid()

        self.size_exp = QRegularExpression(self.point_exp)

        date_pattern = '([0-9]{,4})-([0-9]{,2})-([0-9]{,2})'
        self.date_exp = QRegularExpression(f'^{date_pattern}$')
        assert self.date_exp.isValid()

        time_pattern = '([0-9]{,2}):([0-9]{,2}):([0-9]{,2})'
        self.time_exp = QRegularExpression(f'^{time_pattern}$')
        assert self.time_exp.isValid()

        pattern = f'^{date_pattern}T{time_pattern}$'
        self.dateTime_exp = QRegularExpression(pattern)
        assert self.dateTime_exp.isValid()

    def type_from_text(self, text):
        if self.bool_exp.match(text).hasMatch():
            return bool
        if self.int_exp.match(text).hasMatch():
            return int
        return None

    def create_validator(self, value, parent):
        if isinstance(value, bool):
            return QRegularExpressionValidator(self.bool_exp, parent)
        if isinstance(value, float):
            return QDoubleValidator(parent)
        if isinstance(value, int):
            return QIntValidator(parent)
        if isinstance(value, QByteArray):
            return QRegularExpressionValidator(self.byteArray_exp, parent)
        if isinstance(value, QColor):
            return QRegularExpressionValidator(self.color_exp, parent)
        if isinstance(value, QDate):
            return QRegularExpressionValidator(self.date_exp, parent)
        if isinstance(value, QDateTime):
            return QRegularExpressionValidator(self.dateTime_exp, parent)
        if isinstance(value, QTime):
            return QRegularExpressionValidator(self.time_exp, parent)
        if isinstance(value, QPoint):
            return QRegularExpressionValidator(self.point_exp, parent)
        if isinstance(value, QRect):
            return QRegularExpressionValidator(self.rect_exp, parent)
        if isinstance(value, QSize):
            return QRegularExpressionValidator(self.size_exp, parent)
        return None

    def from_string(self, text, original_value):
        if isinstance(original_value, QColor):
            match = self.color_exp.match(text)
            return QColor(min(int(match.captured(1)), 255),
                          min(int(match.captured(2)), 255),
                          min(int(match.captured(3)), 255),
                          min(int(match.captured(4)), 255))
        if isinstance(original_value, QDate):
            value = QDate.fromString(text, Qt.ISODate)
            return value if value.isValid() else None
        if isinstance(original_value, QDateTime):
            value = QDateTime.fromString(text, Qt.ISODate)
            return value if value.isValid() else None
        if isinstance(original_value, QTime):
            value = QTime.fromString(text, Qt.ISODate)
            return value if value.isValid() else None
        if isinstance(original_value, QPoint):
            match = self.point_exp.match(text)
            return QPoint(int(match.captured(1)),
                          int(match.captured(2)))
        if isinstance(original_value, QRect):
            match = self.rect_exp.match(text)
            return QRect(int(match.captured(1)),
                         int(match.captured(2)),
                         int(match.captured(3)),
                         int(match.captured(4)))
        if isinstance(original_value, QSize):
            match = self.size_exp.match(text)
            return QSize(int(match.captured(1)),
                         int(match.captured(2)))
        if isinstance(original_value, list):
            return text.split(',')
        return type(original_value)(text)


class Settings(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gridLayout = QGridLayout()
        self.setLayout(self.gridLayout)
        self.gridLayout.setObjectName("gridLayout")
        self.settings_tree = SettingsTree()
        self.gridLayout.addWidget(self.settings_tree, 0, 0, 1, 1)
        self.setWindowTitle("Settings Editor")
        self.resize(500, 600)
        settings = QSettings()
        self.set_settings_object(settings)

    def set_settings_object(self, settings):
        settings.setFallbacksEnabled(True)
        self.settings_tree.set_settings_object(settings)
        nice_name = QDir.fromNativeSeparators(settings.fileName())
        nice_name = nice_name.split('/')[-1]
        if not settings.isWritable():
            nice_name += " (read only)"
        self.setWindowTitle(f"{nice_name} - Settings Editor")

    def format(self):
        if self.format_combo.currentIndex() == 0:
            return QSettings.NativeFormat
        else:
            return QSettings.IniFormat

    def scope(self):
        if self.scope_cCombo.currentIndex() == 0:
            return QSettings.UserScope
        else:
            return QSettings.SystemScope

    def organization(self):
        return self.organization_combo.currentText()

    def application(self):
        if self.application_combo.currentText() == "Any":
            return ''

        return self.application_combo.currentText()

    def update_locations(self):
        self.locations_table.setUpdatesEnabled(False)
        self.locations_table.setRowCount(0)

        for i in range(2):
            if i == 0:
                if self.scope() == QSettings.SystemScope:
                    continue

                actual_scope = QSettings.UserScope
            else:
                actual_scope = QSettings.SystemScope

            for j in range(2):
                if j == 0:
                    if not self.application():
                        continue

                    actual_application = self.application()
                else:
                    actual_application = ''

                settings = QSettings(self.format(), actual_scope,
                                     self.organization(), actual_application)

                row = self.locations_table.rowCount()
                self.locations_table.setRowCount(row + 1)

                item0 = QTableWidgetItem()
                item0.setText(settings.fileName())

                item1 = QTableWidgetItem()
                disable = not (settings.childKeys() or settings.childGroups())

                if row == 0:
                    if settings.isWritable():
                        item1.setText("Read-write")
                        disable = False
                    else:
                        item1.setText("Read-only")
                    self.button_box.button(QDialogButtonBox.Ok).setDisabled(disable)
                else:
                    item1.setText("Read-only fallback")

                if disable:
                    item0.setFlags(item0.flags() & ~Qt.ItemIsEnabled)
                    item1.setFlags(item1.flags() & ~Qt.ItemIsEnabled)

                self.locations_table.setItem(row, 0, item0)
                self.locations_table.setItem(row, 1, item1)

        self.locations_table.setUpdatesEnabled(True)


class SettingsTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._type_checker = TypeChecker()
        self.setItemDelegate(VariantDelegate(self._type_checker, self))

        self.setHeaderLabels(("Setting", "Type", "Value"))
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(2, QHeaderView.Stretch)

        self.settings = None
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(2000)
        self.auto_refresh = False

        self.group_icon = QIcon()
        style = self.style()
        self.group_icon.addPixmap(style.standardPixmap(QStyle.SP_DirClosedIcon),
                                  QIcon.Normal, QIcon.Off)
        self.group_icon.addPixmap(style.standardPixmap(QStyle.SP_DirOpenIcon),
                                  QIcon.Normal, QIcon.On)
        self.key_icon = QIcon()
        self.key_icon.addPixmap(style.standardPixmap(QStyle.SP_FileIcon))

        self.refresh_timer.timeout.connect(self.maybe_refresh)

    def set_settings_object(self, settings):
        self.settings = settings
        self.clear()

        if self.settings is not None:
            self.settings.setParent(self)
            self.refresh()
            if self.auto_refresh:
                self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    def sizeHint(self):
        return QSize(800, 600)

    @Slot(bool)
    def set_auto_refresh(self, autoRefresh):
        self.auto_refresh = autoRefresh

        if self.settings is not None:
            if self.auto_refresh:
                self.maybe_refresh()
                self.refresh_timer.start()
            else:
                self.refresh_timer.stop()

    @Slot(bool)
    def set_fallbacks_enabled(self, enabled):
        if self.settings is not None:
            self.settings.setFallbacksEnabled(enabled)
            self.refresh()

    @Slot()
    def maybe_refresh(self):
        if self.state() != QAbstractItemView.EditingState:
            self.refresh()

    @Slot()
    def refresh(self):
        if self.settings is None:
            return

        # The signal might not be connected.
        try:
            self.itemChanged.disconnect(self.update_setting)
        except:
            pass

        self.settings.sync()
        self.update_child_items(None)

        self.itemChanged.connect(self.update_setting)

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            if self.isActiveWindow() and self.auto_refresh:
                self.maybe_refresh()

        return super(SettingsTree, self).event(event)

    def update_setting(self, item):
        key = item.text(0)
        ancestor = item.parent()

        while ancestor:
            key = ancestor.text(0) + '/' + key
            ancestor = ancestor.parent()

        d = item.data(2, Qt.UserRole)
        self.settings.setValue(key, item.data(2, Qt.UserRole))

        if self.auto_refresh:
            self.refresh()

    def update_child_items(self, parent):
        divider_index = 0

        for group in self.settings.childGroups():
            child_index = self.find_child(parent, group, divider_index)
            if child_index != -1:
                child = self.child_at(parent, child_index)
                child.setText(1, '')
                child.setText(2, '')
                child.setData(2, Qt.UserRole, None)
                self.move_item_forward(parent, child_index, divider_index)
            else:
                child = self.create_item(group, parent, divider_index)

            child.setIcon(0, self.group_icon)
            divider_index += 1

            self.settings.beginGroup(group)
            self.update_child_items(child)
            self.settings.endGroup()

        for key in self.settings.childKeys():
            child_index = self.find_child(parent, key, 0)
            if child_index == -1 or child_index >= divider_index:
                if child_index != -1:
                    child = self.child_at(parent, child_index)
                    for i in range(child.childCount()):
                        self.delete_item(child, i)
                    self.move_item_forward(parent, child_index, divider_index)
                else:
                    child = self.create_item(key, parent, divider_index)
                child.setIcon(0, self.key_icon)
                divider_index += 1
            else:
                child = self.child_at(parent, child_index)

            value = self.settings.value(key)
            if value is None:
                child.setText(1, 'Invalid')
            else:
                # Try to convert to type unless a QByteArray is received
                if isinstance(value, str):
                    value_type = self._type_checker.type_from_text(value)
                    if value_type:
                        value = self.settings.value(key, type=value_type)
                child.setText(1, value.__class__.__name__)
            child.setText(2, VariantDelegate.display_text(value))
            child.setData(2, Qt.UserRole, value)

        while divider_index < self.child_count(parent):
            self.delete_item(parent, divider_index)

    def create_item(self, text, parent, index):
        after = None

        if index != 0:
            after = self.child_at(parent, index - 1)

        if parent is not None:
            item = QTreeWidgetItem(parent, after)
        else:
            item = QTreeWidgetItem(self, after)

        item.setText(0, text)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        return item

    def delete_item(self, parent, index):
        if parent is not None:
            item = parent.takeChild(index)
        else:
            item = self.takeTopLevelItem(index)
        del item

    def child_at(self, parent, index):
        if parent is not None:
            return parent.child(index)
        else:
            return self.topLevelItem(index)

    def child_count(self, parent):
        if parent is not None:
            return parent.childCount()
        else:
            return self.topLevelItemCount()

    def find_child(self, parent, text, startIndex):
        for i in range(self.child_count(parent)):
            if self.child_at(parent, i).text(0) == text:
                return i
        return -1

    def move_item_forward(self, parent, oldIndex, newIndex):
        for int in range(oldIndex - newIndex):
            self.delete_item(parent, newIndex)


class VariantDelegate(QItemDelegate):
    def __init__(self, type_checker, parent=None):
        super().__init__(parent)
        self._type_checker = type_checker

    def paint(self, painter, option, index):
        if index.column() == 2:
            value = index.model().data(index, Qt.UserRole)
            if not self.is_supported_type(value):
                my_option = QStyleOptionViewItem(option)
                my_option.state &= ~QStyle.State_Enabled
                super(VariantDelegate, self).paint(painter, my_option, index)
                return

        super(VariantDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        if index.column() != 2:
            return None

        original_value = index.model().data(index, Qt.UserRole)
        if not self.is_supported_type(original_value):
            return None

        editor = None
        if isinstance(original_value, bool):
            editor = QCheckBox(parent)
        elif isinstance(original_value, int):
            editor = QSpinBox(parent)
            editor.setRange(-32767, 32767)
        else:
            editor = QLineEdit(parent)
            editor.setFrame(False)
            validator = self._type_checker.create_validator(original_value, editor)
            if validator:
                editor.setValidator(validator)
        return editor

    def setEditorData(self, editor, index):
        if not editor:
            return
        value = index.model().data(index, Qt.UserRole)
        if isinstance(editor, QCheckBox):
            editor.setCheckState(Qt.Checked if value else Qt.Unchecked)
        elif isinstance(editor, QSpinBox):
            editor.setValue(value)
        else:
            editor.setText(self.display_text(value))

    def value_from_lineedit(self, lineedit, model, index):
        if not lineedit.isModified():
            return None
        text = lineedit.text()
        validator = lineedit.validator()
        if validator is not None:
            state, text, _ = validator.validate(text, 0)
            if state != QValidator.Acceptable:
                return None
        original_value = index.model().data(index, Qt.UserRole)
        return self._type_checker.from_string(text, original_value)

    def setModelData(self, editor, model, index):
        value = None
        if isinstance(editor, QCheckBox):
            value = editor.checkState() == Qt.Checked
        elif isinstance(editor, QSpinBox):
            value = editor.value()
        else:
            value = self.value_from_lineedit(editor, model, index)
        if value is not None:
            model.setData(index, value, Qt.UserRole)
            model.setData(index, self.display_text(value), Qt.DisplayRole)

    @staticmethod
    def is_supported_type(value):
        return isinstance(value, (bool, float, int, QByteArray, str, QColor,
                                  QDate, QDateTime, QTime, QPoint, QRect,
                                  QSize, list))

    @staticmethod
    def display_text(value):
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            return '✓' if value else '☐'
        if isinstance(value, (int, float, QByteArray)):
            return str(value)
        if isinstance(value, QColor):
            (r, g, b, a) = (value.red(), value.green(), value.blue(), value.alpha())
            return f'({r},{g},{b},{a})'
        if isinstance(value, (QDate, QDateTime, QTime)):
            return value.toString(Qt.ISODate)
        if isinstance(value, QPoint):
            x = value.x()
            y = value.y()
            return f'({x},{y})'
        if isinstance(value, QRect):
            x = value.x()
            y = value.y()
            w = value.width()
            h = value.height()
            return f'({x},{y},{w},{h})'
        if isinstance(value, QSize):
            w = value.width()
            h = value.height()
            return f'({w},{h})'
        if isinstance(value, list):
            return ','.join(map(repr, value))
        if value is None:
            return '<Invalid>'

        return f'<{value}>'
