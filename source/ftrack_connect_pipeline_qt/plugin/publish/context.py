# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt.plugin import base


class PublisherContextWidget(base.BaseContextWidget):
    plugin_type = constants.PLUGIN_PUBLISHER_CONTEXT_TYPE


