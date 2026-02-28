#!/bin/bash

# Docker deployment script for Redmine MCP Server
# This script builds and deploys the Docker container using docker compose

set -e  # Exit on error

echo "🐳 Redmine MCP Server Docker Deployment"
echo "========================================"

# Configuration
CONTAINER_NAME="redmine-mcp-server"
IMAGE_NAME="redmine-mcp"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to check if .env.docker file exists
check_env_file() {
    if [ ! -f .env.docker ]; then
        echo "❌ .env.docker file not found"
        echo "📋 Creating .env.docker from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env.docker
            echo "⚠️  Please edit .env.docker with your Redmine configuration before running again"
            exit 1
        else
            echo "❌ .env.example not found. Please create .env.docker manually"
            exit 1
        fi
    fi
    echo "✅ .env.docker file found"
}

# Function to build Docker image with force rebuild option
build_image() {
    local force_rebuild=$1
    
    if [ "$force_rebuild" = true ]; then
        echo "🔨 Force building Docker image (no cache)..."
        docker compose build --no-cache --force-rm redmine-mcp-server
    else
        echo "🔨 Building Docker image..."
        docker compose build redmine-mcp-server
    fi
    echo "✅ Docker image built successfully"
}

# Function to stop and remove existing container
cleanup_container() {
    echo "🛑 Stopping existing services..."
    docker compose down --remove-orphans
    
    # Force remove old container if it still exists
    if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
        echo "🗑️  Force removing old container..."
        docker rm -f $CONTAINER_NAME 2>/dev/null || true
    fi
}

# Function to run the container
run_container() {
    echo "🚀 Starting services..."
    docker compose up -d
    
    echo "✅ Services started successfully"
    echo "📊 Container status:"
    docker compose ps
}

# Function to show logs
show_logs() {
    echo "📋 Container logs (last 20 lines):"
    echo "--------------------------------"
    docker compose logs --tail=20 redmine-mcp-server
    echo "--------------------------------"
    echo "💡 To follow logs: docker compose logs -f redmine-mcp-server"
}

# Function to test the deployment
test_deployment() {
    echo "🧪 Testing deployment..."
    sleep 10  # Wait for container to start

    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
        echo "📊 Health response:"
        curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
    else
        echo "⚠️  Health check failed - checking if server is starting..."
        sleep 10
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            echo "✅ Health check passed (after delay)"
        else
            echo "❌ Health check failed"
            echo "🔍 Container logs:"
            docker compose logs --tail=20 redmine-mcp-server
        fi
    fi
}

# Function to display usage information
show_usage() {
    cat << EOF
🐳 Redmine MCP Server Docker Deployment Script

Usage: \$0 [OPTIONS]

Options:
    --build-only       Build the Docker image only
    --force-rebuild    Force rebuild without cache
    --no-test          Skip deployment testing
    --cleanup          Stop and remove services
    --logs             Show container logs
    --status           Show container status
    --help             Show this help message

Examples:
    \$0                  # Full deployment (build + run + test)
    \$0 --build-only     # Build image only
    \$0 --force-rebuild  # Force rebuild with no cache
    \$0 --cleanup        # Clean up existing deployment
    \$0 --logs           # Show current container logs
    \$0 --status         # Show container status

Services will be available at:
    Server: http://localhost:8000
    Health: http://localhost:8000/health
    MCP:    http://localhost:8000/mcp

EOF
}

# Parse command line arguments
BUILD_ONLY=false
NO_TEST=false
CLEANUP_ONLY=false
LOGS_ONLY=false
STATUS_ONLY=false
FORCE_REBUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        --no-test)
            NO_TEST=true
            shift
            ;;
        --cleanup)
            CLEANUP_ONLY=true
            shift
            ;;
        --logs)
            LOGS_ONLY=true
            shift
            ;;
        --status)
            STATUS_ONLY=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution flow
main() {
    check_docker

    if [ "$LOGS_ONLY" = true ]; then
        show_logs
        exit 0
    fi

    if [ "$STATUS_ONLY" = true ]; then
        echo "📊 Container status:"
        docker compose ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        exit 0
    fi

    if [ "$CLEANUP_ONLY" = true ]; then
        cleanup_container
        echo "✅ Cleanup completed"
        exit 0
    fi

    check_env_file
    build_image $FORCE_REBUILD

    if [ "$BUILD_ONLY" = true ]; then
        echo "✅ Build completed. Image: $IMAGE_NAME:latest"
        exit 0
    fi

    cleanup_container
    run_container

    if [ "$NO_TEST" = false ]; then
        test_deployment
    fi

    echo ""
    echo "🎉 Deployment completed!"
    echo "🌐 Server URL: http://localhost:8000"
    echo "🔗 MCP Endpoint: http://localhost:8000/mcp"
    echo "📋 View logs: docker compose logs -f redmine-mcp-server"
    echo "🛑 Stop services: docker compose down"
}

# Run main function
main "$@"
