from events_base import EventsBaseTestCase

class EventInWorkflowTestCase(EventsBaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    #######################
    ### Testing methods ###
    #######################

    def test_event_in_workflow(self):
        response = self.send_get("/events/event_in_workflow")
        assert b'Edits pending approval' in response.data