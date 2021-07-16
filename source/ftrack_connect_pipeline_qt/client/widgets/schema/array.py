# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget
import uuid
from ftrack_connect_pipeline_qt import utils


class JsonArray(BaseJsonWidget):
    '''Widget representation of an array'''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise JsonArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(JsonArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )
    def build(self):
        self.count = 0
        self.maxItems = self.schema_fragment.get('maxItems')

        self.innerLayout = QtWidgets.QVBoxLayout()

        if 'items' in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                if type(data) == dict:
                    name = data.get('name')
                else:
                    name = data
                # The oneOf implementation for the schemas, oneOf is a list
                # of refs
                if self.schema_fragment['items'].get('oneOf'):
                    schema_fragment = self.schema_fragment['items'].get(
                        'oneOf'
                    )[self.count]
                else:
                    schema_fragment = self.schema_fragment['items']

                worker = utils.WorkerT(
                    self.widget_factory.find_widget,
                    name, schema_fragment, data,
                    self.previous_object_data
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
                    name=name,
                    schema_fragment=schema_fragment,
                    fragment_data=data,
                    previous_object_data=self.previous_object_data
                )
                self.innerLayout.addWidget(widget)
                self.count += 1

        self.layout().addLayout(self.innerLayout)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        out = []
        for i in range(0, self.innerLayout.count()):
            widget = self.innerLayout.itemAt(i).widget()
            if 'to_json_object' in dir(widget):
                out.append(widget.to_json_object())
        return out

