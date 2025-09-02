#!/bin/bash
# Build all A2A agent Docker images with proper tagging and testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REGISTRY="${REGISTRY:-localhost:5000}"
VERSION="${VERSION:-latest}"
BUILD_ARGS="${BUILD_ARGS:-}"

echo -e "${BLUE}🔨 Building all A2A agent Docker images...${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Registry: $REGISTRY"
echo "Version: $VERSION"
echo ""

# Agent configurations
declare -A AGENTS=(
    ["base"]="8080"
    ["calculator"]="8081"
    ["weather"]="8082"
    ["research"]="8083"
    ["move_orchestrator"]="8004"
    ["infrastructure_monitor"]="8005"
)

# Function to build and test an agent image
build_and_test_agent() {
    local agent_name=$1
    local port=$2
    local image_name="a2a-${agent_name}-agent"
    local full_image_name="${REGISTRY}/${image_name}:${VERSION}"
    
    echo -e "${YELLOW}📦 Building ${agent_name} agent...${NC}"
    
    # Build the image
    cd "${PROJECT_ROOT}"
    docker build \
        -f "src/agents/${agent_name}/Dockerfile" \
        -t "${image_name}:${VERSION}" \
        -t "${image_name}:latest" \
        -t "${full_image_name}" \
        ${BUILD_ARGS} \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${agent_name} agent image built successfully${NC}"
    else
        echo -e "${RED}❌ Failed to build ${agent_name} agent image${NC}"
        return 1
    fi
    
    # Test the image
    echo -e "${BLUE}🧪 Testing ${agent_name} agent image...${NC}"
    
    # Start container for testing
    local container_name="test-${agent_name}-$(date +%s)"
    local test_port=$((port + 1000))
    
    docker run -d \
        --name "${container_name}" \
        -p "${test_port}:${port}" \
        -e LOG_LEVEL=DEBUG \
        "${image_name}:${VERSION}"
    
    # Wait for container to start
    echo "Waiting for container to start..."
    sleep 10
    
    # Health check
    local health_check_passed=false
    for i in {1..30}; do
        if curl -f "http://localhost:${test_port}/health" >/dev/null 2>&1; then
            health_check_passed=true
            break
        fi
        echo "Attempt $i/30: Waiting for health check..."
        sleep 2
    done
    
    if [ "$health_check_passed" = true ]; then
        echo -e "${GREEN}✅ ${agent_name} agent health check passed${NC}"
        
        # Test agent card endpoint
        if curl -f "http://localhost:${test_port}/.well-known/agent-card.json" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ ${agent_name} agent card endpoint working${NC}"
        else
            echo -e "${YELLOW}⚠️  ${agent_name} agent card endpoint not responding${NC}"
        fi
    else
        echo -e "${RED}❌ ${agent_name} agent health check failed${NC}"
        docker logs "${container_name}"
        docker stop "${container_name}" >/dev/null 2>&1
        docker rm "${container_name}" >/dev/null 2>&1
        return 1
    fi
    
    # Cleanup test container
    docker stop "${container_name}" >/dev/null 2>&1
    docker rm "${container_name}" >/dev/null 2>&1
    
    echo -e "${GREEN}🎉 ${agent_name} agent image ready for deployment${NC}"
    echo ""
}

# Function to push images to registry
push_images() {
    echo -e "${BLUE}📤 Pushing images to registry...${NC}"
    
    for agent_name in "${!AGENTS[@]}"; do
        local image_name="a2a-${agent_name}-agent"
        local full_image_name="${REGISTRY}/${image_name}:${VERSION}"
        
        echo -e "${YELLOW}Pushing ${full_image_name}...${NC}"
        docker push "${full_image_name}"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ ${agent_name} agent pushed successfully${NC}"
        else
            echo -e "${RED}❌ Failed to push ${agent_name} agent${NC}"
        fi
    done
}

# Main execution
main() {
    local failed_builds=()
    
    # Build and test all agents
    for agent_name in "${!AGENTS[@]}"; do
        local port="${AGENTS[$agent_name]}"
        
        if ! build_and_test_agent "$agent_name" "$port"; then
            failed_builds+=("$agent_name")
        fi
    done
    
    # Report results
    echo -e "${BLUE}📊 Build Summary:${NC}"
    echo "Total agents: ${#AGENTS[@]}"
    echo "Successful builds: $((${#AGENTS[@]} - ${#failed_builds[@]}))"
    echo "Failed builds: ${#failed_builds[@]}"
    
    if [ ${#failed_builds[@]} -gt 0 ]; then
        echo -e "${RED}Failed agents: ${failed_builds[*]}${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🎉 All agent images built and tested successfully!${NC}"
    
    # Ask if user wants to push to registry
    if [ "$REGISTRY" != "localhost:5000" ]; then
        read -p "Push images to registry? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            push_images
        fi
    fi
    
    echo -e "${GREEN}✅ Build process complete!${NC}"
}

# Run main function
main "$@"
