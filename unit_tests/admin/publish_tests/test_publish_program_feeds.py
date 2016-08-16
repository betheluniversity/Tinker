from publish_base import PublishBaseTestCase


class PublishProgramFeedsTestCase(PublishBaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    #######################
    ### Testing methods ###
    #######################

    def test_publish_program_feeds(self):
        response = super(PublishProgramFeedsTestCase, self).send_get("/admin/publish-manager/program-feeds")
        assert b'<h3>Publish Program Feeds</h3>' in response.data

        # <a href=\'/admin/publish-manager/program-feeds/staging\' class="button">Publish to Staging</a>\
        # <a href=\'/admin/publish-manager/program-feeds/production\' class="button">Publish to Production and Staging</a>' in response.data