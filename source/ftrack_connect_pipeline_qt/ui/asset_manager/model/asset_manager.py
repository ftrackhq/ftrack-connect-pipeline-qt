# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.constants import asset as asset_constants
from Qt import QtWidgets, QtCore, QtGui


class AssetManagerModel(QtCore.QAbstractTableModel):
    '''Model representing AssetManager.'''

    DATA_ROLE = QtCore.Qt.UserRole + 1

    @property
    def ftrack_asset_list(self):
        return self._ftrack_asset_list

    def __init__(self, parent=None):
        '''Initialise with *root* entity and optional *parent*.'''
        super(AssetManagerModel, self).__init__(parent=parent)
        self._ftrack_asset_list = []
        self.columns = asset_constants.KEYS

    def set_asset_list(self, ftrack_asset_list):
        '''
        Reset the model and sets the ftrack_asset_list with the given
        *ftrack_asset_list*
        '''
        self.beginResetModel()
        #self.clear()
        self._ftrack_asset_list = ftrack_asset_list
        self.endResetModel()

    def rowCount(self, parent=QtCore.QModelIndex()):
        '''Return number of children *parent* index has.

        *parent* QModelIndex
        '''
        if parent.column() > 0:
            return 0

        return len(self.ftrack_asset_list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        '''Return amount of data *parent* index has.'''
        return len(self.columns)

    def removeRows(self, position, rows=1, index=QtCore.QModelIndex()):
        '''
        Removes the row in the given *position*
        '''
        self.beginRemoveRows(index, position, position + rows - 1)

        self._ftrack_asset_list.pop(position)

        self.endRemoveRows()
        return True

    def data(self, index, role=QtCore.Qt.DisplayRole):
        '''
        Returns the data from the given *index*
        '''
        row = index.row()
        column = index.column()

        if not index.isValid():
            return None

        item = self.ftrack_asset_list[row]
        data = item[self.columns[column]]

        # style versions
        if (
                role == QtCore.Qt.BackgroundRole and
                index.column() == self.get_version_column_index()
        ):
            if item.get(asset_constants.IS_LATEST_VERSION):#.is_latest:
                return QtGui.QBrush(QtGui.QColor(155, 250, 218, 200))
            else:
                return QtGui.QBrush(QtGui.QColor(250, 171, 155, 200))

        elif (
                role == QtCore.Qt.TextAlignmentRole and
                index.column() == self.get_version_column_index()
        ):
            return QtCore.Qt.AlignCenter

        elif (role == QtCore.Qt.TextColorRole and
              index.column() == self.get_version_column_index()
        ):
            return QtGui.QColor(0, 0, 0, 255)

        # style the rest
        elif role == QtCore.Qt.DisplayRole:
            return data

        elif role == QtCore.Qt.EditRole:
            return data

        elif role == self.DATA_ROLE:
            return item

        return None

    def headerData(self, column, orientation, role):
        if (
                orientation == QtCore.Qt.Horizontal and
                role == QtCore.Qt.DisplayRole
        ):
            return self.columns[column].replace('_', ' ').capitalize()

        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        '''
        Sets the givn *value* to the given *index*
        '''
        if role == QtCore.Qt.EditRole:
            if value:
                self.dataChanged.emit(index, index)
                return True
            return False
        else:
            return super(AssetManagerModel, self).setData(index, value, role)

    def flags(self, index):
        if index.column() == self.get_version_column_index():
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def get_version_column_index(self):
        '''Returns the column index of the version_number column'''
        return self.columns.index(asset_constants.VERSION_NUMBER)

    def set_host_connection(self, host_connection):
        '''Sets the host connection'''
        self.host_connection = host_connection


class FilterProxyModel(QtCore.QSortFilterProxyModel):

    DATA_ROLE = AssetManagerModel.DATA_ROLE

    @property
    def ftrack_asset_list(self):
        return self.sourceModel().ftrack_asset_list

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
        print left_data, right_data
        return left_data.id > right_data.id

