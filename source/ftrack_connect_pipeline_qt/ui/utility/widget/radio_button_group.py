from Qt import QtWidgets, QtCore


class RadioButtonGroup(QtWidgets.QWidget):
    ''' Radio Button Group Widget'''
    option_changed = QtCore.Signal(object, object, object)

    def __init__(self, parent=None):
        '''
        Initialize Radio Button Group Widget
        '''
        super(RadioButtonGroup, self).__init__(parent=parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.registry = {}

        self.bg = QtWidgets.QButtonGroup(self)
        self.bg.buttonClicked.connect(self._update_selected_option)

    def set_default(self, name):
        ''' Set given *name* as selected radio button '''
        self.registry[name]["widget"].setChecked(True)
        self._update_selected_option(self.registry[name]["widget"])

    def add_button(self, name, label, inner_widget):
        ''' Add new radio button to group with the given *name* *label* and
        *inner_widget*'''
        new_button = QtWidgets.QRadioButton(label)
        self.bg.addButton(new_button)
        self.layout().addWidget(new_button)
        if not inner_widget:
            inner_widget = QtWidgets.QWidget()
        self.layout().addWidget(inner_widget)
        self.registry[name] = {
            "widget": new_button,
            "inner_widget": inner_widget,
        }
        inner_widget.setVisible(False)
        if len(self.registry.keys()) == 1:
            self.set_default(name)
        return new_button

    def _update_selected_option(self, clicked_button):
        ''' New radio button has been selected, show inner widget and
        emit signal '''
        for name, values in self.registry.items():
            values["inner_widget"].setVisible(values["widget"].isChecked())
            if values['widget'] == clicked_button:
                self.option_changed.emit(
                    name, values['widget'], values["inner_widget"]
                )

    def get_checked_button(self):
        '''Returns current selected radio button'''
        button = self.bg.checkedButton()
        for name, values in self.registry.items():
            if button in values["widget"]:
                return name, values['widget'], values["inner_widget"]
