#!/bin/bash
#
# FlowAudit Installer Script
#
# This script performs preflight checks and sets up FlowAudit.
# Requirements: Docker, Docker Compose v2+, 16GB RAM, 20GB disk space
#
# Usage:
#   ./installer.sh                  # Run preflight checks only
#   ./installer.sh --setup-gpu      # Detect and setup NVIDIA GPU drivers
#   ./installer.sh --generate-secrets  # Generate secure secrets for production
#   ./installer.sh --help           # Show help
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

# Global flags
SETUP_GPU=false
GENERATE_SECRETS=false
SHOW_HELP=false

# Default env file location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/stack.env"

# Show usage help
show_help() {
    echo "FlowAudit Installer Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup-gpu         Detect NVIDIA GPU and install drivers + container toolkit"
    echo "  --generate-secrets  Generate secure secrets for production deployment"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                     # Run preflight checks only"
    echo "  $0 --setup-gpu         # Setup NVIDIA GPU support"
    echo "  $0 --generate-secrets  # Generate production secrets"
    echo ""
}

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

# Generate a random hex string
generate_random_hex() {
    local length="${1:-32}"
    if command -v openssl &> /dev/null; then
        openssl rand -hex "$length"
    elif [ -f /dev/urandom ]; then
        head -c "$length" /dev/urandom | xxd -p | tr -d '\n'
    else
        # Fallback using $RANDOM (less secure)
        local result=""
        for _ in $(seq 1 "$length"); do
            result="${result}$(printf '%x' $((RANDOM % 16)))"
        done
        echo "$result"
    fi
}

# Generate secure secrets for production
generate_secrets() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}         Generate Production Secrets${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"

    print_step "Generating secure random secrets..."

    # Generate secrets
    SECRET_KEY=$(generate_random_hex 32)
    POSTGRES_PASSWORD=$(generate_random_hex 16)
    CHROMA_TOKEN=$(generate_random_hex 16)

    print_success "SECRET_KEY generated (64 chars)"
    print_success "POSTGRES_PASSWORD generated (32 chars)"
    print_success "CHROMA_TOKEN generated (32 chars)"

    # Check if env file exists
    if [ -f "$ENV_FILE" ]; then
        echo ""
        print_warning "Environment file already exists: $ENV_FILE"
        read -p "Do you want to update it with new secrets? [y/N] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Aborted. No changes made."
            return 0
        fi
    fi

    print_step "Creating environment file: $ENV_FILE"

    # Read existing stack.env.example if exists, or create new
    if [ -f "${SCRIPT_DIR}/stack.env.example" ]; then
        cp "${SCRIPT_DIR}/stack.env.example" "$ENV_FILE"
        print_success "Copied from stack.env.example"
    fi

    # Update or create the env file with new secrets
    # Create backup if file exists
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "${ENV_FILE}.bak"
        print_success "Backup created: ${ENV_FILE}.bak"
    fi

    # Update SECRET_KEY
    if grep -q "^SECRET_KEY=" "$ENV_FILE" 2>/dev/null; then
        sed -i "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" "$ENV_FILE"
    else
        echo "SECRET_KEY=${SECRET_KEY}" >> "$ENV_FILE"
    fi

    # Update POSTGRES_PASSWORD
    if grep -q "^POSTGRES_PASSWORD=" "$ENV_FILE" 2>/dev/null; then
        sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" "$ENV_FILE"
    else
        echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> "$ENV_FILE"
    fi

    # Update CHROMA_TOKEN
    if grep -q "^CHROMA_TOKEN=" "$ENV_FILE" 2>/dev/null; then
        sed -i "s/^CHROMA_TOKEN=.*/CHROMA_TOKEN=${CHROMA_TOKEN}/" "$ENV_FILE"
    else
        echo "CHROMA_TOKEN=${CHROMA_TOKEN}" >> "$ENV_FILE"
    fi

    # Disable demo users for production
    if grep -q "^DEMO_USERS=" "$ENV_FILE" 2>/dev/null; then
        sed -i 's/^DEMO_USERS=.*/DEMO_USERS=/' "$ENV_FILE"
    else
        echo "DEMO_USERS=" >> "$ENV_FILE"
    fi

    # Disable debug mode for production
    if grep -q "^DEBUG=" "$ENV_FILE" 2>/dev/null; then
        sed -i 's/^DEBUG=.*/DEBUG=false/' "$ENV_FILE"
    else
        echo "DEBUG=false" >> "$ENV_FILE"
    fi

    print_success "Environment file updated: $ENV_FILE"

    # Summary
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Secrets Generated Successfully${NC}\n"

    echo -e "The following changes were made to ${BLUE}$ENV_FILE${NC}:\n"
    echo -e "  ${GREEN}•${NC} SECRET_KEY       = ${SECRET_KEY:0:8}...${SECRET_KEY: -8} (masked)"
    echo -e "  ${GREEN}•${NC} POSTGRES_PASSWORD = ${POSTGRES_PASSWORD:0:4}...${POSTGRES_PASSWORD: -4} (masked)"
    echo -e "  ${GREEN}•${NC} CHROMA_TOKEN     = ${CHROMA_TOKEN:0:4}...${CHROMA_TOKEN: -4} (masked)"
    echo -e "  ${GREEN}•${NC} DEMO_USERS       = (empty - disabled)"
    echo -e "  ${GREEN}•${NC} DEBUG            = false"

    echo -e "\n${YELLOW}IMPORTANT:${NC}"
    echo -e "  • Keep these secrets secure and never commit them to version control"
    echo -e "  • A backup was saved to: ${ENV_FILE}.bak"
    echo -e "  • Update DATABASE_URL if you changed POSTGRES_PASSWORD"
    echo ""

    return 0
}

