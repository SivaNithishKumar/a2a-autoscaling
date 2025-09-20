#!/bin/bash

# 🎨 Streamlit A2A Application Startup Helper
# This script ensures proper configuration and startup of the Streamlit app
# after Kubernetes services are ready

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-multi-agent-a2a}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}🎨 Streamlit A2A Application Startup Helper${NC}"
echo -e "${CYAN}===========================================${NC}"
echo ""

# Function to check if port is available
check_port_available() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to setup agent port forwards
setup_agent_port_forwards() {
    echo -e "${BLUE}🔗 Setting up port-forwards for A2A agents...${NC}"
    
    # Agent port mappings: local_port:service_name:service_port
    declare -A agents=(
        ["8000"]="base-agent-service:8080"
        ["8001"]="weather-agent-service:8080"
        ["8002"]="calculator-agent-service:8080"
        ["8003"]="research-agent-service:8080"
        ["8004"]="move-orchestrator-agent-service:8080"
        ["8005"]="infrastructure-monitor-agent-service:8080"
    )
    
    for local_port in "${!agents[@]}"; do
        IFS=':' read -r service_name service_port <<< "${agents[$local_port]}"
        
        # Check if service exists
        if kubectl get svc $service_name -n $NAMESPACE >/dev/null 2>&1; then
            echo -e "${YELLOW}   Setting up port-forward: localhost:$local_port -> $service_name:$service_port${NC}"
            kubectl port-forward -n $NAMESPACE svc/$service_name $local_port:$service_port >/dev/null 2>&1 &
            sleep 1
        else
            echo -e "${YELLOW}   ⚠️ Service $service_name not found, skipping port-forward${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Port-forwards established${NC}"
}

