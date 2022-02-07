# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import functools
import platform

import qtawesome as qta

from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.prompt import PromptDialog


class AssetManagerBaseWidget(QtWidgets.QWidget):
    '''Base widget of the asset manager and assembler'''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def init_header_content(self, layout):
        '''To be overridden by child'''
        layout.addStretch()

    @property
    def engine_type(self):
        '''Returns engine_type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Sets the engine_type with the given *value*'''
        self._engine_type = value

    def __init__(self, assembler, event_manager, parent=None):
        '''Initialise AssetManagerWidget with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(AssetManagerBaseWidget, self).__init__(parent=parent)

        self._assembler = assembler
        self._event_manager = event_manager
        self._engine_type = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        '''Build widgets and parent them.'''

        self._header = QtWidgets.QWidget()
        self._header.setLayout(QtWidgets.QHBoxLayout())
        self.init_header_content(self._header.layout())
        self.layout().addWidget(self._header)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout().addWidget(self.scroll, 100)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        pass

    def init_search(self):
        '''Create search box'''
        self._search = Search()
        self._search.input_updated.connect(self.on_search)
        return self._search

    def on_search(self, text):
        '''Search in the current model.'''
        pass


class AssetListModel(QtCore.QAbstractTableModel):
    '''Custom asset list model'''

    @property
    def event_manager(self):
        return self._event_manager

    @property
    def session(self):
        return self._event_manager.session

    def __init__(self, event_manager):
        super(AssetListModel, self).__init__()
        self._event_manager = event_manager
        self.__asset_entities_list = []

    def rowCount(self, index=QtCore.QModelIndex):
        return len(self.__asset_entities_list)

    def columnCount(self, index=QtCore.QModelIndex):
        return 1

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return self.__asset_entities_list[index.row()]

    def insertRows(self, position, data, index=QtCore.QModelIndex):
        rows = len(data)
        self.beginInsertRows(
            QtCore.QModelIndex(), position, position + rows - 1
        )
        for row in range(rows):
            if position + row < len(self.__asset_entities_list):
                self.__asset_entities_list.insert(position + row, data[row])
            else:
                self.__asset_entities_list.append(data[row])
        self.endInsertRows()

    def reset(self):
        self.beginResetModel()
        self.__asset_entities_list = []
        self.endResetModel()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return (
            QtCore.Qt.ItemFlags(QtCore.QAbstractTableModel.flags(self, index))
            | QtCore.Qt.ItemIsEditable
        )


class AssetListWidget(QtWidgets.QWidget):
    '''Generic asset list view'''

    _last_clicked = None
    selection_updated = QtCore.Signal(object)

    @property
    def model(self):
        return self._model

    @property
    def assets(self):
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and isinstance(widget, AccordionBaseWidget):
                yield widget

    def __init__(self, model, parent=None):
        super(AssetListWidget, self).__init__(parent=parent)
        self._model = model
        self.was_clicked = False

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(1, 1, 1, 1)
        self.layout().setSpacing(1)

    def build(self):
        pass

    def post_build(self):
        self._model.rowsInserted.connect(self.on_assets_added)
        self._model.modelReset.connect(self.rebuild)

    def on_assets_added(self, parent, first, last):
        self.rebuild()
        self.selection_updated.emit(self.selection())

    def rebuild(self):
        '''Clear widget and add all assets again from model.'''
        raise NotImplementedError()

    def reset(self):
        '''Remove all assets'''
        self.model.reset()
        self.rebuild()

    def selection(
        self, warn_on_empty=False, empty_returns_all=False, as_widgets=False
    ):
        result = []
        for widget in self.assets:
            if widget.selected:
                if as_widgets:
                    result.append(widget)
                else:
                    result.append(self.model.data(widget.index))
        if len(result) == 0:
            if empty_returns_all:
                dlg = PromptDialog(
                    'Assembler',
                    'Load all?',
                    self,
                )
                if dlg.exec_():
                    for widget in self.assets:
                        widget.set_selected(True)
                        if as_widgets:
                            result.append(widget)
                        else:
                            result.append(self.model.data(widget.index))
            elif warn_on_empty:
                QtWidgets.QMessageBox.critical(
                    None,
                    'Error!',
                    "Please select at least one asset!",
                    QtWidgets.QMessageBox.Abort,
                )
        return result

    def clear_selection(self):
        selection_modified = False
        for asset_widget in self.assets:
            if asset_widget.set_selected(False):
                selection_modified = True
        if selection_modified:
            self.selection_updated.emit(self.selection())

    def asset_clicked(self, asset_widget, event):
        '''An asset (accordion) were clicked in list, evaluate selection.'''
        selection_modified = False
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.button() == QtCore.Qt.RightButton:
            return
        if (
            modifiers == QtCore.Qt.Key_Meta and platform.system() != 'Darwin'
        ) or (
            modifiers == QtCore.Qt.ControlModifier
            and platform.system() == 'Darwin'
        ):
            # Add to selection
            pass
        elif modifiers == QtCore.Qt.ShiftModifier:
            # Select inbetweens
            if self._last_clicked:
                start_row = min(
                    self._last_clicked.index.row(), asset_widget.index.row()
                )
                end_row = max(
                    self._last_clicked.index.row(), asset_widget.index.row()
                )
                for widget in self.assets:
                    if start_row < widget.index.row() < end_row:
                        if widget.set_selected(True):
                            selection_modified = True
        else:
            self.clear_selection()
        if asset_widget.set_selected(True):
            selection_modified = True
        self._last_clicked = asset_widget
        if selection_modified:
            self.selection_updated.emit(self.selection())

    def mousePressEvent(self, event):
        # Consume this event, so parent client does not de-select all
        pass