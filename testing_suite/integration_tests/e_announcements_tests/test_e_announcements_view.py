from testing_suite.integration_tests import IntegrationTestCase


class ViewTestCase(IntegrationTestCase):

    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(ViewTestCase, self).__init__(methodName)
        self.request_type = "GET"
        self.request = ""

    #######################
    ### Testing methods ###
    #######################

    def test_view(self):
        # The id may need to get changed someday if this e-announcement gets deleted
        id_to_test = "12f336eb8c58651305d79299154d15ff"
        self.request = self.generate_url("view", e_announcement_id=id_to_test)
        expected_response = repr('{\x03\x10\xa9\x8a\x91\x8c\xe4B\x84g^r`\x8e\xcd')  # b'<h5>First Date</h5>'
        response = self.send_get(self.request)
        short_string = self.get_unique_short_string(response.data)
        failure_message = self.generate_failure_message(self.request_type, self.request, response.data,
                                                        expected_response, self.class_name, self.get_line_number())
        self.assertEqual(expected_response, short_string, msg=failure_message)
