import tinker
import unittest


class ClearCacheBaseTestCase(unittest.TestCase):

    # This method is designed to set up a temporary database, such that the tests won't affect the real database
    def setUp(self):
        tinker.app.testing = True
        self.app = tinker.app.test_client()

    def send_post(self, url, form_contents):
        return self.app.post(url, data=form_contents, follow_redirects=True)

    def send_get(self, url):
        return self.app.get(url, follow_redirects=True)

    def get_csrf_token(self, url):
        import re
        response = self.send_get(url)
        # Returns 3rd parentheses group
        csrf_token = re.search('<input(.*)id="csrf_token"(.*)value="(.+)"(/?)>', response.data).group(3)
        return csrf_token

    # Corresponding to the setUp method, this method deletes the temporary database
    def tearDown(self):
        pass

if __name__ == "__main__":
    testsuite = unittest.TestLoader().discover('.')
    unittest.TextTestRunner(verbosity=1).run(testsuite)
