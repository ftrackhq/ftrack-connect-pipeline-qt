# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtCore, QtGui, QtWidgets
from ftrack_connect_pipeline import constants


class LogTableModel(QtCore.QAbstractTableModel):

    DATA_ROLE = QtCore.Qt.UserRole + 1

    @property
    def log_items(self):
        return self._data

    def __init__(self, parent):
        '''Initialize model model with *items*.'''

        super(LogTableModel, self).__init__(parent)

        self._headers = [
            'status', 'execution_time', 'plugin_name', 'plugin_type'
        ]

        self._data = []

    def set_log_items(self, log_items):
        '''
        Reset the model and sets the ftrack_asset_list with the given
        *ftrack_asset_list*
        '''
        self.beginResetModel()
        self._data = log_items
        self.endResetModel()


    def rowCount(self, parent):
        '''Return the row count for the internal data.'''
        if parent.column() > 0:
            return 0

        return len(self.log_items)

    def columnCount(self, parent):
        '''Return the column count for the internal data.'''
        return len(self._headers)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        '''Return the data provided in the given *index* and with *role*'''

        row = index.row()
        column = index.column()

        if not index.isValid():
            return None

        item = self.log_items[row]
        column_name = self._headers[column]

        # style versions
        if role == QtCore.Qt.TextColorRole:
            if constants.status_bool_mapping[item.status]:
                return QtGui.QBrush(QtGui.QColor(155, 250, 218, 200))
            elif item.status == 'RUNNING_STATUS':
                return
            else:
                return QtGui.QBrush(QtGui.QColor(250, 171, 155, 200))

        elif role == QtCore.Qt.TextAlignmentRole and column == 0:
            return QtCore.Qt.AlignCenter

        # style the rest
        elif role == QtCore.Qt.DisplayRole:
            return getattr(item, column_name)

        elif role == self.DATA_ROLE:
            return item

        return None

    def headerData(self, col, orientation, role):
        '''Provide header data'''
        if (
            orientation == QtCore.Qt.Horizontal and
            role == QtCore.Qt.DisplayRole
        ):
            return self._headers[col].capitalize()
        return None


class FilterProxyModel(QtCore.QSortFilterProxyModel):

    DATA_ROLE = LogTableModel.DATA_ROLE

    def __init__(self, parent=None):
        '''Initialize the FilterProxyModel'''
        super(FilterProxyModel, self).__init__(parent=parent)

        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setFilterKeyColumn(-1)

    def filterAcceptsRowItself(self, source_row, source_parent):
        '''Provide a way to filter internal values.'''
        return super(FilterProxyModel, self).filterAcceptsRow(
            source_row, source_parent
        )

    def filterAcceptsRow(self, source_row, source_parent):
        '''Override filterAcceptRow to filter to any entry.'''
        if self.filterAcceptsRowItself(source_row, source_parent):
            return True

        parent = source_parent
        while parent.isValid():
            if self.filterAcceptsRowItself(parent.row(), parent.parent()):
                return True
            parent = parent.parent()

        return False

    def lessThan(self, left, right):
        '''Allow to sort the model.'''
        left_data = self.sourceModel().item(left)
        right_data = self.sourceModel().item(right)
        return left_data.id > right_data.id