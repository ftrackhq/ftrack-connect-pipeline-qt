# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
from ftrack_connect_pipeline import constants

#: Default ui type for ftrack_connect_pipeline_qt
UI_TYPE = 'qt'
#: Default host type for ftrack_connect_pipeline_qt
HOST_TYPE = constants.HOST_TYPE

#: UI Not set value for UI overrides
NOT_SET = 'widget_not_set'

#: Base name for events
_BASE_ = 'ftrack.pipeline'

MAIN_FRAMEWORK_WIDGET = 'main_framework_widget'

PIPELINE_WIDGET_LAUNCH = '{}.client.launch'.format(_BASE_)

# Avoid circular dependencies.
from ftrack_connect_pipeline_qt.constants.icons import *
