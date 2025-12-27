#!/bin/bash
#
# FlowAudit Installer Script
#
# This script performs preflight checks and sets up FlowAudit.
# Requirements: Docker, Docker Compose v2+, 16GB RAM, 20GB disk space
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Minimum requirements
MIN_DOCKER_VERSION="20.10"
MIN_COMPOSE_VERSION="2.0"
MIN_RAM_GB=16
MIN_DISK_GB=20

# Track errors
ERRORS=()

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║      FlowAudit Installation Script             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
    ERRORS+=("$1")
}

# Compare version numbers
version_ge() {
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check Docker installation
check_docker() {
    print_step "Checking Docker..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker: https://docs.docker.com/get-docker/"
        return 1
    fi

    # Get Docker version
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "0.0.0")

    if [ "$DOCKER_VERSION" = "0.0.0" ]; then
        print_error "Docker daemon is not running. Please start Docker."
        return 1
    fi

    # Check minimum version
    DOCKER_MAJOR=$(echo "$DOCKER_VERSION" | cut -d. -f1)
    DOCKER_MINOR=$(echo "$DOCKER_VERSION" | cut -d. -f2)
    MIN_MAJOR=$(echo "$MIN_DOCKER_VERSION" | cut -d. -f1)
    MIN_MINOR=$(echo "$MIN_DOCKER_VERSION" | cut -d. -f2)

    if [ "$DOCKER_MAJOR" -lt "$MIN_MAJOR" ] || ([ "$DOCKER_MAJOR" -eq "$MIN_MAJOR" ] && [ "$DOCKER_MINOR" -lt "$MIN_MINOR" ]); then
        print_error "Docker version $DOCKER_VERSION is too old. Minimum required: $MIN_DOCKER_VERSION"
        return 1
    fi

    print_success "Docker $DOCKER_VERSION installed"
    return 0
}

# Check Docker Compose
check_compose() {
    print_step "Checking Docker Compose..."

    # Try docker compose (v2)
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short 2>/dev/null)
        COMPOSE_CMD="docker compose"
    # Try docker-compose (v1)
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose version --short 2>/dev/null)
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose is not installed. Please install Docker Compose v2+."
        return 1
    fi

    # Extract major version
    COMPOSE_MAJOR=$(echo "$COMPOSE_VERSION" | sed 's/^v//' | cut -d. -f1)

    if [ "$COMPOSE_MAJOR" -lt 2 ]; then
        print_error "Docker Compose version $COMPOSE_VERSION is too old. Minimum required: v$MIN_COMPOSE_VERSION"
        print_warning "Docker Compose v1 is deprecated. Please upgrade to v2."
        return 1
    fi

    print_success "Docker Compose $COMPOSE_VERSION installed ($COMPOSE_CMD)"
    return 0
}

# Check available RAM
check_ram() {
    print_step "Checking available RAM..."

    # Get total RAM in GB
    if [ "$(uname)" = "Darwin" ]; then
        # macOS
        TOTAL_RAM_BYTES=$(sysctl -n hw.memsize)
        TOTAL_RAM_GB=$((TOTAL_RAM_BYTES / 1073741824))
    else
        # Linux
        TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1048576))
    fi

    if [ "$TOTAL_RAM_GB" -lt "$MIN_RAM_GB" ]; then
        print_error "Insufficient RAM: ${TOTAL_RAM_GB}GB available, ${MIN_RAM_GB}GB required"
        print_warning "Ollama LLM requires at least 16GB RAM for optimal performance."
        return 1
    fi

    print_success "RAM: ${TOTAL_RAM_GB}GB available (minimum: ${MIN_RAM_GB}GB)"
    return 0
}

# Check available disk space
check_disk() {
    print_step "Checking disk space..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ "$(uname)" = "Darwin" ]; then
        # macOS
        AVAILABLE_GB=$(df -g "$SCRIPT_DIR" | tail -1 | awk '{print $4}')
    else
        # Linux
        AVAILABLE_KB=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $4}')
        AVAILABLE_GB=$((AVAILABLE_KB / 1048576))
    fi

    if [ "$AVAILABLE_GB" -lt "$MIN_DISK_GB" ]; then
        print_error "Insufficient disk space: ${AVAILABLE_GB}GB available, ${MIN_DISK_GB}GB required"
        print_warning "Ollama models and Docker images require significant disk space."
        return 1
    fi

    print_success "Disk space: ${AVAILABLE_GB}GB available (minimum: ${MIN_DISK_GB}GB)"
    return 0
}

# Check GPU availability (optional)
check_gpu() {
    print_step "Checking GPU availability (optional)..."

    GPU_AVAILABLE=false

    # Check for NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
            GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -1)
            print_success "NVIDIA GPU detected: $GPU_NAME ($GPU_MEMORY)"
            GPU_AVAILABLE=true

            # Check for nvidia-container-toolkit
            if docker info 2>/dev/null | grep -q "nvidia"; then
                print_success "NVIDIA Container Toolkit is installed"
            else
                print_warning "NVIDIA Container Toolkit not detected. GPU acceleration may not work in Docker."
                print_warning "Install with: sudo apt-get install nvidia-container-toolkit"
            fi
        fi
    fi

    if [ "$GPU_AVAILABLE" = false ]; then
        print_warning "No GPU detected. LLM inference will use CPU (slower but functional)."
    fi

    return 0
}

# Check network connectivity
check_network() {
    print_step "Checking network connectivity..."

    # Check Docker Hub connectivity
    if curl -s --connect-timeout 5 https://hub.docker.com > /dev/null 2>&1; then
        print_success "Docker Hub is reachable"
    else
        print_warning "Cannot reach Docker Hub. Make sure you have internet connectivity for pulling images."
    fi

    return 0
}

# Summary of checks
print_summary() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"

    if [ ${#ERRORS[@]} -eq 0 ]; then
        echo -e "${GREEN}All preflight checks passed!${NC}\n"
        echo -e "You can now start FlowAudit with:"
        echo -e "  ${BLUE}cd docker && docker compose up -d${NC}\n"
        return 0
    else
        echo -e "${RED}Preflight checks failed with ${#ERRORS[@]} error(s):${NC}\n"
        for error in "${ERRORS[@]}"; do
            echo -e "  ${RED}•${NC} $error"
        done
        echo -e "\nPlease fix the above issues and run this script again.\n"
        return 1
    fi
}

# Main execution
main() {
    print_header

    echo -e "Running preflight checks...\n"

    check_docker
    check_compose
    check_ram
    check_disk
    check_gpu
    check_network

    print_summary
    exit_code=$?

    exit $exit_code
}

# Run main function
main "$@"
