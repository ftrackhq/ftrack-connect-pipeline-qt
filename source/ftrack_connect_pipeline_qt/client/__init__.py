# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtGui, QtCore, QtWidgets
from ftrack_connect_pipeline import client, constants
from ftrack_connect_pipeline_qt.ui.utility.widget import header, definition_selector
from ftrack_connect_pipeline_qt.client.widgets import factory
from ftrack_connect_pipeline_qt import constants as qt_constants


class QtClient(client.Client, QtWidgets.QWidget):
    '''
    Base QT client widget class.
    '''

    ui = [constants.UI, qt_constants.UI]
    host_connection = None
    schema = None
    definition = None

    def __init__(self, event_manager,parent=None):
        '''Initialise with *event_manager* , and optional *ui* List and
        *parent* widget'''
        QtWidgets.QWidget.__init__(self, parent=parent)
        client.Client.__init__(self, event_manager)
        self.widget_factory = factory.WidgetFactory(
            event_manager,
            self.ui
        )

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
        super(QtClient, self)._host_discovered(event)
        self.host_selector.add_hosts(self.hosts)
        if self.definition_filter:
            self.host_selector.set_definition_filter(self.definition_filter)

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    def build(self):
        '''Build widgets and parent them.'''
        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)

        self.host_selector = definition_selector.DefinitionSelector()
        self.layout().addWidget(self.host_selector)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout().addWidget(self.scroll)

        self.run_button = QtWidgets.QPushButton('Run')
        self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.definition_changed.connect(self._definition_changed)
        self.host_selector.host_changed.connect(self._host_changed)
        self.run_button.clicked.connect(self._on_run)

        self.widget_factory.widget_status_updated.connect(
            self._on_widget_status_updated
        )

        self.widget_factory.widget_context_updated.connect(
            self._on_widget_context_updated
        )

        self.widget_factory.widget_run_plugin.connect(
            self._on_run_plugin
        )

        # # apply styles
        # theme.applyTheme(self, 'dark')
        # theme.applyFont()

    def _host_changed(self, host_connection):
        ''' Triggered when host_changed is called from the host_selector.'''

        if self.scroll.widget():
            self.scroll.widget().deleteLater()

    def _definition_changed(self, host_connection, schema, definition):
        ''' Triggered when definition_changed is called from the host_selector.
        Generates the widgets interface from the given *host_connection*,
        *schema* and *definition*'''

        if not host_connection:
            return

        self.logger.info('connection {}'.format(host_connection))
        self.host_connection = host_connection

        asset_type = []
        current_package = None
        for package in self.host_connection.definitions['package']:
            if package['name'] == definition['package']:
                asset_type = package['asset_type']
                current_package = package

        # set current context to host context
        self.context = host_connection.context or self.context

        context = {
            'context_id': self.context,
            'asset_type': asset_type
        }

        self.schema = schema
        self.definition = definition

        self.widget_factory.set_context(context)
        self.widget_factory.set_host_connection(self.host_connection)
        self.widget_factory.set_definition_type(self.definition['type'])
        self.widget_factory.set_package(current_package)

        self._current_def = self.widget_factory.create_widget(
            definition['name'],
            schema,
            self.definition
        )
        self.scroll.setWidget(self._current_def)

    def _on_widget_status_updated(self, data):
        ''' Triggered when a widget generated by the fabric has emit the
        widget_status_update signal.
        Sets the status from the given *data* to the header
        '''
        status, message = data
        self.header.setMessage(message, status)

    def _on_widget_context_updated(self, context_id):
        self.context = context_id
        self.host_connection.context = context_id

    def _on_run_plugin(self, plugin_data, method='run'):
        engine_type = self.definition['_config']['engine_type']
        # Plugin type is constructed using the engine_type and the plugin_type
        # (publisher.collector). We have to make sure that plugin_type is in
        # the data argument passed to the host_connection, because we are only
        # passing data to the engine. And the engine_type is only available
        # on the definition.
        plugin_type = '{}.{}'.format(engine_type, plugin_data['plugin_type'])
        data = {'plugin': plugin_data,
                'plugin_type': plugin_type,
                'method': method
                }
        self.host_connection.run(
            data, engine_type, self._run_callback
        )

    def _on_run(self):
        '''Function called when click the run button'''
        serialized_data = self._current_def.to_json_object()
        engine_type = serialized_data['_config']['engine_type']
        self.host_connection.run(
            serialized_data, engine_type, self._run_callback
        )

    def _run_callback(self, event):
        #TODO: if we run each plugin separately we will have to move all the
        # logic and validations in the client(here) and that may not make sense...
        print "_run_callback event --> {}".format(event)
        pass

