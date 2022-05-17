# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import platform

from functools import partial

from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt.ui.utility.widget.button import (
    DenyButton,
    ApproveButton,
)
from ftrack_connect_pipeline_qt.utils import get_theme, set_theme
from ftrack_connect_pipeline_qt.utils import center_widget
from ftrack_connect_pipeline_qt.ui import theme


class Dialog(QtWidgets.QDialog):
    '''
    A basic dialog window, intended to live on top of DCC app main window.
    Supports to be shaded when a modal dialog is put in front.
    '''

    @property
    def darken(self):
        return self._darken

    @darken.setter
    def darken(self, value):
        self._darken = value
        if self._darken:
            self._overlay_widget = OverlayWidget(self)
            self._overlay_widget.move(0, 0)
            self._overlay_widget.resize(self.size())
            self._overlay_widget.show()
        else:
            if self._overlay_widget:
                self._overlay_widget.close()

    def __init__(self, parent):
        super(Dialog, self).__init__(parent=parent)
        self._overlay_widget = None


class OverlayWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(OverlayWidget, self).__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self._fill_color = QtGui.QColor(19, 25, 32, 169)

    def paintEvent(self, event):
        super(OverlayWidget, self).paintEvent(event)
        # Get current window size and paint a semi transparent dark overlay across widget
        size = self.size()
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(self._fill_color)
        painter.setBrush(self._fill_color)
        painter.drawRect(0, 0, size.width(), size.height())
        painter.end()


class ModalDialog(QtWidgets.QDialog):
    '''
    A styled modal ftrack dialog box, intended to live on top of a base dialog.
    Behaviour defaults to a prompt (Yes-No) dialog.
    '''

    def __init__(
        self,
        parent,
        message=None,
        question=None,
        title=None,
        prompt=False,
        on_top=False,
        modal=False,
    ):
        super(ModalDialog, self).__init__(parent=parent)

        self.setParent(parent)

        self.setWindowFlags(QtCore.Qt.Tool)
        set_theme(self, get_theme())
        if self.get_theme_background_style():
            self.setProperty('background', self.get_theme_background_style())

        self._message = message or question
        self._title = title or 'ftrack'
        self._prompt = prompt

        self.pre_build()
        self.build()
        self.post_build()

        self.setModal(modal)
        self.setWindowFlags(
            QtCore.Qt.SplashScreen
            | (QtCore.Qt.WindowStaysOnTopHint if on_top else 0)
        )

        if prompt is False:
            self.exec_()

    def get_theme_background_style(self):
        return 'ftrack'

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        '''Can be overridden by custom dialogs.'''

        self._title_label = TitleLabel()
        self._title_label.setAlignment(QtCore.Qt.AlignCenter)
        self._title_label.setObjectName('titlebar')
        self.layout().addWidget(self._title_label)
        self._title_label.setMinimumHeight(24)

        self.layout().setSpacing(5)

        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())

        widget.layout().addWidget(self.get_content_widget())

        self.layout().addWidget(widget, 100)

        buttonbar = QtWidgets.QWidget()
        buttonbar.setLayout(QtWidgets.QHBoxLayout())
        buttonbar.layout().setContentsMargins(10, 1, 10, 1)
        buttonbar.layout().setSpacing(10)

        buttonbar.layout().addWidget(QtWidgets.QLabel(), 100)
        self._approve_button = self.get_approve_button()
        if not self._prompt is False:
            self._deny_button = self.get_deny_button()
        else:
            self._deny_button = None
        if platform.system().lower() != 'darwin':
            if self._approve_button:
                buttonbar.layout().addWidget(self._approve_button)
            if self._deny_button:
                buttonbar.layout().addWidget(self._deny_button)
        else:
            if self._deny_button:
                buttonbar.layout().addWidget(self._deny_button)
            if self._approve_button:
                buttonbar.layout().addWidget(self._approve_button)

        self.layout().addWidget(buttonbar, 1)

    def get_content_widget(self):
        label = QtWidgets.QLabel(self._message)
        label.setObjectName('h3')
        return center_widget(label)

    def get_approve_button(self):
        return ApproveButton('YES' if self._prompt is True else 'OK')

    def get_deny_button(self):
        return DenyButton('NO')

    def post_build(self):
        if self._approve_button:
            self._approve_button.clicked.connect(partial(self.done, 1))
        if self._deny_button:
            self._deny_button.clicked.connect(self.reject)

        self.setWindowTitle(self.get_title())
        self.resize(250, 100)
        if not self._prompt is None:
            self.setMaximumHeight(100)

    def get_title(self):
        return self._title

    def setWindowTitle(self, title):
        super(ModalDialog, self).setWindowTitle(title)
        self._title_label.setText(title.upper())

    def setVisible(self, visible):
        if isinstance(self.parentWidget(), Dialog):
            self.parentWidget().darken = visible
        super(ModalDialog, self).setVisible(visible)


class TitleLabel(QtWidgets.QLabel):
    def __init__(self, label="", parent=None):
        super(TitleLabel, self).__init__(label, parent=parent)