# Function to verify agent connectivity
verify_agent_connectivity() {
    echo -e "${BLUE}🔍 Verifying agent connectivity...${NC}"
    
    local agents=(
        "Base Agent:8000:/health"
        "Weather Agent:8001:/health"
        "Calculator Agent:8002:/health"
        "Research Agent:8003:/health"
        "Move Orchestrator:8004:/health"
        "Infrastructure Monitor:8005:/health"
    )
    
    local connected_agents=0
    local total_agents=${#agents[@]}
    
    for agent_info in "${agents[@]}"; do
        IFS=':' read -r agent_name port health_path <<< "$agent_info"
        
        echo -e "${YELLOW}   Checking $agent_name on port $port...${NC}"
        
        # Try to connect with retries
        local retries=5
        local connected=false
        
        for ((i=1; i<=retries; i++)); do
            if curl -s -f "http://localhost:$port$health_path" >/dev/null 2>&1; then
                echo -e "${GREEN}   ✅ $agent_name is responding${NC}"
                connected=true
                break
            fi
            
            if [ $i -lt $retries ]; then
                echo -e "${YELLOW}      Attempt $i/$retries failed, retrying in 2s...${NC}"
                sleep 2
            fi
        done
        
        if [ "$connected" = true ]; then
            connected_agents=$((connected_agents + 1))
        else
            echo -e "${RED}   ❌ $agent_name is not responding${NC}"
        fi
    done
    
    echo ""
    echo -e "${BLUE}📊 Agent Connectivity Summary: $connected_agents/$total_agents agents responding${NC}"
    
    if [ $connected_agents -eq $total_agents ]; then
        echo -e "${GREEN}✅ All agents are connected and ready${NC}"
        return 0
    elif [ $connected_agents -gt 0 ]; then
        echo -e "${YELLOW}⚠️ Some agents are not responding, but continuing with available agents${NC}"
        return 0
    else
        echo -e "${RED}❌ No agents are responding, check Kubernetes deployment${NC}"
        return 1
    fi
}

# Function to create Streamlit configuration
create_streamlit_config() {
    echo -e "${BLUE}⚙️ Creating Streamlit configuration...${NC}"
    
    # Create .streamlit directory if it doesn't exist
    mkdir -p .streamlit
    
    # Create config.toml
    cat > .streamlit/config.toml << EOF
[server]
port = $STREAMLIT_PORT
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = $STREAMLIT_PORT

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = true
EOF
    
    echo -e "${GREEN}✅ Streamlit configuration created${NC}"
}

# Function to setup environment variables
setup_environment() {
    echo -e "${BLUE}🌍 Setting up environment variables...${NC}"
    
    # Create .env file with agent endpoints
    cat > .env << EOF
# A2A Agent Endpoints
BASE_AGENT_URL=http://localhost:8000
WEATHER_AGENT_URL=http://localhost:8001
CALCULATOR_AGENT_URL=http://localhost:8002
RESEARCH_AGENT_URL=http://localhost:8003
MOVE_ORCHESTRATOR_URL=http://localhost:8004
INFRASTRUCTURE_MONITOR_URL=http://localhost:8005

# Streamlit Configuration
STREAMLIT_PORT=$STREAMLIT_PORT

# A2A Protocol Configuration
A2A_PROTOCOL_VERSION=1.0.0
A2A_SYSTEM_NAME=Multi-Agent A2A AI-Ops System

# Logging
LOG_LEVEL=INFO
METRICS_ENABLED=true
EOF
    
    echo -e "${GREEN}✅ Environment variables configured${NC}"
}

# Function to install Python dependencies
install_dependencies() {
    echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
    
    # Check if we're in a virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        echo -e "${YELLOW}⚠️ No virtual environment detected. Consider using a virtual environment.${NC}"
    fi
    
    # Install from requirements.txt if it exists
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}   Installing from requirements.txt...${NC}"
        pip install -r requirements.txt --quiet
    else
        echo -e "${YELLOW}   Installing core dependencies...${NC}"
        pip install streamlit httpx python-dotenv a2a-sdk openai langchain langchain-openai --quiet
    fi
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Function to start Streamlit app
start_streamlit() {
    echo -e "${BLUE}🚀 Starting Streamlit application...${NC}"
    
    # Check if Streamlit app file exists
    if [ ! -f "streamlit_a2a_app.py" ]; then
        echo -e "${RED}❌ streamlit_a2a_app.py not found${NC}"
        return 1
    fi
    
    # Check if port is available
    if ! check_port_available $STREAMLIT_PORT; then
        echo -e "${YELLOW}⚠️ Port $STREAMLIT_PORT is already in use${NC}"
        echo -e "${YELLOW}   Trying to find available port...${NC}"
        
        for port in {8502..8510}; do
            if check_port_available $port; then
                STREAMLIT_PORT=$port
                echo -e "${GREEN}   Using port $STREAMLIT_PORT instead${NC}"
                break
            fi
        done
    fi
    
    echo -e "${GREEN}🌐 Starting Streamlit on http://localhost:$STREAMLIT_PORT${NC}"
    echo -e "${YELLOW}   Press Ctrl+C to stop the application${NC}"
    echo ""
    
    # Start Streamlit
    streamlit run streamlit_a2a_app.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Starting Streamlit A2A Application...${NC}"
    echo ""
    
    # Check if kubectl is available and connected
    if ! kubectl cluster-info >/dev/null 2>&1; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        echo -e "${YELLOW}   Please ensure kubectl is configured and cluster is accessible${NC}"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
        echo -e "${RED}❌ Namespace $NAMESPACE does not exist${NC}"
        echo -e "${YELLOW}   Please run the deployment script first${NC}"
        exit 1
    fi
    
    # Setup steps
    create_streamlit_config
    setup_environment
    install_dependencies
    setup_agent_port_forwards
    
    # Wait for port-forwards to establish
    echo -e "${YELLOW}⏳ Waiting for port-forwards to establish...${NC}"
    sleep 5
    
    # Verify connectivity
    if ! verify_agent_connectivity; then
        echo -e "${YELLOW}⚠️ Some agents may not be ready, but starting Streamlit anyway${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                         🎨 STREAMLIT APP READY TO START                         ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Start Streamlit
    start_streamlit
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up port-forwards...${NC}"
    # Kill all kubectl port-forward processes
    pkill -f "kubectl port-forward" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set up signal handling
trap cleanup EXIT INT TERM

# Run main function
main "$@"