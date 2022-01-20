from ftrack_connect_pipeline_qt.ui.client import default as default_widgets
from ftrack_connect_pipeline_qt.ui.client import overrides as override_widgets
from ftrack_connect_pipeline import constants as core_constants

UI_OVERRIDES = {
    'progress_widget': default_widgets.ProgressWidget,
    'main_widget': default_widgets.DefaultMainWidget,
    core_constants.CONTEXTS: {
        'step_container': default_widgets.DefaultStepContainerWidget,
        'step_widget': None,
        'stage_widget': default_widgets.DefaultStageWidget,
        'plugin_container': None,
    },
    core_constants.COMPONENTS: {
        'step_container': default_widgets.DefaultStepContainerWidget,
        'step_container.loader': override_widgets.RadioButtonStepContainerWidget,
        'step_widget.loader': override_widgets.RadioButtonItemStepWidget,
        'step_widget.publisher': override_widgets.AccordionStepWidget,
        'stage_widget': default_widgets.DefaultStageWidget,
        # Example to override specific stage widget
        # 'stage_widget.collector': default_widgets.DefaultStageWidget,
        'plugin_container': default_widgets.DefaultPluginContainerWidget,
        # We are saying that all the plugins of type validator will not have a plugin container
        'plugin_container.validator': None,
        'plugin_container.output': None,
        # Example to override specific plugin container
        # 'plugin_container.collect from given path': default_widgets.DefaultPluginContainerWidget,
    },
    core_constants.FINALIZERS: {
        'show': True,
        #'step_container': override_widgets.TabStepContainerWidget,
        'step_container': default_widgets.DefaultStepContainerWidget,
        'step_widget': default_widgets.DefaultStepWidget,
        #'stage_widget': override_widgets.GroupBoxStageWidget,
        'stage_widget': default_widgets.DefaultStageWidget,
        'plugin_container': override_widgets.AccordionPluginContainerWidget,
    },
}
