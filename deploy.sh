#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_ID="me-sb-dgcp-dpoc-pocyosh-pr"
IMAGE_NAME="gcr.io/${PROJECT_ID}/mcp-server"
TAG="latest"

# Build the Docker image with platform specification and no cache
echo "Building Docker image..."
docker build --platform linux/amd64 --no-cache -t ${IMAGE_NAME}:${TAG} .

# Push the image to Google Container Registry
echo "Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:${TAG}

echo "Deployment completed successfully!" 