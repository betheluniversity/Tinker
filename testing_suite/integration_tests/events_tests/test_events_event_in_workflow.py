from testing_suite.integration_tests import IntegrationTestCase


class EventInWorkflowTestCase(IntegrationTestCase):

    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(EventInWorkflowTestCase, self).__init__(methodName)
        self.request_type = "GET"
        self.request = self.generate_url("event_in_workflow")

    #######################
    ### Testing methods ###
    #######################

    def test_event_in_workflow(self):
        expected_response = repr("\xd0u'r\xdew8+a\x0bh\x99\xf9\xe5\xf2I")  # b'Edits pending approval'
        response = self.send_get(self.request)
        short_string = self.get_unique_short_string(response.data)
        failure_message = self.generate_failure_message(self.request_type, self.request, response.data,
                                                        expected_response, self.class_name, self.get_line_number())
        self.assertEqual(expected_response, short_string, msg=failure_message)