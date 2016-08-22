from sync_base import SyncBaseTestCase


class DataDefinitionTestCase(SyncBaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(DataDefinitionTestCase, self).__init__(methodName)
        self.class_name = self.__class__.__bases__[0].__name__ + '/' + self.__class__.__name__

    def create_form(self, id):
        return {
            'id': id
        }

    #######################
    ### Testing methods ###
    #######################

    def test_datadefinition(self):
        failure_message = 'Sending a valid submission to "POST /admin/sync/datadefinition" didn\'t succeed as expected by ' + self.class_name + '.'
        expected_response = b'<h3>Successfully Synced'
        form_contents = self.create_form("yes")
        response = super(DataDefinitionTestCase, self).send_post("/admin/sync/datadefinition", form_contents)
        self.assertIn(expected_response, response.data, msg=failure_message)