from unit_tests import BaseTestCase


class AllTestCase(BaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(AllTestCase, self).__init__(methodName)
        self.class_name = self.__class__.__bases__[0].__name__ + '/' + self.__class__.__name__
        self.request = "POST /admin/sync/all"

    def create_form(self, id):
        return {
            'id': id
        }

    #######################
    ### Testing methods ###
    #######################

    def test_all(self):
        expected_response = b'<h3>Successfully Synced'
        form_contents = self.create_form("yes")
        response = self.send_post("/admin/sync/all", form_contents)
        failure_message = self.generate_failure_message(self.request, response.data, expected_response, self.class_name)
        self.assertIn(expected_response, response.data, msg=failure_message)