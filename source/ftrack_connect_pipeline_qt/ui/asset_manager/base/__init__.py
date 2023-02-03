# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import platform
from functools import partial
import shiboken2

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import scroll_area


class AssetManagerBaseWidget(QtWidgets.QWidget):
    '''Base widget of the asset manager'''

    refresh = QtCore.Signal()  # Refresh asset list from model
    rebuild = QtCore.Signal()  # Fetch assets from DCC and update model

    changeAssetVersion = QtCore.Signal(
        object, object
    )  # User has requested a change of asset version
    selectAssets = QtCore.Signal(object, object)  # Select assets in DCC
    removeAssets = QtCore.Signal(object, object)  # Remove assets from DCC
    updateAssets = QtCore.Signal(
        object, object
    )  # Update DCC assets to latest version
    loadAssets = QtCore.Signal(object, object)  # Load assets into DCC
    unloadAssets = QtCore.Signal(object, object)  # Unload assets from DCC

    stopBusyIndicator = QtCore.Signal()  # Stop spinner and hide it

    DEFAULT_ACTIONS = {
        'select': [{'ui_callback': 'ctx_select', 'name': 'select_asset'}],
        'remove': [{'ui_callback': 'ctx_remove', 'name': 'remove_asset'}],
        'load': [{'ui_callback': 'ctx_load', 'name': 'load_asset'}],
        'unload': [{'ui_callback': 'ctx_unload', 'name': 'unload_asset'}],
    }

    @property
    def client(self):
        '''Return asset list widget'''
        return self._client

    @property
    def snapshot_assets(self):
        '''Return True if should display separate list of snapshot assets.'''
        return self.client.snapshot_assets

    @property
    def is_assembler(self):
        '''Return asset list widget'''
        return self.client.is_assembler

    @property
    def asset_list(self):
        '''Return asset list widget'''
        return self._asset_list

    @property
    def asset_list_container(self):
        return self._asset_list_container

    @property
    def snapshot_asset_list_container(self):
        return self._snapshot_asset_list_container

    @property
    def host_connection(self):
        '''Return the host connection'''
        return self.client.host_connection

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self.client.event_manager

    @property
    def engine_type(self):
        '''Returns engine_type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Sets the engine_type with the given *value*'''
        self._engine_type = value

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def __init__(self, asset_manager_client, asset_list_model, parent=None):
        '''
        Initialize asset manager widget

        :param is_assembler: Boolean telling if this asset manager is docked in assembler (True) or in DCC (False)
        :param event_manager:  :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param asset_list_model: : instance of :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel`
        :param parent: the parent dialog or frame
        '''
        super(AssetManagerBaseWidget, self).__init__(parent=parent)

        self._client = asset_manager_client
        self._asset_list = None
        self._asset_list_model = asset_list_model
        self._engine_type = None
        self._asset_list_container = None
        self._snapshot_asset_list_container = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.scroll_area = scroll_area.ScrollArea()
        if self.client.snapshot_assets:
            self.snapshot_scroll_area = scroll_area.ScrollArea()

    def build_asset_list_container(self, scroll_widget, snapshot=False):
        '''Return the widget enclosing the asset list, can be overidden by child'''
        return AssetListContainerWidget(scroll_widget)

    def build_header(self, layout):
        '''Build the asset manager header and add to *layout*. To be overridden by child'''
        layout.addStretch()

    def build(self):
        '''Build widgets and parent them.'''
        self._header = QtWidgets.QWidget()
        self._header.setLayout(QtWidgets.QVBoxLayout())
        self._header.layout().setContentsMargins(1, 1, 1, 10)
        self._header.layout().setSpacing(4)
        self.build_header(self._header.layout())
        self.layout().addWidget(self._header)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )

        if not self.client.snapshot_assets:
            # A single list of ftrack assets
            self.layout().addWidget(self.asset_list_container, 100)
        else:
            # Create a scroll area for snapshot component list
            self.snapshot_scroll_area.setWidgetResizable(True)
            self.snapshot_scroll_area.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )

            # Put into a split view
            self._splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
            self._splitter.addWidget(self.asset_list_container)
            self._splitter.addWidget(self.snapshot_asset_list_container)
            self._splitter.setStretchFactor(0, 1)
            self._splitter.setStretchFactor(1, 1)
            self._splitter.setHandleWidth(1)

            self.layout().addWidget(self._splitter, 100)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        pass

    def init_search(self):
        '''Create search input'''
        self._search = Search(
            collapsed=self.is_assembler, collapsable=self.is_assembler
        )
        self._search.inputUpdated.connect(self.on_search)
        return self._search

    def on_search(self, text):
        '''Search in the current model, to be implemented by child.'''
        pass


