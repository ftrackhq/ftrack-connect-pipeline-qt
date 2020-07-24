#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial

from ftrack_connect_pipeline.client.asset_manager import AssetManagerClient
from Qt import QtWidgets, QtCore, QtCompat, QtGui
from ftrack_connect_pipeline_qt.ui.utility.widget import header, host_selector
from ftrack_connect_pipeline_qt.ui.asset_manager import AssetManagerWidget
from ftrack_connect_pipeline import constants as core_const


class QtAssetManagerClient(AssetManagerClient, QtWidgets.QWidget):
    '''
    Base load widget class.
    '''
    definition_filter = 'asset_manager'

    def __init__(self, event_manager, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        AssetManagerClient.__init__(self, event_manager)

        self.asset_manager_widget = AssetManagerWidget(event_manager)
        self.asset_manager_widget.set_asset_list(self.ftrack_asset_list)

        self.host_connection = None

        self.pre_build()
        self.build()
        self.post_build()
        self.add_hosts(self.discover_hosts())

    def add_hosts(self, hosts):
        for host in hosts:
            if host in self.hosts:
                continue
            self._host_list.append(host)

    def _host_discovered(self, event):
        '''callback, adds new hosts connection from the given *event* to the
        host_selector'''
        super(AssetManagerClient, self)._host_discovered(event)
        self.host_selector.add_hosts(self.hosts)

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)

        self.host_selector = host_selector.HostSelector()
        self.layout().addWidget(self.host_selector)

        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed,
            QtWidgets.QSizePolicy.Fixed
        )
        self.layout().addWidget(self.refresh_button, alignment=QtCore.Qt.AlignRight)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.host_changed.connect(self._host_changed)
        self.refresh_button.clicked.connect(partial(self._refresh_ui,None))

        self.asset_manager_widget.widget_status_updated.connect(
            self._on_widget_status_updated
        )

    def _on_widget_status_updated(self, data):
        ''' Triggered when a widget generated by the fabric has emit the
        widget_status_update signal.
        Sets the status from the given *data* to the header
        '''
        status, message = data
        self.header.setMessage(message, status)

    def _host_changed(self, host_connection):
        ''' Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *host_connection*,
        *schema* and *definition*'''
        if not host_connection:
            return

        self.logger.info('connection {}'.format(host_connection))
        self.host_connection = host_connection

        self.asset_manager_widget.set_host_connection(self.host_connection)

        self.schemas = [
            schema for schema in self.host_connection.definitions['schema']
            if schema.get('title').lower() == 'asset_manager'
        ]
        #Only one schema available for now, we Don't have a schema selector
        # on the AM
        schema = self.schemas[0]
        schema_title = schema.get('title').lower()
        definitions = self.host_connection.definitions.get(schema_title)
        #Only one definition for now, we don't have a definition schema on the
        # AM
        self.definition = definitions[0]
        self.schema_engine = self.definition['_config']['engine']

        self.action_plugins = self.definition['actions']
        self.menu_action_plugins = self.definition['menu_actions']
        self.discover_plugins = self.definition['discover']

        self._run_discover_assets(self.discover_plugins[0])
        self.asset_manager_widget.engine = self.schema_engine
        self.asset_manager_widget.set_context_actions(self.menu_action_plugins)

        #TODO: discover actions for the context menu
        self.scroll.setWidget(self.asset_manager_widget)
        self._listen_refresh_request()

    def _run_discover_assets(self, plugin):
        self._reset_asset_list()
        self.host_connection.run(
            plugin, self.schema_engine, self._asset_discovered
        )

    def _asset_discovered(self, event):
        '''callback, adds new hosts connection from the given *event*'''
        AssetManagerClient._asset_discovered(self, event)
        self.asset_manager_widget.set_asset_list(self.ftrack_asset_list)

    def _listen_refresh_request(self):
        self.event_manager.subscribe(
            '{} and data.pipeline.host_id={}'.format(
                core_const.PIPELINE_REFRESH_AM, self.host_connection.id
            ),
            self._refresh_ui
        )
        self.logger.info(
            'subscribe to asset manager version changed  {} ready.'.format(
                self.host_connection.id
            )
        )

    def _refresh_ui(self, event):
        if not self.host_connection:
            return
        self._run_discover_assets(self.discover_plugins[0])