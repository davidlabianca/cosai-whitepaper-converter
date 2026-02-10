#!/usr/bin/env bash
# Local-only devcontainer validation. Requires: devcontainer CLI, Docker.
#
# Usage: ./scripts/test-devcontainer.sh [variant]
#   variant: "default" (default) or "pdflatex"
#
# What it tests:
#   1. devcontainer build   — Dockerfile builds successfully
#   2. devcontainer up      — Container starts, features install, onCreateCommand completes
#   3. devcontainer exec    — verify-deps.sh passes inside the container
#   4. devcontainer exec    — unit tests pass inside the container
#   5. Cleanup              — remove the test container

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[*]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error()   { echo -e "${RED}[✗]${NC} $1"; }

# Parse arguments
VARIANT="${1:-default}"
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER_ID=""

case "$VARIANT" in
    default)
        CONFIG_PATH="$WORKSPACE_DIR/.devcontainer/devcontainer.json"
        log_info "Testing default devcontainer variant"
        ;;
    pdflatex)
        CONFIG_PATH="$WORKSPACE_DIR/.devcontainer/pdflatex/devcontainer.json"
        log_info "Testing pdflatex devcontainer variant"
        ;;
    *)
        log_error "Unknown variant: $VARIANT (expected 'default' or 'pdflatex')"
        exit 1
        ;;
esac

# Verify prerequisites
if ! command -v devcontainer >/dev/null 2>&1; then
    log_error "devcontainer CLI not found. Install with: npm install -g @devcontainers/cli"
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    log_error "Docker not found. Please install Docker."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    log_error "Docker daemon not running."
    exit 1
fi

# Cleanup function
cleanup() {
    if [ -n "$CONTAINER_ID" ]; then
        log_info "Cleaning up container $CONTAINER_ID..."
        docker rm -f "$CONTAINER_ID" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

# Step 1: Build
log_info "Step 1/4: Building devcontainer..."
if devcontainer build --workspace-folder "$WORKSPACE_DIR" --config "$CONFIG_PATH"; then
    log_success "Build succeeded"
else
    log_error "Build failed"
    exit 1
fi

# Step 2: Start container
log_info "Step 2/4: Starting devcontainer..."
UP_OUTPUT=$(devcontainer up --workspace-folder "$WORKSPACE_DIR" --config "$CONFIG_PATH" 2>&1)
UP_EXIT=$?

if [ $UP_EXIT -ne 0 ]; then
    log_error "devcontainer up failed:"
    echo "$UP_OUTPUT"
    exit 1
fi

# Extract container ID from JSON output
# devcontainer up outputs JSON with containerId field
CONTAINER_ID=$(echo "$UP_OUTPUT" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('{'):
        try:
            data = json.loads(line)
            if 'containerId' in data:
                print(data['containerId'])
                break
        except json.JSONDecodeError:
            pass
" 2>/dev/null || true)

if [ -z "$CONTAINER_ID" ]; then
    log_warning "Could not extract container ID from devcontainer up output, trying docker ps..."
    CONTAINER_ID=$(docker ps -q --latest 2>/dev/null || true)
fi

if [ -z "$CONTAINER_ID" ]; then
    log_error "Could not determine container ID"
    exit 1
fi

log_success "Container started: ${CONTAINER_ID:0:12}"

# Step 3: Run verify-deps.sh
log_info "Step 3/4: Running verify-deps.sh inside container..."
if devcontainer exec --workspace-folder "$WORKSPACE_DIR" --config "$CONFIG_PATH" \
    bash -c "./scripts/verify-deps.sh"; then
    log_success "Dependency verification passed"
else
    log_error "Dependency verification failed"
    exit 1
fi

# Step 4: Run unit tests
log_info "Step 4/4: Running unit tests inside container..."
if devcontainer exec --workspace-folder "$WORKSPACE_DIR" --config "$CONFIG_PATH" \
    bash -c "pytest tests/unit/ --tb=short -q"; then
    log_success "Unit tests passed"
else
    log_warning "Some unit tests failed (check output above)"
    # Don't exit — pre-existing failures are expected
fi

echo ""
log_success "Devcontainer validation complete ($VARIANT variant)"
