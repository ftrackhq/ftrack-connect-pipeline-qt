
from Qt import QtCore


class BaseUi(QtCore.QObject):
    def __init__(self, *args, **kwargs):
        super(BaseUi, self).__init__(parent=kwargs.get('parent', None))

    def __del__(self):
        self.deleteLater()
