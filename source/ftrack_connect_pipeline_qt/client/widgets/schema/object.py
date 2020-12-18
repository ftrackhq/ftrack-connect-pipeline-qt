# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget

def merge(source, destination):
    """
    Utility function to merge two json objects
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination

class JsonObject(BaseJsonWidget):
    '''Widget representation of an object'''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise JsonObject with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(JsonObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        if self.schema_fragment.get('allOf'):
            # Dealing with allOf objects in the schemas, will create the widget
            # without any inner widgets or grupboxes, layout....
            new_schema = self.schema_fragment.get('allOf')[0]
            for k, v in self.schema_fragment.items():
                if k != 'allOf':
                    new_schema[k] = merge(v, new_schema[k])
            widget = self.widget_factory.create_widget(
                self.name, new_schema, self.fragment_data,
                self.previous_object_data
            )
            self.layout().addWidget(widget)
            return

        self.groupBox = QtWidgets.QGroupBox(self.name, self._parent)
        layout = QtWidgets.QVBoxLayout()
        self.innerLayout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.groupBox.setLayout(layout)
        self.groupBox.setFlat(False)
        self.groupBox.layout().setContentsMargins(0, 0, 0, 0)

        if self.previous_object_data:
            self.plugin_type = self.previous_object_data.get('name')

        self.groupBox.setToolTip(self.description)

        self.properties_widgets = {}

        if not self.properties:
            label = QtWidgets.QLabel(
                'Invalid object description (missing properties)',
                self)
            label.setStyleSheet('QLabel { color: red; }')
            layout.addWidget(label)
        else:
            if 'widget' in list(self.properties.keys()):
                widget = self.widget_factory.fetch_plugin_widget(
                    self.fragment_data, self.plugin_type
                )
                self.innerLayout.addWidget(widget)
            else:
                for k, v in list(self.properties.items()):
                    new_fragment_data = None
                    if self.fragment_data:
                        new_fragment_data = self.fragment_data.get(k)
                    widget = self.widget_factory.create_widget(
                        k, v, new_fragment_data, self.fragment_data
                    )
                    self.innerLayout.addWidget(widget)
                    self.properties_widgets[k] = widget
        layout.addLayout(self.innerLayout)
        self.layout().addWidget(self.groupBox)

    def to_json_object(self):
        out = {}

        if self.schema_fragment.get('allOf'):
            # return the widget information when schema cointains allOf,
            # the widget doesn't have any inner widgets, so we query the
            # information from the widget 0 which is the allOf widget, and
            # augment the widget information with the data_fragment keys and
            # values to match the schema.
            widget = self.layout().itemAt(0).widget()
            if 'to_json_object' in dir(widget):
                out = widget.to_json_object()
                for k, v in list(self.fragment_data.items()):
                    if k not in list(out.keys()):
                        out[k] = v
        elif 'widget' in list(self.properties.keys()):
            # return the widget information when widget is in properties keys,
            # and augment the widget information with the data_fragment keys and
            # values to match the schema.
            widget = self.widget_factory.get_registered_widget_plugin(
                self.fragment_data)
            out = widget.to_json_object()
            for k, v in list(self.fragment_data.items()):
                if k not in list(out.keys()):
                    out[k] = v
        else:
            # Return the widget information for any other case.
            for k, v in list(self.properties.items()):
                widget = self.properties_widgets[k]
                out[k] = widget.to_json_object()

        return out
