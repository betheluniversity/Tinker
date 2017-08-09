from sqlalchemy.exc import IntegrityError

from redirects_controller_base import RedirectsControllerBaseTestCase
from tinker.admin.redirects.models import BethelRedirect


class APIAddRowTestCase(RedirectsControllerBaseTestCase):
    #######################
    ### Utility methods ###
    #######################

    def __init__(self, methodName):
        super(APIAddRowTestCase, self).__init__(methodName)

    #######################
    ### Testing methods ###
    #######################

    def test_api_add_row_valid(self):
        from_path = "/from?"
        to_url = "to!"
        response = self.controller.api_add_row(from_path, to_url)
        self.assertTrue(isinstance(response, BethelRedirect))
        self.assertEqual(str(response), '<Redirect %(0)s to %(1)s>' % {'0': from_path, '1': to_url})
        query_results = self.controller.search_db('from_path', from_path)
        self.assertTrue(isinstance(query_results, list))
        self.assertEqual(len(query_results), 1)
        self.assertEqual(response, query_results[0])
        self.controller.delete_row_from_db(from_path)

    def test_api_add_row_invalid(self):
        invalid_args = {
            'from_path': None,
            'to_url': "to!"
        }
        # Because we have to rollback the DB after this exception, I can't use self.assertRaises
        integrity_error_caught = False
        try:
            self.controller.api_add_row(**invalid_args)
        except IntegrityError:
            integrity_error_caught = True
            self.controller.rollback()

        self.assertTrue(integrity_error_caught)