# Detect NVIDIA GPU hardware
detect_nvidia_gpu() {
    print_step "Detecting NVIDIA GPU hardware..."

    # Check for NVIDIA GPU via lspci
    if command -v lspci &> /dev/null; then
        GPU_INFO=$(lspci | grep -i nvidia 2>/dev/null || true)
        if [ -n "$GPU_INFO" ]; then
            print_success "NVIDIA GPU detected in system:"
            echo "$GPU_INFO" | while read -r line; do
                echo -e "    ${GREEN}•${NC} $line"
            done
            return 0
        fi
    fi

    # Alternative check via /sys
    if [ -d "/sys/class/drm" ]; then
        for card in /sys/class/drm/card*/device/vendor; do
            if [ -f "$card" ] && grep -q "0x10de" "$card" 2>/dev/null; then
                print_success "NVIDIA GPU detected via sysfs"
                return 0
            fi
        done
    fi

    print_warning "No NVIDIA GPU hardware detected in this system."
    return 1
}

# Check CUDA/driver version compatibility
check_cuda_compatibility() {
    print_step "Checking CUDA/driver compatibility..."

    if ! command -v nvidia-smi &> /dev/null; then
        print_warning "nvidia-smi not found. Driver may not be installed."
        return 1
    fi

    DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1 || echo "unknown")
    CUDA_VERSION=$(nvidia-smi --query-gpu=cuda_version --format=csv,noheader 2>/dev/null | head -1 2>/dev/null || \
                   nvidia-smi | grep "CUDA Version" | awk '{print $9}' || echo "unknown")

    if [ "$DRIVER_VERSION" = "unknown" ]; then
        print_warning "Could not determine driver version"
        return 1
    fi

    print_success "NVIDIA Driver: $DRIVER_VERSION"
    print_success "CUDA Version: $CUDA_VERSION"

    # Check minimum driver version for CUDA 11+ (required for modern LLMs)
    DRIVER_MAJOR=$(echo "$DRIVER_VERSION" | cut -d. -f1)
    if [ "$DRIVER_MAJOR" -lt 450 ]; then
        print_warning "Driver version $DRIVER_VERSION may be too old for optimal LLM performance."
        print_warning "Recommended minimum: 450.x for CUDA 11 support."
    fi

    return 0
}

# Install NVIDIA driver on Debian/Ubuntu
install_nvidia_driver() {
    print_step "Installing NVIDIA driver..."

    # Check if already installed
    if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
        print_success "NVIDIA driver is already installed and working."
        return 0
    fi

    # Check for apt (Debian/Ubuntu)
    if ! command -v apt-get &> /dev/null; then
        print_error "apt-get not found. This script only supports Debian/Ubuntu for automatic driver installation."
        print_warning "For other distributions, please install the NVIDIA driver manually."
        return 1
    fi

    # Check for root/sudo
    if [ "$EUID" -ne 0 ]; then
        print_warning "Root privileges required for driver installation."
        echo -e "${YELLOW}Please run: sudo $0 --setup-gpu${NC}"
        return 1
    fi

    print_step "Updating package lists..."
    apt-get update -qq

    print_step "Installing NVIDIA driver (this may take a few minutes)..."

    # Try nvidia-driver-535 (recommended for modern GPUs)
    if apt-cache show nvidia-driver-535 &> /dev/null; then
        apt-get install -y nvidia-driver-535
    elif apt-cache show nvidia-driver-525 &> /dev/null; then
        apt-get install -y nvidia-driver-525
    elif apt-cache show nvidia-driver-470 &> /dev/null; then
        apt-get install -y nvidia-driver-470
    else
        # Use ubuntu-drivers to auto-select
        if command -v ubuntu-drivers &> /dev/null; then
            ubuntu-drivers autoinstall
        else
            apt-get install -y ubuntu-drivers-common
            ubuntu-drivers autoinstall
        fi
    fi

    print_success "NVIDIA driver installed successfully."
    print_warning "A system reboot may be required for the driver to take effect."
    return 0
}

