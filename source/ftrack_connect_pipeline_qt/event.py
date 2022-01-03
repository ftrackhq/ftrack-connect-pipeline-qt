
import ftrack_api
from ftrack_connect_pipeline.event import EventManager
from ftrack_connect_pipeline_qt import constants as qt_constants

class QEventManager(EventManager):
    
    def _wait(self):
        pass

    def launch_widget(self, host_id, widget_name, source=None):
        '''Send a widget launch event, to be picked up by DCC. '''
        event = ftrack_api.event.base.Event(
            topic=qt_constants.PIPELINE_WIDGET_LAUNCH,
            data={
                'pipeline': {
                    'host_id': host_id,
                    'widget_name': widget_name,
                    'source': source
                }
            }
        )
        self.publish(
            event,
        )
