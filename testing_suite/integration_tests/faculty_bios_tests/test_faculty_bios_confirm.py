from testing_suite.integration_tests import IntegrationTestCase


class ConfirmTestCase(IntegrationTestCase):

    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(ConfirmTestCase, self).__init__(methodName)
        self.request_type = "GET"
        self.request = self.generate_url("confirm")

    #######################
    ### Testing methods ###
    #######################

    def test_confirm(self):
        expected_response = repr('\xd8;\xad\xec\xd2\xd1\xe8\x93\x04\xf7\xbbqX\x82\xd0\x0e')
        # b'<h1 class="first-subtitle">Congrats!</h1>'
        response = self.send_get(self.request)
        short_string = self.get_unique_short_string(response.data)
        failure_message = self.generate_failure_message(self.request_type, self.request, response.data,
                                                        expected_response, self.class_name, self.get_line_number())
        self.assertEqual(expected_response, short_string, msg=failure_message)