# Install NVIDIA Container Toolkit
install_container_toolkit() {
    print_step "Installing NVIDIA Container Toolkit..."

    # Check if already working
    if docker info 2>/dev/null | grep -q "nvidia"; then
        print_success "NVIDIA Container Toolkit is already installed and configured."
        return 0
    fi

    # Check for apt (Debian/Ubuntu)
    if ! command -v apt-get &> /dev/null; then
        print_error "apt-get not found. This script only supports Debian/Ubuntu."
        print_warning "For other distributions, see: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        return 1
    fi

    # Check for root/sudo
    if [ "$EUID" -ne 0 ]; then
        print_warning "Root privileges required for toolkit installation."
        echo -e "${YELLOW}Please run: sudo $0 --setup-gpu${NC}"
        return 1
    fi

    print_step "Adding NVIDIA Container Toolkit repository..."

    # Install prerequisites
    apt-get update -qq
    apt-get install -y curl gnupg

    # Add NVIDIA GPG key and repository
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null

    apt-get update -qq

    print_step "Installing nvidia-container-toolkit..."
    apt-get install -y nvidia-container-toolkit

    print_step "Configuring Docker to use NVIDIA runtime..."
    nvidia-ctk runtime configure --runtime=docker

    print_step "Restarting Docker daemon..."
    systemctl restart docker

    # Verify installation
    if docker info 2>/dev/null | grep -q "nvidia"; then
        print_success "NVIDIA Container Toolkit installed and configured successfully."
    else
        print_warning "Installation completed but Docker NVIDIA runtime not detected."
        print_warning "You may need to restart Docker or the system."
    fi

    return 0
}

# Full GPU setup
setup_gpu() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}         NVIDIA GPU Setup${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}\n"

    # Step 1: Detect hardware
    if ! detect_nvidia_gpu; then
        print_error "No NVIDIA GPU found. GPU setup cannot continue."
        return 1
    fi

    # Step 2: Check/install driver
    if ! check_cuda_compatibility; then
        echo ""
        read -p "Would you like to install the NVIDIA driver? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_nvidia_driver
        else
            print_warning "Skipping driver installation."
        fi
    fi

    # Step 3: Install container toolkit
    if ! docker info 2>/dev/null | grep -q "nvidia"; then
        echo ""
        read -p "Would you like to install the NVIDIA Container Toolkit? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_container_toolkit
        else
            print_warning "Skipping container toolkit installation."
        fi
    fi

    # Summary
    echo -e "\n${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}GPU Setup Complete${NC}\n"

    if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
        print_success "NVIDIA driver is working"
    else
        print_warning "NVIDIA driver needs installation or reboot"
    fi

    if docker info 2>/dev/null | grep -q "nvidia"; then
        print_success "Docker can use NVIDIA GPU"
        echo -e "\nTo use GPU-accelerated Ollama, use:"
        echo -e "  ${BLUE}docker compose -f docker-compose.portainer.gpu.yml up -d${NC}\n"
    else
        print_warning "Docker NVIDIA runtime not configured"
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

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --setup-gpu)
                SETUP_GPU=true
                shift
                ;;
            --generate-secrets)
                GENERATE_SECRETS=true
                shift
                ;;
            --help|-h)
                SHOW_HELP=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Main execution
main() {
    parse_args "$@"

    if [ "$SHOW_HELP" = true ]; then
        show_help
        exit 0
    fi

    print_header

    if [ "$SETUP_GPU" = true ]; then
        setup_gpu
        exit $?
    fi

    if [ "$GENERATE_SECRETS" = true ]; then
        generate_secrets
        exit $?
    fi

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
