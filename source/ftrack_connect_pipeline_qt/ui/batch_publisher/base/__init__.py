# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline_qt.ui.utility.widget import (
    icon,
    overlay,
    scroll_area,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.button import OptionsButton

from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel
from ftrack_connect_pipeline_qt.ui.factory.batch_publisher import (
    BatchPublisherWidgetFactory,
)
from ftrack_connect_pipeline_qt.utils import (
    set_property,
    clear_layout,
    get_main_framework_window_from_widget,
)
from ftrack_connect_pipeline_qt.ui.asset_manager.base import (
    AssetListWidget,
)


class BatchPublisherBaseWidget(QtWidgets.QWidget):

    listWidgetCreated = QtCore.Signal(object)

    @property
    def client(self):
        return self._client

    @property
    def session(self):
        return self._client.session

    def __init__(self, client, parent=None):
        self._client = client
        super(BatchPublisherBaseWidget, self).__init__(parent=parent)
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Create objects widget.'''
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.model = AssetListModel(self.client.event_manager)

    def build(self):
        '''Build widget.'''
        self._label_info = QtWidgets.QLabel('No asset(s)')
        self._label_info.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self._label_info.setObjectName('gray')
        self.layout().addWidget(self._label_info)

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setStyle(QtWidgets.QStyleFactory.create("plastique"))

        self.layout().addWidget(self.scroll, 1000)

    def post_build(self):
        '''Build widget.'''
        pass

    def on_context_changed(self, context_id):
        '''Handle context change, should be overridden'''
        pass

    def set_items(self, items, item_widget_class):
        '''Create and deploy list of publishable *items* using *item_widget_class*'''
        # Create component list
        self.item_list = item_widget_class(self)
        self.listWidgetCreated.emit(self.item_list)

        self.scroll.setWidget(self.item_list)

        # Will trigger list to be rebuilt.
        self.model.insertRows(0, items)

        self._label_info.setText(
            'Listing {} asset{}'.format(
                self.model.rowCount(),
                's' if self.model.rowCount() > 1 else '',
            )
        )


class BatchPublisherListBaseWidget(AssetListWidget):
    '''Base for item lists within the batch publisher'''

    def __init__(self, batch_publisher_widget, parent=None):
        self._batch_publisher_widget = batch_publisher_widget
        super(BatchPublisherListBaseWidget, self).__init__(
            self._batch_publisher_widget.model, parent=parent
        )

    def post_build(self):
        super(BatchPublisherListBaseWidget, self).post_build()
        self._model.rowsInserted.connect(self._on_items_added)
        self._model.modelReset.connect(self._on_items_added)
        self._model.rowsRemoved.connect(self._on_items_added)
        self._model.dataChanged.connect(self._on_items_added)

    def _on_items_added(self, *args):
        '''Model has been updated'''
        self.rebuild()
        selection = self.selection()
        if selection:
            self.selectionUpdated.emit(selection)

    def rebuild(self):
        raise NotImplementedError()

    def get_loadable(self):
        '''Return a list of all loadable assets regardless of selection'''
        result = []
        for widget in self.assets:
            if widget.definition is not None:
                widget.set_selected(True)
                result.append(widget)
        return result


class ItemBaseWidget(AccordionBaseWidget):
    '''Base widget representation of an item within the batch publisher'''

    @property
    def index(self):
        '''Return the index this asset has in list'''
        return self._index

    @index.setter
    def index(self, value):
        '''Set the index this asset has in list'''
        self._index = value

    @property
    def options_widget(self):
        '''Return the widget representing options'''
        return self._options_button

    @property
    def definition(self):
        '''Return the currently selected definition to use for loading'''
        return (
            self._widget_factory.definition if self._widget_factory else None
        )

    @property
    def factory(self):
        '''Return the factory to use for building options and loader serialize'''
        return self._widget_factory

    @property
    def item(self):
        '''Return the generic publishable item data for this widget'''
        return self._item

    @item.setter
    def item(self, value):
        '''Set generic publishable item data for this widget'''
        self._item = value

    @property
    def info_message(self):
        '''Return the warning message'''
        return self._info_label.text()

    @info_message.setter
    def info_message(self, value):
        '''Set the warning message and adjust height'''
        if len(value or '') > 0:
            self._info_label.setText(value)
            self.info_message_widget.setVisible(True)
        else:
            self.info_message_widget.setVisible(False)
        self._adjust_height()

    @property
    def session(self):
        return self._batch_publisher_widget.session

    def __init__(
        self, index, batch_publisher_widget, event_manager, parent=None
    ):
        '''
        Instantiate the asset widget

        :param index: index of this asset has in list
        :param assembler_widget: :class:`~ftrack_connect_pipeline_qt.ui.assembler.base.AssemblerBaseWidget` instance
        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param parent: the parent dialog or frame
        '''
        self._batch_publisher_widget = batch_publisher_widget
        super(ItemBaseWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_LIST,
            AccordionBaseWidget.CHECK_MODE_CHECKBOX,
            event_manager=event_manager,
            checked=False,
            collapsable=False,
            parent=parent,
        )
        self.index = index
        self._item = None
        self._adjust_height()

    def init_options_button(self):
        self._options_button = PublisherOptionsButton(
            'O', icon.MaterialIcon('settings', color='gray')
        )
        self._options_button.setObjectName('borderless')
        self._options_button.clicked.connect(self._build_options)
        return self._options_button

    def get_ident_widget(self):
        '''Widget containing identification of item (main label)'''
        raise NotImplementedError()

    def get_context_widget(self):
        '''Widget containing visual context feedback on the item - e.g. were item will be published'''
        raise NotImplementedError()

    def get_progress_label(self, item):
        '''Return the label to use for progress widget, from *item*'''
        raise NotImplementedError()

    def init_header_content(self, header_widget, collapsed):
        '''Build all widgets'''
        header_layout = QtWidgets.QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_widget.setLayout(header_layout)

        upper_widget = QtWidgets.QWidget()
        upper_layout = QtWidgets.QHBoxLayout()
        upper_layout.setContentsMargins(5, 1, 1, 1)
        upper_layout.setSpacing(2)
        upper_widget.setMinimumHeight(25)
        upper_widget.setLayout(upper_layout)

        # Append ident widget
        upper_layout.addWidget(self.get_ident_widget())

        upper_layout.addWidget(QtWidgets.QLabel(), 100)

        upper_layout.addWidget(self.get_context_widget())

        # Options widget,initialize its factory
        upper_layout.addWidget(self.init_options_button())

        self._widget_factory = BatchPublisherWidgetFactory(
            self.event_manager, self._batch_publisher_widget.client.ui_types
        )

        header_layout.addWidget(upper_widget, 10)

        self.info_message_widget = QtWidgets.QWidget()
        lower_layout = QtWidgets.QHBoxLayout()
        lower_layout.setContentsMargins(1, 1, 1, 1)
        lower_layout.setSpacing(1)
        self.info_message_widget.setLayout(lower_layout)

        info_icon_label = QtWidgets.QLabel()
        info_icon_label.setPixmap(
            icon.MaterialIcon('info', color='#5cbaff').pixmap(
                QtCore.QSize(16, 16)
            )
        )
        lower_layout.addWidget(info_icon_label)
        self._info_label = InfoLabel()
        lower_layout.addWidget(self._info_label, 100)

        header_layout.addWidget(self.info_message_widget)
        self.info_message_widget.setVisible(False)

    def _build_options(self):
        '''Build options overlay with factory'''
        self._widget_factory.build(self.options_widget.main_widget)
        # Make sure we can save options on close
        self.options_widget.overlay_container.close_btn.clicked.connect(
            self._store_options
        )
        # Show overlay
        self.options_widget.show_overlay()

    def _store_options(self):
        '''Serialize definition and store'''
        updated_definition = self._widget_factory.to_json_object()

        self._widget_factory.set_definition(updated_definition)
        # Transfer back load mode
        self._set_default_mode()
        # Clear out overlay, not needed anymore
        clear_layout(self.options_widget.main_widget.layout())

    def init_content(self, content_layout):
        '''No content in this accordion for now'''
        pass

    def set_data(self, definition):
        '''Update widget from data, should be overriden'''
        self._batch_publisher_widget.client.setup_widget_factory(
            self._widget_factory, definition
        )

    def on_collapse(self, collapsed):
        '''Not collapsable'''
        pass

    def get_height(self):
        '''Return the height of the widget in pixels, can be overridden by child'''
        return 32

    def _adjust_height(self):
        '''Align the height with warning label'''
        widget_height = self.get_height() + (
            18 if len(self.info_message) > 0 else 0
        )
        self.header.setMinimumHeight(widget_height)
        self.header.setMaximumHeight(widget_height)
        self.setMinimumHeight(widget_height)
        self.setMaximumHeight(widget_height)


class PublisherOptionsButton(OptionsButton):
    '''Create loader options button with its overlay'''

    def __init__(self, title, icon, parent=None):
        super(PublisherOptionsButton, self).__init__(parent=parent)
        self.name = title
        self._icon = icon

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumSize(30, 30)
        self.setMaximumSize(30, 30)
        self.setIcon(self._icon)
        self.setFlat(True)

    def build(self):
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(QtWidgets.QVBoxLayout())
        self.main_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        self.main_widget.layout().setContentsMargins(5, 1, 5, 10)

        self.scroll = scroll_area.ScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.main_widget)

        self.overlay_container = overlay.Overlay(
            self.scroll, width_percentage=0.6, height_percentage=0.9
        )
        self.overlay_container.setVisible(False)

    def post_build(self):
        pass

    def show_overlay(self):
        '''Bring up options'''
        main_window = get_main_framework_window_from_widget(self)
        if main_window:
            self.overlay_container.setParent(main_window)
        self.overlay_container.setVisible(True)


class InfoLabel(QtWidgets.QLabel):
    def __init__(self):
        super(InfoLabel, self).__init__()
