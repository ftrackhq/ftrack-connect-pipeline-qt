from Qt import QtWidgets, QtCore


class RadioButtonGroup(QtWidgets.QWidget):
    option_changed = QtCore.Signal(object, object, object)

    def __init__(self, parent=None):
        '''
        Initialize base accordion widget
        '''
        super(RadioButtonGroup, self).__init__(parent=parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.registry = {}

        self.bg = QtWidgets.QButtonGroup(self)
        self.bg.buttonClicked.connect(self._update_selected_option)

    def set_default(self, name):
        self.registry[name]["widget"].setChecked(True)

    def add_button(self, name, label, inner_widget):
        new_button = QtWidgets.QRadioButton(label)
        self.bg.addButton(new_button)
        self.layout().addWidget(new_button)
        if not inner_widget:
            inner_widget = QtWidgets.QWidget()
        self.layout().addWidget(inner_widget)
        self.registry[name] = {
            "widget": new_button,
            "inner_widget": inner_widget
        }
        inner_widget.setVisible(False)
        if len(self.registry.keys()) == 1:
            self.set_default(name)
        return new_button

    def _update_selected_option(self, clicked_button):
        for name, values in self.registry.items():
            values["inner_widget"].setVisible(values["widget"].isChecked())
            if values['widget'] == clicked_button:
                self.option_changed.emit(
                    name, values['widget'], values["inner_widget"]
                )
