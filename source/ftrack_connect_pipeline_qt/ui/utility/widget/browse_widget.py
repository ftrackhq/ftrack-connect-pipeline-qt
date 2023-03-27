from Qt import QtWidgets


class BrowseWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        '''
        Initialize base accordion widget
        '''
        super(BrowseWidget, self).__init__(parent=parent)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(
            15, 0, 0, 0
        )
        self.layout().setSpacing(0)

        self._path_le = QtWidgets.QLineEdit()

        self.layout().addWidget(self._path_le, 20)

        self._browse_btn = QtWidgets.QPushButton('BROWSE')
        self._browse_btn.setObjectName('borderless')

        self.layout().addWidget(self._browse_btn)

