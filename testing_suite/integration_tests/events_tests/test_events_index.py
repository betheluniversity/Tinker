from testing_suite.integration_tests import IntegrationTestCase


class IndexTestCase(IntegrationTestCase):

    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(IndexTestCase, self).__init__(methodName)
        self.request_type = "GET"
        self.request = self.generate_url("index")

    #######################
    ### Testing methods ###
    #######################

    def test_index(self):
        expected_response = b'All events will be reviewed and approved within 2-3 business days by Conference'
        response = self.send_get(self.request)
        failure_message = self.generate_failure_message(self.request_type, self.request, response.data,
                                                        expected_response, self.class_name, self.get_line_number())
        self.assertIn(expected_response, response.data, msg=failure_message)
