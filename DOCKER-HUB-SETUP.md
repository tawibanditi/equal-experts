# Docker Hub CI/CD Setup Guide

## Overview
This GitHub Actions workflow automatically tests, builds, and pushes the gist-server Docker image to Docker Hub on every push to `main` or `solution` branches.

## Required Secrets Setup

### 1. Create Docker Hub Access Token
1. Log in to [Docker Hub](https://hub.docker.com)
2. Go to **Account Settings** → **Security** → **Access Tokens**
3. Click **New Access Token**
4. Name: `GitHub Actions CI`
5. Permissions: **Read, Write, Delete**
6. Copy the generated token (save it securely)

### 2. Add GitHub Repository Secrets
1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

   **DOCKERHUB_USERNAME**
   ```
   your-dockerhub-username
   ```
   
   **DOCKERHUB_TOKEN**
   ```
   dckr_pat_your-token-here
   ```

## Workflow Features

### Jobs Overview:
1. **test** - Runs Python unit tests and server functionality test
2. **build-and-push** - Builds multi-architecture Docker image and pushes to Docker Hub
3. **security-scan** - Scans the pushed image for vulnerabilities

### Image Tags Generated:
- `latest` - Only for main/default branch
- `solution-abc123...` - Branch name with commit SHA
- `main-abc123...` - Branch name with commit SHA

### Security Features:
- Docker Hub authentication using access tokens (not passwords)
- Multi-architecture builds (AMD64 + ARM64)
- Vulnerability scanning with Trivy
- Build caching for faster builds
- Only pushes on actual commits (not pull requests)

## Docker Hub Repository
Your images will be available at:
```
https://hub.docker.com/r/YOUR_USERNAME/gist-server
```

Pull commands:
```bash
# Latest version
docker pull YOUR_USERNAME/gist-server:latest

# Specific commit
docker pull YOUR_USERNAME/gist-server:main-abc123...
```

## Testing Locally Before Push

### Test the Docker build:
```bash
cd gist-server
docker build -t gist-server-test .
docker run -p 8080:8080 gist-server-test
```

### Test endpoints:
```bash
curl http://localhost:8080/octocat
curl http://localhost:8080/nonexistent  # Should return 404
```

## Workflow Triggers
- **Push** to `main` or `solution`: Runs all jobs including build/push
- **Pull Request**: Runs only tests (no building/pushing to registry)

## Troubleshooting

### Common Issues:

**Authentication Failed:**
- Verify DOCKERHUB_USERNAME matches your Docker Hub username exactly
- Regenerate DOCKERHUB_TOKEN if it expired
- Ensure token has write permissions

**Build Failed:**
- Check Dockerfile syntax in `gist-server/` directory
- Verify all files are committed and pushed

**Tests Failed:**
- Run tests locally: `python -m unittest test_server.py -v`
- Check if server.py has any syntax errors

### Debug Steps:
1. Check **Actions** tab in GitHub repository
2. Click on failed workflow run
3. Expand failed job to see detailed logs
4. Look for specific error messages

## Security Best Practices
✅ Using access tokens instead of passwords  
✅ Limited token permissions (Read, Write, Delete only)  
✅ Secrets stored securely in GitHub  
✅ Vulnerability scanning enabled  
✅ Multi-architecture builds  
✅ Build caching for efficiency

## Next Steps
After secret setup is complete:
```bash
git add .github/
git commit -m "Add Docker Hub CI/CD pipeline"
git push
```

The workflow will trigger automatically and you can monitor progress in the Actions tab.