# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline.constants import asset as asset_constants

from Qt import QtCore
from ftrack_connect_pipeline.asset import FtrackAssetBase


class QFtrackAsset(FtrackAssetBase, QtCore.QObject):
    '''
    Base QFtrackAsset class.
    '''

    @property
    def id(self):
        asset_id = self.asset_info[asset_constants.ASSET_ID]
        version_id = self.asset_info[asset_constants.VERSION_ID]
        component_id = self.asset_info[asset_constants.COMPONENT_ID]
        return hash(asset_id+version_id+component_id)

    def __init__(self, event_manager):
        '''
        Initialize QFtrackAsset with *event_manager*.
        '''
        super(QFtrackAsset, self).__init__(event_manager)

