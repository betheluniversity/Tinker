from unit_tests import BaseTestCase


class PublishProgramFeedsReturnTestCase(BaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(PublishProgramFeedsReturnTestCase, self).__init__(methodName)

    #######################
    ### Testing methods ###
    #######################

    def test_publish_program_feeds_return(self):
        # destination = "staging"  # or "production"
        # failure_message = '"GET /admin/publish-manager/program-feeds/%s" didn\'t return the HTML code expected by ' % destination \
        #                   + self.class_name + '.'
        # expected_response = b'<h3>Publish Program Feeds</h3>'
        # response = super(PublishProgramFeedsReturnTestCase, self).send_get("/admin/publish-manager/program-feeds/" + destination)
        # self.assertIn(expected_response, response.data, msg=failure_message)
        pass