# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt.plugin import base


class PublisherValidatorPluginWidget(base.BaseValidatorPluginWidget):
    plugin_type = core_constants.PLUGIN_PUBLISHER_VALIDATOR_TYPE
