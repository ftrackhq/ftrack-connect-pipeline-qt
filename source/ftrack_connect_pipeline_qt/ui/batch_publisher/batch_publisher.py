# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import json
from functools import partial


from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.base.accordion_base import (
    AccordionBaseWidget,
)


class BatchPublisherWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(BatchPublisherWidget, self).__init__(parent=parent)

    def pre_build(self):
        '''Create objects widget.'''
        self._widget = QtWidgets.QWidget()
        self._widget.setLayout(QtWidgets.QVBoxLayout())
        self._widget.layout().setAlignment(QtCore.Qt.AlignTop)
        self._widget.layout().setSpacing(0)
        self._widget.layout().setContentsMargins(0, 0, 0, 0)

    def build(self):
        '''Build widget.'''
        self._widget.layout().addWidget(QtWidgets.QLabel(), 100)

    def post_build(self):
        '''Build widget.'''
        pass
