import logging
from Qt import QtWidgets, QtCore, QtGui


class AssetComboBox(QtWidgets.QComboBox):
    context_changed = QtCore.Signal(object)
    valid_asset_name = QtCore.QRegExp('[A-Za-z0-9_]+')

    def __init__(self, session, asset_type, parent=None):
        super(AssetComboBox, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.setEditable(True)

        self.session = session
        self.asset_type = asset_type

        validator = QtGui.QRegExpValidator(self.valid_asset_name)
        self.setValidator(validator)

        self.post_build()

    def post_build(self):
        self.context_changed.connect(self._on_context_changed)

    def _on_context_changed(self, context):
        self.clear()
        assets = self.session.query(
            'select name, versions.task.id , type.id '
            'from Asset where versions.task.id is {} and type.id is {}'.format(
                context['id'], self.asset_type['id'])
        ).all()
        for asset in assets:
            self.addItem(asset['name'], asset['id'])


class AssetSelector(QtWidgets.QWidget):

    asset_changed = QtCore.Signal(object, object)

    def __init__(self, session, asset_type, parent=None):
        super(AssetSelector, self).__init__(parent=parent)
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.info('init asset selector with : {}'.format(asset_type))

        self.session = session
        self.asset_type = asset_type

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(main_layout)

    def build(self):
        self.asset_name_label = QtWidgets.QLabel("Asset Name")
        self.asset_combobox = AssetComboBox(self.session, self.asset_type)
        self.layout().addWidget(self.asset_name_label)
        self.layout().addWidget(self.asset_combobox)

    def post_build(self):
        self.asset_combobox.currentIndexChanged.connect(
            self._current_asset_changed
        )
        self.asset_combobox.editTextChanged.connect(self._current_asset_changed)

    def _current_asset_changed(self, index):
        asset_name = self.asset_combobox.currentText()
        current_idx = self.asset_combobox.currentIndex()
        asset_id = self.asset_combobox.itemData(current_idx)
        self.asset_changed.emit(asset_name, asset_id)

    def set_context(self, context):
        self.logger.info('setting context to :{}'.format(context))
        self.asset_combobox.context_changed.emit(context)
