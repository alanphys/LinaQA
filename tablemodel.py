from PyQt5.QtCore import QAbstractTableModel, Qt
# Adapted from https://www.pythonguis.com/tutorials/qtableview-modelviews-numpy-pandas/
# Author: Martin Fitzpatrick
# Adapted by AC Chamberlain


class TableModel(QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            # Note: self._data[index.row()][index.column()] will also work
            value = self._data[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return super().flags(index) | Qt.ItemIsEditable  # add editable flag.

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            # Set the value into the frame.
            self._data[index.row(), index.column()] = value if value != '' else 0
            return True
        return False
