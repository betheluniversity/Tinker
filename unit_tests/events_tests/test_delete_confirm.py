from . import EventsBaseTestCase

class DeleteConfirmTestCase(EventsBaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    #######################
    ### Testing methods ###
    #######################

    def test_delete_confirm(self):
        response = self.send_get("/event/delete_confirm")
        assert b'Your event has been deleted.' in response.data