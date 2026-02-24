from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.request
import urllib.error

class GistHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Path must be exactly /<username>
        parts = self.path.strip('/').split('/')
        if len(parts) != 1 or not parts[0]:
            self.send_error(404, "Not Found")
            return
        
        username = parts[0]
        try:
            url = f'https://api.github.com/users/{username}/gists'
            req = urllib.request.Request(url, headers={"User-Agent": "gist-server/1.0"})
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

        except urllib.error.HTTPError as e:
            self.send_error(e.code, e.reason)
        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), GistHandler)
    print("Listening on port 8080...")
    server.serve_forever()