class AssetListContainerWidget(QtWidgets.QWidget):
    '''Container widget for asset list widget, allows for DCC overrides with
    additional toolings'''

    def __init__(self, scroll_widget, parent=None):
        super(AssetListContainerWidget, self).__init__(parent=parent)
        self._scroll_widget = scroll_widget
        self._header_widget = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        if self._header_widget:
            self.layout().addWidget(self._header_widget)
        self.layout().addWidget(self._scroll_widget, 1000)

    def post_build(self):
        pass


class AssetListWidget(QtWidgets.QWidget):
    '''Generic asset list view widget'''

    _last_clicked = None  # The asset last clicked, used for SHIFT+ selections

    selectionUpdated = QtCore.Signal(
        object
    )  # Emitted when selection has been updated

    checkedUpdated = QtCore.Signal(
        object
    )  # Emitted when checked state has been updated

    refreshed = QtCore.Signal()  # Should be emitted when list has been rebuilt

    @property
    def model(self):
        return self._model

    @property
    def item_widget_class(self):
        return self._item_widget_class

    @property
    def assets(self):
        '''Return assets added to widget'''
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if widget and isinstance(widget, AccordionBaseWidget):
                yield widget

    @property
    def count(self):
        return self.model.rowCount()

    def __init__(self, model, item_widget_class, parent=None):
        '''
        Initialize asset list widget

        :param model: :class:`~ftrack_connect_pipeline_qt.ui.asset_manager.model.AssetListModel` instance
        :param parent:  The parent dialog or frame
        '''
        super(AssetListWidget, self).__init__(parent=parent)
        self._model = model
        self._item_widget_class = item_widget_class
        self.was_clicked = False

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        pass

    def post_build(self):
        pass

    def rebuild(self):
        '''Clear widget and add all assets again from model. Should be overridden by child'''
        raise NotImplementedError()

    def selection(self, as_widgets=False):
        '''Return list of selected model data or asset widgets if *as_widgets* is True'''
        result = []
        for widget in self.assets:
            if widget.selected:
                if as_widgets:
                    result.append(widget)
                else:
                    data = self.model.data(widget.index)
                    if data is None:
                        # Data has changed
                        return None
                    result.append(data)
        return result

    def checked(self, as_widgets=False):
        '''Return list of checked model data or asset widgets if *as_widgets* is True'''
        result = []
        for widget in self.assets:
            if widget.checked:
                if as_widgets:
                    result.append(widget)
                else:
                    data = self.model.data(widget.index)
                    if data is None:
                        # Data has changed
                        return None
                    result.append(data)
        return result

    def items(self):
        '''Return a list of all tuples, (data, widget), of all assets in list'''
        result = []
        for widget in self.assets:
            data = self.model.data(widget.index)
            if data is None:
                # Data has changed
                return None
            result.append((data, widget))
        return result

    def clear_selection(self):
        '''De-select all assets'''
        if not shiboken2.isValid(self):
            return
        selection_asset_data_changed = False
        for asset_widget in self.assets:
            if asset_widget.set_selected(False):
                selection_asset_data_changed = True
        if selection_asset_data_changed:
            selection = self.selection()
            if selection is not None:
                self.selectionUpdated.emit(selection)

    def asset_clicked(self, asset_widget, event):
        '''An asset were clicked in list, evaluate selection.'''
        selection_asset_data_changed = False
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.button() == QtCore.Qt.RightButton:
            return
        if (
            modifiers == QtCore.Qt.Key_Meta and platform.system() != 'Darwin'
        ) or (
            modifiers == QtCore.Qt.ControlModifier
            and platform.system() == 'Darwin'
        ):
            # Toggle selection
            if not asset_widget.selected:
                if asset_widget.set_selected(True):
                    selection_asset_data_changed = True
            else:
                if asset_widget.set_selected(False):
                    selection_asset_data_changed = True
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
                    if start_row <= widget.index.row() <= end_row:
                        if widget.set_selected(True):
                            selection_asset_data_changed = True
        else:
            self.clear_selection()
            if asset_widget.set_selected(True):
                selection_asset_data_changed = True
        self._last_clicked = asset_widget
        if selection_asset_data_changed:
            selection = self.selection()
            if selection is not None:
                self.selectionUpdated.emit(selection)

    def asset_checked(self, asset_widget):
        self.checkedUpdated.emit(self.checked())

    def add_widget(self, widget):
        self.layout().addWidget(widget)
        self.setup_widget(widget)

    def setup_widget(self, widget):
        '''Initialize accordion asset widget, ignore other types of widget in list'''
        if isinstance(widget, AccordionBaseWidget):
            widget.clicked.connect(partial(self.asset_clicked, widget))
            widget.checkedStateChanged.connect(self.asset_checked)

    def get_widget(self, index):
        '''Return the asset widget representation at *index*'''
        for widget in self.assets:
            if widget.index.row() == index.row():
                return widget

    def mousePressEvent(self, event):
        '''Consume this event, so parent client does not de-select all'''
        pass
