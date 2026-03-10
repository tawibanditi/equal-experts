import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer
from unittest.mock import patch, MagicMock

from server import GistHandler

# Fake GitHub API response — includes extra fields to verify the server filters them out
SAMPLE_GISTS = [
    {
        "id": "abc123",
        "description": "A sample gist",
        "html_url": "https://gist.github.com/octocat/abc123",
        "created_at": "2021-01-01T00:00:00Z",
        "updated_at": "2021-01-02T00:00:00Z",
        "url": "https://api.github.com/gists/abc123",       # extra — should be filtered
        "forks_url": "https://api.github.com/gists/abc123/forks",  # extra — should be filtered
    }
]

def _make_mock_response(data):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode('utf-8')
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp

def _urlopen_side_effect(req, timeout=None):
    url = req.full_url if hasattr(req, 'full_url') else req
    if 'thisuserdoesnotexist' in url:
        raise urllib.error.HTTPError(url, 404, 'Not Found', {}, None)
    return _make_mock_response(SAMPLE_GISTS)

class TestGistServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patcher = patch('server.urllib.request.urlopen', side_effect=_urlopen_side_effect)
        cls.patcher.start()

        cls.server = HTTPServer(("localhost", 0), GistHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever)
        cls.thread.daemon = True
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.patcher.stop()

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
        self.assertGreater(len(body), 0, "Expected at least one gist")
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

    def test_extra_github_fields_are_stripped(self):
        _, body = self.get("/octocat")
        for gist in body:
            self.assertNotIn("forks_url", gist)

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
