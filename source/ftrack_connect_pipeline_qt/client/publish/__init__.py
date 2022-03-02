#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client import QtClient


class QtPublisherClient(QtClient):
    '''
    Base publish widget class.
    '''

    definition_filter = 'publisher'
    client_name = 'publish'

    def __init__(self, event_manager, parent_window, parent=None):

        super(QtPublisherClient, self).__init__(
            event_manager, parent_window, parent=parent
        )
        self.setWindowTitle('Standalone Pipeline Publisher')
        self.logger.debug('start qt publisher')

    def pre_build(self):
        '''
        .. note::
            We want to hidde the finalizers on the publisher but not on
            the loader, so we extend the schema_name_mapping dictionary.
        '''
        super(QtPublisherClient, self).pre_build()
