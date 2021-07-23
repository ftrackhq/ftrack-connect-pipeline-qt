# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget


class AccordionStageArray(BaseJsonWidget):
    '''Widget representation of an array'''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise JsonArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(AccordionStageArray, self).__init__(
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

                # We create an accordion widget only for the wanted components.
                has_acordion = False
                accordion_widget = None
                if name in['validator', 'output']:
                    has_acordion = True
                    accordion_widget = AccordionWidget(
                        title=name#, checkable=optional_component
                    )
                obj = self.widget_factory.create_widget(
                    name, schema_fragment, data,
                    self.previous_object_data
                )
                if has_acordion:
                    accordion_widget.add_widget(obj)
                    self.innerLayout.addWidget(accordion_widget)
                else:
                    self.innerLayout.addWidget(obj)
                self.count += 1

        self.layout().addLayout(self.innerLayout)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        out = []
        for i in range(0, self.innerLayout.count()):
            widget = self.innerLayout.itemAt(i).widget()
            if widget.__class__.__name__ == 'AccordionWidget':
                for idx in range(0, widget.count_widgets()):
                    in_widget = widget.get_witget_at(idx)
                    if 'to_json_object' in dir(in_widget):
                        data = in_widget.to_json_object()
                        data['enabled'] = widget.is_checked()
                        out.append(data)
            elif 'to_json_object' in dir(widget):
                out.append(widget.to_json_object())
        return out

