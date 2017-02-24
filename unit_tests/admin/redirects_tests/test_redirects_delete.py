from redirects_base import RedirectsBaseTestCase


class DeleteTestCase(RedirectsBaseTestCase):

    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(DeleteTestCase, self).__init__(methodName)
        self.request_type = "POST"
        self.request = self.generate_url("delete_redirect")

    def create_form(self, from_path="/from?"):
        return {
            'from_path': from_path
        }

    #######################
    ### Testing methods ###
    #######################

    def test_delete_valid(self):
        # Create a row that can then be deleted immediately
        self.send_post(self.generate_url("new_redirect_submit"), {
            'new-redirect-from': "/from?",
            'new-redirect-to': "to!",
            'short-url': "on",
            'expiration-date': "Fri Jul 01 2016"
        })
        expected_response = b'deleted done'
        form_contents = self.create_form("/from?")
        response = self.send_post(self.request, form_contents)
        failure_message = self.generate_failure_message(self.request_type, self.request, response.data,
                                                        expected_response, self.class_name, self.get_line_number())
        self.assertIn(expected_response, response.data, msg=failure_message)

    def test_delete_invalid_path(self):
        expected_response = b'fail'
        form_contents = self.create_form("/gibberish_url")
        response = self.send_post(self.request, form_contents)
        failure_message = self.generate_failure_message(self.request_type, self.request, response.data,
                                                        expected_response, self.class_name, self.get_line_number())
        self.assertIn(expected_response, response.data, msg=failure_message)