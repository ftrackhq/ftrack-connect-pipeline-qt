# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from Qt import QtGui, QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import JsonObject
import uuid
from ftrack_connect_pipeline_qt import utils

class PluginContainerObject(JsonObject):
    '''
    Override widget representation of an object
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise PluginContainerObject with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(PluginContainerObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        if self.previous_object_data:
            self.stage_name = self.previous_object_data.get('name')

        self.properties_widgets = {}

        if not self.properties:
            label = QtWidgets.QLabel(
                'Invalid object description (missing properties)',
                self)
            label.setStyleSheet('QLabel { color: red; }')
            self.layout().addWidget(label)
        else:
            if 'widget' in list(self.properties.keys()):
                widget = self.widget_factory.fetch_plugin_widget(
                    self.fragment_data, self.stage_name
                )
                self.layout().addWidget(widget)
            else:
                for k, v in list(self.properties.items()):
                    new_fragment_data = None
                    if self.fragment_data:
                        new_fragment_data = self.fragment_data.get(k)

                    guid = uuid.uuid4().hex
                    worker = utils.WorkerT(
                        self.widget_factory.find_widget,
                        name=k,
                        schema_fragment=v,
                        fragment_data=new_fragment_data,
                        previous_object_data=self.fragment_data
                    )
                    worker.start()
                    while worker.isRunning():
                        app = QtWidgets.QApplication.instance()
                        app.processEvents()
                    if worker.error:
                        raise worker.error[1].with_traceback(worker.error[2])

                    widget_fn = worker.result

                    widget = self.widget_factory.create_widget(
                        widget_fn=widget_fn,
                        name=k,
                        schema_fragment=v,
                        fragment_data=new_fragment_data,
                        previous_object_data=self.fragment_data
                    )
                    self.layout().addWidget(widget)
                    self.properties_widgets[k] = widget
