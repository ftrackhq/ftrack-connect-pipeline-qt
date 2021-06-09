# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack
import os

import ftrack_api
import logging
from Qt import QtWidgets, QtCore

import ftrack_connect.ui.application
import ftrack_connect.ui.widget.overlay
import ftrack_connect.ui.widget.actions

from ftrack_connect_pipeline import host, constants, event
from ftrack_connect_pipeline_qt.client import asset_manager, log_viewer, publish, load

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)



logger = logging.getLogger('ftrack-connect-pipeline-qt.pipeline-publisher-plugin')


class StandalonePublisherClient(QtPublisherClient):

    def __init__(self, parent=None):
        session = ftrack_api.Session(auto_connect_event_hub=False)
        event_manager = event.QEventManager(
            session=session, mode=constants.LOCAL_EVENT_MODE
        )
        self.current_host = host.Host(event_manager)
        super(StandalonePublisherClient, self).__init__(
            event_manager, parent=parent
        )


class PipelinePublisher(ftrack_connect.ui.application.ConnectWidget):

    def __init__(self, session, parent=None):
        '''Instantiate the actions widget.'''
        super(Launch, self).__init__(session, parent=parent)
        self.publisher_client = StandalonePublisherClient(parent=parent)
        self.layout().addWidget(self.publisher_client)



def register(session, **kw):
    '''Register plugin. Called when used as an plugin.'''
    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(session, ftrack_api.session.Session):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack_api.Session instance.'.format(session)
        )
        return

    plugin = ftrack_connect.ui.application.ConnectWidgetPlugin(PipelinePublisher)
    logger.info('registering {}'.format(plugin))
    plugin.register(session, priority=10)
