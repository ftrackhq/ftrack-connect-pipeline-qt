# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class JsonString(BaseJsonWidget):
    """
        Widget representation of a string.
        Strings are text boxes with labels for names.
    """
    def __init__(self, name, schema_fragment, fragment_data,
                 previous_object_data, widgetFactory, parent=None):

        super(JsonString, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widgetFactory, parent=parent
        )

        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.edit = QtWidgets.QLineEdit()

        self.label.setToolTip(self.description)

        if "default" in self.schema_fragment:
            self.edit.setPlaceholderText(self.schema_fragment['default'])

        if self.fragment_data:
            self.edit.setText(self.fragment_data)

        hbox.addWidget(self.label)
        hbox.addWidget(self.edit)

        self.layout().addLayout(hbox)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        return str(self.edit.text())