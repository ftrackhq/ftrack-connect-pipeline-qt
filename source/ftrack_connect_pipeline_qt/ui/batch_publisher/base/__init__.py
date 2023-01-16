# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import traceback
import uuid
from functools import partial

from Qt import QtCore, QtWidgets

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt.ui.utility.widget import (
    icon,
    overlay,
    scroll_area,
    dialog,
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
        '''Return client instance.'''
        return self._client

    @property
    def initial_items(self):
        '''Return the list of initial items passed to batch publisher widget from client'''
        return self._initial_items

    @property
    def level(self):
        '''The recursive level of this batch publisher widget.'''
        return self._level

    @property
    def session(self):
        return self._client.session

    @property
    def logger(self):
        return self._client.logger

    def __init__(self, client, initial_items, level=0, parent=None):
        self._client = client
        self._initial_items = initial_items
        self._level = level
        self.item_list = None
        self.total = self.failed = 0
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

        # Create the data model, it will contain tuple of custom data with item data and definition being the first twp elements
        self.model = AssetListModel(self.client.event_manager)

    def build(self):
        '''Build widget.'''
        self._label_info = QtWidgets.QLabel('No asset(s)')
        self._label_info.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self._label_info.setObjectName('gray')
        self.layout().addWidget(self._label_info)

        self.scroll = None
        if self.level == 0:
            self.scroll = scroll_area.ScrollArea()
            self.scroll.setWidgetResizable(True)
            self.scroll.setHorizontalScrollBarPolicy(
                QtCore.Qt.ScrollBarAlwaysOff
            )
            self.scroll.setStyle(QtWidgets.QStyleFactory.create("plastique"))

            self.layout().addWidget(self.scroll, 1000)

    def post_build(self):
        '''Build widget.'''
        pass

    def on_context_changed(self, context_id):
        '''Handle context change, should be overridden'''
        pass

    def build_items(self, definition):
        '''Build model data, DCC specific'''
        raise NotImplementedError()

    def set_items(self, items, item_list_widget_class):
        '''Create and deploy list of publishable *items* using *item_widget_class*'''

        # Create component list
        self.item_list = item_list_widget_class(self)
        self.listWidgetCreated.emit(self.item_list)

        if self.scroll:
            self.scroll.setWidget(self.item_list)
        else:
            self.layout().addWidget(self.item_list, 1000)

        # Will trigger list to be rebuilt.

        self.model.insertRows(0, items)

        self.item_list.selectionUpdated.connect(self._item_selection_updated)
        # Have client reflect upon checked items
        self.item_list.checkedUpdated.connect(self.client.refresh)

        if self.level == 0:
            self._label_info.setText(
                'Listing {} {}'.format(
                    self.model.rowCount(),
                    'assets' if self.model.rowCount() > 1 else 'asset',
                )
            )
        else:
            self._label_info.setText(
                '{} {}'.format(
                    self.model.rowCount(),
                    'dependencies'
                    if self.model.rowCount() > 1
                    else 'dependency',
                )
            )

    def _item_selection_updated(self, selection):
        '''Handle selection update.'''
        pass

    def prepare_run_definition(self, definition, asset_path):
        '''Should be imlemented by child.'''
        raise NotImplementedError()

    def count(self):
        '''Return amount publishable items (no recursion)'''
        item_widgets = self.item_list.checked()
        return len(item_widgets)

    def run(self):
        '''Prepare and run batch publish of checked items, called recursively'''
        # Load batch of components, any selected
        item_widgets = self.item_list.checked(as_widgets=True)
        self.total = len(item_widgets)
        self.succeeded = 0
        self.failed = 0

        if self.total == 0:
            return core_constants.SUCCESS_STATUS, 0, 0

        progress_widget = self.client.progress_widget

        # Each item contains a definition ready to run and a factory,
        # queue them up one by one. Start by preparing progress widget

        for item_widget in item_widgets:
            item = self.item_list.model.data(item_widget.index)[0]
            factory = item_widget.factory
            factory.progress_widget = (
                progress_widget  # Have factory update main progress widget
            )
            progress_widget.add_item(item)
            progress_widget.add_step(
                core_constants.CONTEXT,
                item_widget.get_ident(),
                batch_id=item_widget.item_id,
                indent=10 * self.level,
            )
            factory.build_progress_ui(item_widget.item_id)

            self.client.run_queue.put(item_widget)

            # Recursively add dependencies to progress widget and queue up
            if item_widget.dependencies_batch_publisher_widget is not None:
                item_widget.dependencies_batch_publisher_widget.run()

        if self.level > 0:
            return

        # Add cancel button wo widget
        self._abort_button = AbortButton('Abort')
        self._abort_button.clicked.connect(self.client.run_abort)
        progress_widget.widgets_added(self._abort_button)

        progress_widget.show_widget()

        # Trig start of execution
        self.client.runNextItem.emit()

    def run_item(self, item_widget):
        '''Publish a single item'''

        self.logger.info('Publishing {}'.format(item_widget.get_ident()))
        progress_widget = self.client.progress_widget

        # Prepare progress widget
        item = self.item_list.model.data(item_widget.index)
        progress_widget.set_status(
            core_constants.RUNNING_STATUS,
            'Publishing "{}"...'.format(item_widget.get_ident()),
        )
        progress_widget.show_widget()

        # Prepare batch publish definition, create parent context if necessary
        try:
            definition = self.prepare_run_definition(item)
            progress_widget.update_step_status(
                core_constants.CONTEXT,
                item_widget.get_ident(),
                core_constants.SUCCESS_STATUS,
                'Prepared publish',
                {},
                item_widget.item_id,
            )
        except Exception as e:
            # Log error and present in progress widget
            print(traceback.format_exc())
            self.logger.exception(e)
            progress_widget.update_step_status(
                core_constants.CONTEXT,
                item_widget.get_ident(),
                core_constants.ERROR_STATUS,
                str(e),
                traceback.format_exc(),
                item_widget.item_id,
            )
            self.failed += 1

            # Run next item
            self.client.runNextItem.emit()

            return

        # Run definition in background thread
        self.client.run_queue_async.put((item_widget, definition))

    def run_post(self):
        '''Summarize counts and store'''
        item_widgets = self.item_list.checked(as_widgets=True)

        total = self.total
        succeeded = self.succeeded
        failed = self.failed

        for item_widget in item_widgets:
            if item_widget.dependencies_batch_publisher_widget:
                (
                    _total,
                    _succeeded,
                    _failed,
                ) = item_widget.dependencies_batch_publisher_widget.run_post()
                total += _total
                succeeded += _succeeded
                failed += _failed
        return total, succeeded, failed


class BatchPublisherListBaseWidget(AssetListWidget):
    '''Base for item lists within the batch publisher'''

    @property
    def level(self):
        '''Return the recursive level of this widget'''
        return self._batch_publisher_widget.level

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
        '''Rebuild the list based on model data, must be implemented by child'''
        raise NotImplementedError()


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

    @property
    def batch_publisher_widget(self):
        '''Return the parent batch publisher widget'''
        return self._batch_publisher_widget

    @property
    def level(self):
        '''The recursive level of parent batch publisher widget.'''
        return self.batch_publisher_widget.level

    @property
    def item_id(self):
        '''Return the unique temporary batch publisher id of this item'''
        return self._item_id

    @property
    def logger(self):
        return self.batch_publisher_widget.logger

    def __init__(
        self,
        index,
        batch_publisher_widget,
        event_manager,
        collapsable=False,
        parent=None,
    ):
        '''
        Instantiate the asset widget

        :param index: index of this asset has in list
        :param assembler_widget: :class:`~ftrack_connect_pipeline_qt.ui.assembler.base.AssemblerBaseWidget` instance
        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param parent: the parent dialog or frame
        '''
        self._batch_publisher_widget = batch_publisher_widget
        self._item_id = str(uuid.uuid4())
        super(ItemBaseWidget, self).__init__(
            AccordionBaseWidget.SELECT_MODE_LIST,
            AccordionBaseWidget.CHECK_MODE_CHECKBOX,
            event_manager=event_manager,
            checked=False,
            collapsable=collapsable,
            parent=parent,
        )
        self.index = index
        self._item = None
        self._adjust_height()

    def init_options_button(self):
        '''Create the options button and connect ut to option build function'''
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

    def get_ident(self):
        '''Return human readable idendification of item'''
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
        # Clear out overlay, not needed anymore
        clear_layout(self.options_widget.main_widget.layout())

    def init_content(self, content_layout):
        '''No content in this accordion for now, should be implemented by DCC specific item widget'''
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
        pass

    def update_item(self, project_context_id):
        '''Have item reflect upon change of *project_context_id*, must be implemented by child'''
        raise NotImplementedError()

    def run_callback(self, item_widget, event):
        '''Executed after an item has been published through event from pipeline, should be implemented by child'''
        pass


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


class AbortButton(QtWidgets.QPushButton):
    def __init__(self, label, width=60, height=22, parent=None):
        super(AbortButton, self).__init__(label, parent=parent)
        self.setMinimumSize(QtCore.QSize(width, height))
