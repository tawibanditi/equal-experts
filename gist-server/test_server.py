import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer

from server import GistHandler

class TestGistServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start server on a random free port
        cls.server = HTTPServer(("localhost", 0), GistHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()
    
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def get(self, path):
        url = f"http://localhost:{self.port}{path}"
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
        
    # -- happy path tests --

    def test_returns_200_for_valid_user(self):
        status, _ = self.get("/octocat")
        self.assertEqual(status, 200)
    
    def test_returns_list(self):
        _, body = self.get("/octocat")
        self.assertIsInstance(body, list)

    def test_gist_has_required_fields(self):
        _, body = self.get("/octocat")
        self.assertGreater(len(body), 0, "Expected at least one gist for octocat")
        for gist in body:
            self.assertIn("id", gist)
            self.assertIn("description", gist)
            self.assertIn("url", gist)
            self.assertIn("created_at", gist)
            self.assertIn("updated_at", gist)

    def test_url_field_is_github_link(self):
        _, body = self.get("/octocat")
        for gist in body:
            self.assertIn("gist.github.com", gist["url"])

    # -- error handling tests --

    def test_unknown_user_returns_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/thisuserdoesnotexist0000xyz")
        self.assertEqual(ctx.exception.code, 404)

    def test_subpath_returns_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/octocat/extra")
        self.assertEqual(ctx.exception.code, 404)

    def test_root_path_returns_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/")
        self.assertEqual(ctx.exception.code, 404)

if __name__ == "__main__":
    unittest.main(verbosity=2)