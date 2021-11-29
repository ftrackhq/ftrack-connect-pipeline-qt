import sys
import os
import logging

from Qt import QtWidgets

logger = logging.getLogger(__name__)

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)


if __name__ == '__main__':

    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    import ftrack_api
    from ftrack_connect_pipeline import constants, host
    from ftrack_connect_pipeline_qt import event

    from ftrack_connect_pipeline_qt.client.load import QtLoaderClient


    class StandaloneLoaderClient(QtLoaderClient):

        def __init__(self, parent=None):
            session = ftrack_api.Session(auto_connect_event_hub=False)
            event_manager = event.QEventManager(
                session=session, mode=constants.LOCAL_EVENT_MODE
            )
            self.current_host = host.Host(event_manager)
            super(StandaloneLoaderClient, self).__init__(
                event_manager, parent=parent
            )

    wid = StandaloneLoaderClient()
    wid.show()
    sys.exit(app.exec_())
