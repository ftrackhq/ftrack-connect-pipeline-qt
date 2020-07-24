# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from ftrack_connect_pipeline import constants


UI = 'qt'
HOST = constants.HOST

# Base name.
_BASE_ = 'ftrack.pipeline'

PIPELINE_UPDATE_UI = '{}.QtClient.update'.format(_BASE_)

# Avoid circular dependencies.
from ftrack_connect_pipeline_qt.constants.icons import *
