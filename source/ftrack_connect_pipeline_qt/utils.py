# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import threading
import sys
import logging

from Qt import QtCore, QtWidgets

class Worker(QtCore.QThread):
    '''Perform work in a background thread.'''

    def __init__(self, function, args=None, kwargs=None, parent=None):
        '''Execute *function* in separate thread.

        *args* should be a list of positional arguments and *kwargs* a
        mapping of keyword arguments to pass to the function on execution.

        Store function call as self.result. If an exception occurs
        store as self.error.

        Example::

            try:
                worker = Worker(theQuestion, [42])
                worker.start()

                while worker.isRunning():
                    app = QtGui.QApplication.instance()
                    app.processEvents()

                if worker.error:
                    raise worker.error[1], None, worker.error[2]

            except Exception as error:
                traceback.print_exc()
                QtGui.QMessageBox.critical(
                    None,
                    'Error',
                    'An unhandled error occurred:'
                    '\\n{0}'.format(error)
                )

        '''
        super(Worker, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self.result = None
        self.error = None

    def run(self):
        '''Execute function and store result.'''
        try:
            self.result = self.function(*self.args, **self.kwargs)
        except Exception as error:
            self.logger.error(str(error))
            self.error = sys.exc_info()


def asynchronous(method):
    '''Decorator to make a method asynchronous using its own thread.'''

    def wrapper(*args, **kwargs):
        '''Thread wrapped method.'''

        def exceptHookWrapper(*args, **kwargs):
            '''Wrapp method and pass exceptions to global excepthook.

            This is needed in threads because of
            https://sourceforge.net/tracker/?func=detail&atid=105470&aid=1230540&group_id=5470
            '''
            try:
                method(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info())

        thread = threading.Thread(
            target=exceptHookWrapper,
            args=args,
            kwargs=kwargs
        )
        thread.start()

    return wrapper


class BaseThread(threading.Thread):
    def __init__(self, callback=None, target_args=None, *args, **kwargs):
        target = kwargs.pop('target')
        super(BaseThread, self).__init__(target=self.target_with_callback, *args, **kwargs)
        self.callback = callback
        self.method = target
        self.target_args = target_args

    def target_with_callback(self):
        result = self.method(*self.target_args)
        if self.callback is not None:
            self.callback(result)


def get_main_framework_window_from_widget(widget):
    '''This function will return the main window of the framework from the
    given *widget*. The main window is named as main_framework_widget'''
    main_window = widget.window()
    if not main_window:
        return

    if not main_window.objectName() == "main_framework_widget":
        main_window = main_window.findChild(
            QtWidgets.QWidget, "main_framework_widget"
        )

    return main_window