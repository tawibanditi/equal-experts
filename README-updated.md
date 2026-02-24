#Gist Server
A simple HTTP server that returns a GitHub user's public gist

## Endpoints

GET /<username>

## Run locally

Requires Python 3.x. No dependencies to install

Using bash run the following command
python3 server.py
curl http://localhost:8080/octocat

## Run with Docker

Using bash run the following command
docker build -t gist-server .
docker run -p 8080:8080 gist-server
curl http://localhost:8080/octocat

## Run Tests

Using bash run the following command
python3 -m unittest test_server.py