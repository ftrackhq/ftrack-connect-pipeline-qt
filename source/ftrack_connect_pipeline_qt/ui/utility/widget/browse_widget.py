from Qt import QtWidgets, QtCore


class BrowseWidget(QtWidgets.QWidget):
    browse_button_clicked = QtCore.Signal()

    def __init__(self, parent=None):
        '''
        Initialize base accordion widget
        '''
        super(BrowseWidget, self).__init__(parent=parent)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(15, 0, 0, 0)
        self.layout().setSpacing(0)

        self._path_le = QtWidgets.QLineEdit()

        self.layout().addWidget(self._path_le, 20)

        self._browse_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_btn.setObjectName('borderless')

        self.layout().addWidget(self._browse_btn)

        self._browse_btn.clicked.connect(self._browse_button_clicked)

    def get_path(self):
        return self._path_le.text()

    def set_path(self, path_text):
        self._path_le.setText(path_text)

    def set_tool_tip(self, tooltip_text):
        self._path_le.setToolTip(tooltip_text)

    def _browse_button_clicked(self):
        self.browse_button_clicked.emit()
