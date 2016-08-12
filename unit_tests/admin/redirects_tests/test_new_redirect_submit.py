from redirects_Base import RedirectsBaseTestCase


class NewRedirectSubmitTestCase(RedirectsBaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    def create_new_form_submission(self, from_path, to_url):
        csrf_token = super(NewRedirectSubmitTestCase, self).get_csrf_token('/admin/redirect')
        return {
            'csrf_token': csrf_token,
            'new-redirect-from': from_path,
            'new-redirect-to': to_url,
            'short-url': "on",
            'expiration-date': "Fri Jul 01 2016"
        }

    #######################
    ### Testing methods ###
    #######################

    def test_new_redirect_submit_valid(self):
        form_contents = self.create_new_form_submission("from?", "to!")
        response = super(NewRedirectSubmitTestCase, self).send_post('/admin/redirect/new-redirect-submit', form_contents)
        assert b'<Redirect /from? to to!>' in response.data
        # add an assertion that it got added to the database

    def test_new_redirect_submit_invalid_from(self):
        form_contents = self.create_new_form_submission(None, "to!")
        response = super(NewRedirectSubmitTestCase, self).send_post('/admin/redirect/new-redirect-submit', form_contents)
        assert b'400 Bad Request' in response.data

    def test_new_redirect_submit_invalid_to(self):
        form_contents = self.create_new_form_submission("from?", None)
        response = super(NewRedirectSubmitTestCase, self).send_post('/admin/redirect/new-redirect-submit', form_contents)
        assert b'400 Bad Request' in response.data