from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)


class NodeComboBox(QtWidgets.QWidget):
    refresh_clicked = QtCore.Signal()
    text_changed = QtCore.Signal(object)

    def __init__(self, parent=None):
        '''
        Initialize base accordion widget
        '''
        super(NodeComboBox, self).__init__(parent=parent)
        self.setLayout(QtWidgets.QVBoxLayout())

        h_layout = QtWidgets.QHBoxLayout()
        h_layout.setContentsMargins(
            15, 0, 0, 0
        )
        h_layout.setSpacing(0)

        self._combo_box = QtWidgets.QComboBox()

        h_layout.addWidget(self._combo_box, 20)

        self._refresh_button = CircularButton('sync')

        h_layout.addWidget(self._refresh_button)

        self.layout().addLayout(h_layout)

        self._warning = QtWidgets.QLabel()
        self._warning.setVisible(False)
        self.layout().addWidget(self._warning)

        self._refresh_button.clicked.connect(self._refresh)
        self._combo_box.currentTextChanged.connect(self._current_text_changed)

    def add_items(self, node_names, default_name=None):
        if node_names:
            self._combo_box.setDisabled(False)
        else:
            self._combo_box.setDisabled(True)
        self._combo_box.clear()
        for (index, node_name) in enumerate(node_names):
            self._combo_box.addItem(node_name)
            if node_name == default_name:
                self._combo_box.setCurrentIndex(index)

    def show_warning(self, text):
        self._warning.setVisible(True)
        self._warning.setText(
            '<html><i style="color:red">{}</i></html>'.format(text)
        )

    def hide_warning(self):
        self._warning.setVisible(False)

    def _refresh(self):
        self.refresh_clicked.emit()

    def _current_text_changed(self, text):
        self.text_changed.emit(text)

    def get_text(self):
        return self._combo_box.currentText()