from unit_tests import BaseTestCase


class IndexTestCase(BaseTestCase):
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
        expected_response = repr('\xd2l\xab{t\x00\xd1\x9f\xc2\x0c\x00>\xb2\xc9pu')
        # b'<form id="blink-login" action="https://blink.bethel.edu/cp/home/login" method="post">'
        response = self.send_get(self.request)
        short_string = self.get_unique_short_string(response.data)
        failure_message = self.generate_failure_message(self.request_type, self.request, response.data,
                                                        expected_response, self.class_name, self.get_line_number())
        # self.assertIn(expected_response, response.data, msg=failure_message)

        self.assertEqual(expected_response, short_string, msg=failure_message)
