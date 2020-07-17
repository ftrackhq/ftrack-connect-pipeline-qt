# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets, QtCore, QtGui


class VersionDelegate(QtWidgets.QItemDelegate):

    def __init__(self, parent=None):
        super(VersionDelegate, self).__init__(parent=parent)

    def createEditor(self, parent, option, index):

        item = index.model().data(index, index.model().DATA_ROLE)
        versions_collection = item.ftrack_versions

        combo = QtWidgets.QComboBox(parent)
        for asset_version in versions_collection:
            combo.addItem(str(asset_version['version']), asset_version['id'])

        return combo

    def setEditorData(self, editor, index):
        editor_data = str(index.model().data(index, QtCore.Qt.EditRole))
        idx = editor.findText(editor_data)
        editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        if not index.isValid():
            return False
        model.setData(
            index, editor.itemData(editor.currentIndex()), QtCore.Qt.EditRole
        )

