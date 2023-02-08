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
    itemPublished = QtCore.Signal(object)

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
        return self._level if not self._level is None else 0

    @property
    def session(self):
        return self._client.session

    @property
    def logger(self):
        return self._client.logger

    def __init__(self, client, initial_items, level=None, parent=None):
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
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(2, 2, 2, 2)

        # Create the data model, it will contain tuple of custom data with item data and definition being the first twp elements
        self.model = AssetListModel(self.client.event_manager)

    def build(self):
        '''Build widget.'''
        self._label_info = QtWidgets.QLabel()
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
        self.itemPublished.connect(self._on_item_published)
        self._update_info_label()

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

        self._update_info_label()

    def _update_info_label(self):
        raise NotImplementedError()

    def _item_selection_updated(self, selection):
        '''Handle selection update.'''
        pass

    def on_log_item_added(self, log_item):
        # Find the widget having options open
        for item_widget in self.item_list.assets:
            if item_widget.showing_options:
                item_widget.factory.update_widget(log_item)

    def prepare_run_definition(self, definition, asset_path):
        '''Should be imlemented by child.'''
        raise NotImplementedError()

    def count(self):
        '''Return amount publishable items (no recursion)'''
        item_widgets = self.item_list.checked()
        return len(item_widgets)

    def can_publish(self):
        '''Return True if there are publishable items'''
        raise NotImplementedError()

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
            progress_widget.add_item(item_widget.get_ident())
            progress_widget.add_step(
                core_constants.CONTEXT,
                core_constants.CONTEXT,
                batch_id=item_widget.item_id,
                indent=10 * self.level,
            )
            factory.build_progress_ui(
                item_widget.item_id, item_widget.get_ident()
            )

            item_widget.has_run = False
            self.client.prepare_queue.put(item_widget)

            item_widget.run()

        if self.level > 0:
            return

        # Add cancel button wo widget
        self._abort_button = AbortButton('Abort')
        self._abort_button.clicked.connect(self.client.run_abort)
        progress_widget.widgets_added(self._abort_button)

        progress_widget.show_widget()

        # Trig start of execution
        self.client.prepareNextItem.emit()

    def prepare_item(self, item_widget):
        '''Prepare publish of a single item'''

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
                core_constants.CONTEXT,
                core_constants.SUCCESS_STATUS,
                'Prepared context',
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
            self.client.prepareNextItem.emit()

            return

        self.client.queueNextItem.emit(item_widget, definition)

    def run_item(self, item_widget, definition):
        '''Publish a single item'''

        try:
            factory = item_widget.factory
            factory.listen_widget_updates()

            # Make sure item widget can react and extract metadata when publish has finished
            self.client.set_run_callback_function(
                partial(
                    item_widget.run_callback,
                    item_widget,
                )
            )

            item_widget.finalizer_user_data = None

            engine_type = definition['_config']['engine_type']

            # Run the definition, status feedback will come in async but pushed to main thread by factory
            self.client.run_definition(definition, engine_type)

            # Did publish succeed?
            if factory.has_error:
                item_widget.batch_publisher_widget.failed += 1
            else:
                item_widget.batch_publisher_widget.succeeded += 1
                item_widget.has_run = True
                # Have the batch publisher widget post process the item
                item_widget.batch_publisher_widget.itemPublished.emit(
                    item_widget
                )

        except Exception as e:
            self.logger.warning(traceback.format_exc())
            item_widget.batch_publisher_widget.failed += 1

        finally:
            self.client.set_run_callback_function(None)
            item_widget.factory.end_widget_updates()

            # Run next item in queue regardless of failure
            self.client.prepareNextItem.emit()

    def _on_item_published(self, item_widget):
        '''Executed when an item has been published, to be overridden by child'''
        pass

    def run_post(self):
        '''Summarize counts and store'''
        item_widgets = self.item_list.checked(as_widgets=True)

        total = self.total
        succeeded = self.succeeded
        failed = self.failed

        for item_widget in item_widgets:
            _total, _succeeded, _failed = item_widget.summarise()
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

    def __init__(self, batch_publisher_widget, item_widget_class, parent=None):
        self._batch_publisher_widget = batch_publisher_widget
        super(BatchPublisherListBaseWidget, self).__init__(
            self._batch_publisher_widget.model,
            item_widget_class,
            parent=parent,
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
    def has_run(self):
        '''Return the unique temporary batch publisher id of this item'''
        return self._has_run

    @has_run.setter
    def has_run(self, value):
        '''Set the unique temporary batch publisher id of this item'''
        self._has_run = value

    @property
    def session(self):
        return self._batch_publisher_widget.session

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
        self._has_run = False
        self.showing_options = False
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

    def post_build(self):
        super(ItemBaseWidget, self).post_build()
        self.factory.widgetRunPlugin.connect(
            self.batch_publisher_widget.client._on_run_plugin
        )

    def _build_options(self):
        '''Build options overlay with factory'''
        self.factory.listen_widget_updates()
        self.showing_options = (
            True  # Make sure fetch plugin results get to the right place
        )
        self.factory.build(self.options_widget.main_widget)
        # Make sure we can save options on close
        self.options_widget.overlay_container.close_btn.clicked.connect(
            self._store_options
        )
        # Show overlay
        self.options_widget.show_overlay()

    def _store_options(self):
        '''Serialize definition and store'''
        updated_definition = self.factory.to_json_object()

        self.factory.end_widget_updates()

        self.factory.set_definition(updated_definition)

        # Clear out overlay, not needed anymore
        clear_layout(self.options_widget.main_widget.layout())

        self.showing_options = False

    def init_content(self, content_layout):
        '''No content in this accordion for now, should be implemented by DCC specific item widget'''
        pass

    def set_data(self, definition):
        '''Update widget from data, should be overriden'''
        self._batch_publisher_widget.client.setup_widget_factory(
            self.factory, definition
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

    def run(self):
        '''Called during run of batch publisher, should be implemented by child'''
        pass

    def summarise(self):
        '''Called after run of batch publisher, summarize additional child publishes. Should be implemented by child'''
        return 0, 0, 0

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
