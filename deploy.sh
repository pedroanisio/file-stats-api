#!/bin/bash

# File Stats API Deployment Script
# This script helps deploy the File Stats API using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        if ! docker compose version &> /dev/null; then
            error "Docker Compose is not installed. Please install Docker Compose first."
        fi
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    success "Docker and Docker Compose are available"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    mkdir -p ./data
    mkdir -p ./logs
    success "Directories created"
}

# Build the Docker image
build_image() {
    log "Building Docker image..."
    $DOCKER_COMPOSE build --no-cache
    success "Docker image built successfully"
}

# Deploy the application
deploy() {
    log "Deploying File Stats API..."
    $DOCKER_COMPOSE up -d file-stats-api
    success "File Stats API deployed successfully"
}

# Deploy with Traefik
deploy_with_traefik() {
    log "Deploying File Stats API with Traefik..."
    $DOCKER_COMPOSE --profile traefik up -d
    success "File Stats API and Traefik deployed successfully"
}

# Show status
show_status() {
    log "Checking service status..."
    $DOCKER_COMPOSE ps
    
    log "Checking service health..."
    sleep 5
    
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        success "API is responding at http://localhost:8000"
        success "API documentation available at http://localhost:8000/docs"
    else
        warning "API might still be starting up. Please wait a moment and try again."
    fi
}

# Stop services
stop() {
    log "Stopping services..."
    $DOCKER_COMPOSE down
    success "Services stopped"
}

# Clean up
cleanup() {
    log "Cleaning up..."
    $DOCKER_COMPOSE down --rmi all --volumes --remove-orphans
    success "Cleanup completed"
}

# Show logs
logs() {
    $DOCKER_COMPOSE logs -f file-stats-api
}

# Main script logic
case "${1:-deploy}" in
    "build")
        check_docker
        create_directories
        build_image
        ;;
    "deploy")
        check_docker
        create_directories
        build_image
        deploy
        show_status
        ;;
    "deploy-traefik")
        check_docker
        create_directories
        build_image
        deploy_with_traefik
        show_status
        ;;
    "status")
        check_docker
        show_status
        ;;
    "stop")
        check_docker
        stop
        ;;
    "restart")
        check_docker
        stop
        deploy
        show_status
        ;;
    "logs")
        check_docker
        logs
        ;;
    "cleanup")
        check_docker
        cleanup
        ;;
    "help"|"-h"|"--help")
        echo "File Stats API Deployment Script"
        echo ""
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  build           Build the Docker image"
        echo "  deploy          Deploy the API (default)"
        echo "  deploy-traefik  Deploy the API with Traefik reverse proxy"
        echo "  status          Show service status"
        echo "  stop            Stop all services"
        echo "  restart         Restart the API service"
        echo "  logs            Show service logs"
        echo "  cleanup         Stop services and remove containers/images"
        echo "  help            Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0              # Deploy the API"
        echo "  $0 deploy       # Deploy the API"
        echo "  $0 status       # Check status"
        echo "  $0 logs         # Follow logs"
        echo "  $0 stop         # Stop services"
        ;;
    *)
        error "Unknown command: $1. Use '$0 help' for usage information."
        ;;
esac 