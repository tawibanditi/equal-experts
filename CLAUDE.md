# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands are run from the `gist-server/` directory unless noted.

```bash
# Install dependencies (required before running locally)
pip install -r requirements.txt

# Run tests
python -m unittest test_server.py -v

# Run a single test
python -m unittest test_server.GistServerTest.<test_name> -v

# Start the server locally
python server.py

# Build Docker image
docker build -t gist-server .

# Run container
docker run -p 8080:8080 gist-server

# Smoke test
curl http://localhost:8080/octocat

# Check metrics
curl http://localhost:8080/metrics
```

There is no linter configured. Dependencies are in `gist-server/requirements.txt` (`prometheus_client`).

## Architecture

A single Python microservice (`gist-server/server.py`) that acts as a proxy/adapter to the GitHub Gists API. No framework — built entirely on Python's stdlib `http.server`.

**Request flow:**
```
Client → GET /<username> (port 8080)
       → gist-server fetches https://api.github.com/users/{username}/gists
       → transforms response to 5-field schema per gist: id, description, url, created_at, updated_at
       → returns JSON array
```

**Routing rules enforced in `do_GET`:**
- `GET /metrics` → served by `prometheus_client`, not counted in metrics
- Exactly one path segment required; `/`, `/user/extra`, etc. → 404
- GitHub 404 is propagated as 404; all other exceptions → 500

**Metrics (`prometheus_client`):** Three metrics are tracked via a `try/except/finally` wrapping the handler logic:
- `http_requests_total` (Counter, label: `status_code`) — every non-`/metrics` request
- `http_request_duration_seconds` (Histogram) — every non-`/metrics` request
- `github_api_errors_total` (Counter, label: `error_code`) — only on upstream GitHub API failures

**Observability stack:** `k8s/prometheus.yaml` deploys Prometheus to the `monitoring` namespace with pod-annotation-based discovery. Gist-server pods are annotated with `prometheus.io/scrape: "true"` so Prometheus scrapes them automatically. Prometheus UI is exposed via `LoadBalancer` on port 9090 (`http://localhost:9090` on Docker Desktop).

**Testing approach:** Tests in `test_server.py` spin up a real `HTTPServer` on a random port in a daemon thread (`setUpClass`) and make live HTTP calls against the actual GitHub API — there is no mocking. The `octocat` GitHub account is used as a stable fixture.

## CI/CD Pipeline

Defined in `.github/workflows/ci.yml`. Triggers on push/PR to `main`.

**Job 1: `test`** (GitHub-hosted `ubuntu-latest`)
- Runs unit tests then a smoke-test: starts server in background, waits 3s, curls `/octocat`

**Job 2: `build-and-deploy`** (self-hosted runner — requires local Docker Desktop)
- Builds Docker image tagged with `${{ github.sha }}` and `latest`
- Switches kubectl context to `docker-desktop` and deploys via `kubectl set image` + rollout wait

The self-hosted runner implies deployment targets a local Docker Desktop Kubernetes cluster. The `k8s/gist-server.yaml` manifest defines a `Deployment` (2 replicas, `imagePullPolicy: Never`) and a `LoadBalancer` Service on port 80 → 8080.

To deploy Prometheus (one-time setup):
```bash
kubectl apply -f k8s/prometheus.yaml
kubectl -n monitoring rollout status deployment/prometheus
```
