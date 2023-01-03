#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import shiboken2
import traceback
from functools import partial

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.utils import str_version

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import ModalDialog
from ftrack_connect_pipeline_qt.client.publish import QtPublisherClient
from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
from ftrack_connect_pipeline_qt.ui.factory import (
    WidgetFactoryBase,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    header,
    line,
    host_selector,
    button,
    scroll_area,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.context_selector import (
    ContextSelector,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.button import (
    RunButton,
)


class QtBatchPublisherClientWidget(QtPublisherClient, dialog.Dialog):
    ''' '''

    contextChanged = QtCore.Signal(object)  # Context has changed
    definitionsPopulated = QtCore.Signal(object)

    def __init__(
        self,
        event_manager,
        title=None,
        immediate_run=False,
        parent=None,
    ):
        '''
        Initialize the assembler client

        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param title: The title widget dialog should have
        :param multithreading_enabled: Multithreading is enabled

        :param parent:
        '''
        dialog.Dialog.__init__(self, parent=parent)
        QtPublisherClient.__init__(self, event_manager)
        self._immediate_run = immediate_run

        self.logger.debug('start batch publisher')

        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())
        self.setProperty('docked', 'true' if self.is_docked() else 'false')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.pre_build()
        self.build()
        self.post_build()

        self.discover_hosts()

        self.setWindowTitle(title or 'ftrack Batch Publisher')
        self.resize(800, 600)

    def get_theme_background_style(self):
        return 'ftrack'

    def is_docked(self):
        return False

    # Build

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(16, 16, 16, 16)
        self.header = header.Header(self.session)
        self.header.setMinimumHeight(50)

    def build(self):
        '''Build assembler widget.'''

        self.layout().addWidget(self.header)

        # Create the host selector, usually hidden
        self.host_selector = host_selector.HostSelector(self)
        self.layout().addWidget(self.host_selector)

        self.layout().addWidget(line.Line(style='solid'))

        self.progress_widget = WidgetFactoryBase.create_progress_widget(
            core_constants.BATCH_PUBLISHER
        )
        self.header.content_container.layout().addWidget(
            self.progress_widget.widget
        )

        self.context_selector = ContextSelector(self.session)
        self.layout().addWidget(self.context_selector, QtCore.Qt.AlignTop)

        self.definition_selector = self._build_definition_selector()
        self.definition_selector.refreshed.connect(partial(self.refresh, True))
        self.layout().addWidget(self.definition_selector)

        self.batch_publisher_widget = self._build_batch_publisher_widget()
        self.layout().addWidget(self.batch_publisher_widget, 1000)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(QtWidgets.QHBoxLayout())
        button_widget.layout().setContentsMargins(2, 4, 8, 0)
        button_widget.layout().addStretch()
        self.run_button = RunButton('PUBLISH')
        self.run_button.setFocus()
        button_widget.layout().addWidget(self.run_button)
        self.layout().addWidget(button_widget)

    def post_build(self):
        self.host_selector.hostChanged.connect(self.change_host)
        self.contextChanged.connect(self.on_context_changed_sync)
        self.definition_selector.definitionChanged.connect(
            self.change_definition
        )
        self.context_selector.changeContextClicked.connect(
            self._launch_context_selector
        )

        self.run_button.setFocus()
        self.run_button.clicked.connect(self.run)

    # Host

    def on_hosts_discovered(self, host_connections):
        '''(Override)'''
        self.host_selector.add_hosts(host_connections)

    def on_host_changed(self, host_connection):
        '''Triggered when client has set host connection'''
        if self.definition_filters:
            self.definition_selector.definition_filters = (
                self.definition_filters
            )
        if self.definition_extensions_filter:
            self.definition_selector.definition_extensions_filter = (
                self.definition_extensions_filter
            )
        # Feed it to definition selector, to get schemas stored
        self.definition_selector.on_host_changed(host_connection)

    # Context

    def on_context_changed(self, context_id):
        '''Async call upon context changed'''
        self.contextChanged.emit(context_id)

    def on_context_changed_sync(self, context_id):
        '''(Override) Context has been set'''
        if not shiboken2.isValid(self):
            # Widget has been closed while context changed
            return
        self.context_selector.context_id = self.context_id
        # Reset definition selector and clear client
        self.definition_selector.clear_definitions()
        self.definition_selector.populate_definitions()
        self.definitionsPopulated.emit(self.definition_selector.definitions)
        self.batch_publisher_widget.on_context_changed(context_id)

    # Definition

    def change_definition(self, definition, schema=None):
        if definition is None:
            return
        super(QtBatchPublisherClientWidget, self).change_definition(
            definition, schema=schema
        )
        # We have a definition selection, build model data - items
        items = self._build_items(definition)
        # Store and present
        self.batch_publisher_widget.set_items(
            items, self._get_list_widget_class()
        )

    # Use

    def _on_assets_discovered(self):
        '''The assets in AM has been discovered, refresh at our end.'''
        self.refresh()

    def _on_components_checked(self, available_components_count):
        self.definition_changed(self.definition, available_components_count)
        self.run_button.setEnabled(available_components_count >= 1)

    # Run

    def setup_widget_factory(self, widget_factory, definition):
        widget_factory.set_definition(definition)
        widget_factory.host_connection = self._host_connection
        widget_factory.set_definition_type(definition['type'])

    def _on_run_plugin(self, plugin_data, method):
        '''Function called to run one single plugin *plugin_data* with the
        plugin information and the *method* to be run has to be passed'''
        self.run_plugin(plugin_data, method, self.engine_type)

    def _build_definition_selector(self):
        raise NotImplementedError()

    def _build_batch_publisher_widget(self):
        raise NotImplementedError()

    def _get_list_widget_class(self):
        raise NotImplementedError()

    def _build_items(self, definition):
        raise NotImplementedError()

    def prepare_run_definition(self, definition, asset_path):
        '''Should be overridden by child.'''
        raise NotImplementedError()

    def run(self):
        '''Function called when the run button is clicked.'''
        # Load batch of components, any selected
        item_widgets = self.batch_publisher_widget.item_list.selection(
            as_widgets=True
        )
        if len(item_widgets) == 0:
            dialog.ModalDialog(
                self,
                message='Please select at least one item to publish!'.format(),
            )
            return
        # Each item contains a definition ready to run and a factory,
        # run them one by one. Start by preparing progress widget
        self.progress_widget.prepare_add_steps()
        self.progress_widget.set_status(
            core_constants.RUNNING_STATUS, 'Initializing...'
        )
        for item_widget in item_widgets:
            item = self.batch_publisher_widget.item_list.model.data(
                item_widget.index
            )[0]
            factory = item_widget.factory
            factory.progress_widget = (
                self.progress_widget
            )  # Have factory update main progress widget
            self.progress_widget.add_item(item)
            self.progress_widget.add_step(
                core_constants.CONTEXT,
                item_widget.get_progress_label(item),
                batch_id=item[0],
            )
            factory.build_progress_ui(item)
        self.progress_widget.components_added()

        self.progress_widget.show_widget()
        failed = 0
        for item_widget in item_widgets:
            # Prepare progress widget
            item = self.batch_publisher_widget.item_list.model.data(
                item_widget.index
            )[0]
            self.progress_widget.set_status(
                core_constants.RUNNING_STATUS,
                'Publishing {}...'.format(item),
            )
            # Prepare batch publish definition, create parent context if neccessary
            try:
                definition = self.prepare_run_definition(item)
                self.progress_widget.update_step_status(
                    core_constants.CONTEXT,
                    item_widget.get_progress_label(item),
                    core_constants.SUCCESS_STATUS,
                    'Asset build validated',
                    None,
                    item[0],
                )
            except Exception as e:
                # Log error and present in progress widget
                self.logger.exception(e)
                self.progress_widget.update_step_status(
                    core_constants.CONTEXT,
                    item_widget.get_progress_label(item),
                    core_constants.ERROR_STATUS,
                    str(e),
                    traceback.format_exc(),
                    item[0],
                )
                failed += 1
            else:
                factory = item_widget.factory
                factory.listen_widget_updates()

                engine_type = definition['_config']['engine_type']
                try:
                    self.run_definition(definition, engine_type)
                    # Did it go well?
                    if factory.has_error:
                        failed += 1
                finally:
                    item_widget.factory.end_widget_updates()

        succeeded = len(item_widgets) - failed
        if succeeded > 0:
            if failed == 0:
                self.progress_widget.set_status(
                    core_constants.SUCCESS_STATUS,
                    'Successfully published {}/{} asset{}!'.format(
                        succeeded,
                        len(item_widgets),
                        's' if len(item_widgets) > 1 else '',
                    ),
                )
            else:
                self.progress_widget.set_status(
                    core_constants.WARNING_STATUS,
                    'Successfully published {}/{} asset{}, {} failed - check logs for more information!'.format(
                        succeeded,
                        len(item_widgets),
                        's' if len(item_widgets) > 1 else '',
                        failed,
                    ),
                )
            self.asset_manager.asset_manager_widget.rebuild.emit()
        else:
            self.progress_widget.set_status(
                core_constants.ERROR_STATUS,
                'Could not publish asset{} - check logs for more information!'.format(
                    's' if len(item_widgets) > 1 else '',
                ),
            )

    def refresh(self):
        pass

    def _launch_context_selector(self):
        '''Close client (if not docked) and open entity browser.'''
        if not self.is_docked():
            self.hide()
        self.host_connection.launch_client(qt_constants.CHANGE_CONTEXT_WIDGET)

    def closeEvent(self, e):
        super(QtBatchPublisherClientWidget, self).closeEvent(e)
        self.logger.debug('closing qt client')
        # Unsubscribe to context change events
        self.unsubscribe_host_context_change()
