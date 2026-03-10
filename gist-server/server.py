from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import time
import urllib.request
import urllib.error

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests by status code',
    ['status_code']
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds'
)
GITHUB_API_ERRORS = Counter(
    'github_api_errors_total',
    'GitHub API errors by HTTP status code',
    ['error_code']
)

class GistHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            output = generate_latest()
            self.send_response(200)
            self.send_header('Content-Type', CONTENT_TYPE_LATEST)
            self.send_header('Content-Length', str(len(output)))
            self.end_headers()
            self.wfile.write(output)
            return

        start = time.time()
        status_code = 500

        try:
            # Path must be exactly /<username>
            parts = self.path.strip('/').split('/')
            if len(parts) != 1 or not parts[0]:
                status_code = 404
                self.send_error(404, "Not Found")
                return

            username = parts[0]
            url = f'https://api.github.com/users/{username}/gists'
            headers = {"User-Agent": "gist-server/1.0"}
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
               gists = json.loads(resp.read())

            results = [
                {
                    "id": gist['id'],
                    "description": gist['description'],
                    "url": gist['html_url'],
                    "created_at": gist['created_at'],
                    "updated_at": gist['updated_at']
                }
                for gist in gists
            ]

            body = json.dumps(results).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            status_code = 200

        except urllib.error.HTTPError as e:
            status_code = e.code
            GITHUB_API_ERRORS.labels(error_code=str(e.code)).inc()
            self.send_error(e.code, e.reason)
        except Exception as e:
            status_code = 500
            GITHUB_API_ERRORS.labels(error_code='500').inc()
            self.send_error(500, str(e))
        finally:
            REQUEST_DURATION.observe(time.time() - start)
            REQUEST_COUNT.labels(status_code=str(status_code)).inc()

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), GistHandler)
    print("Listening on port 8080...")
    server.serve_forever()
