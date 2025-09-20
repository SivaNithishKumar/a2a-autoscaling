#!/bin/bash

# 🚀 Fixed A2A Multi-Agent System Deployment Script
# This script properly configures port-forwarding and agent connectivity

set -e

# Colors for enhanced output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration Variables
NAMESPACE="${NAMESPACE:-multi-agent-a2a}"
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-kubernetes}"  # kubernetes or local
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"

echo -e "${CYAN}🚀 Fixed A2A Multi-Agent System Deployment${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   Namespace:         ${YELLOW}$NAMESPACE${NC}"
echo -e "   Deployment Mode:   ${YELLOW}$DEPLOYMENT_MODE${NC}"
echo -e "   Streamlit Port:    ${YELLOW}$STREAMLIT_PORT${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for deployment
wait_for_deployment() {
    local deployment=$1
    local namespace=$2
    local timeout=${3:-120}
    
    echo -e "${YELLOW}⏳ Waiting for deployment $deployment...${NC}"
    
    local count=0
    local max_attempts=$((timeout / 10))
    while [ $count -lt $max_attempts ]; do
        local ready_pods=$(kubectl get pods -n $namespace -l app=$deployment --no-headers 2>/dev/null | grep -c "Running" || echo "0")
        if [ "$ready_pods" -gt 0 ]; then
            echo -e "${GREEN}✅ $deployment is running${NC}"
            return 0
        fi
        count=$((count + 1))
        echo -e "${YELLOW}   Attempt $count/$max_attempts...${NC}"
        sleep 10
    done
    
    echo -e "${YELLOW}⚠️ $deployment may still be starting, continuing...${NC}"
    return 0
}

# Prerequisite checks
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
for tool in kubectl curl; do
    if command_exists "$tool"; then
        echo -e "${GREEN}✅ $tool is available${NC}"
    else
        echo -e "${RED}❌ $tool is not installed${NC}"
        exit 1
    fi
done

# Check kubectl cluster connection
if kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
else
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

# Step 1: Deploy Core System
echo -e "${BLUE}🏗️ Step 1: Deploying core system...${NC}"

# Deploy namespace
kubectl apply -f k8s/agents/namespace.yaml
echo -e "${GREEN}✅ Namespace deployed${NC}"

# Deploy agents
kubectl apply -f k8s/agents/
echo -e "${GREEN}✅ Agent manifests applied${NC}"

# Wait for key agents
echo -e "${YELLOW}⏳ Waiting for agents to start...${NC}"
key_agents=("base-agent" "calculator-agent" "weather-agent" "research-agent")
for agent in "${key_agents[@]}"; do
    wait_for_deployment "$agent" "$NAMESPACE" 60
done

# Step 2: Check Service Status
echo -e "${BLUE}🔍 Step 2: Checking service status...${NC}"
echo -e "${YELLOW}📋 Services:${NC}"
kubectl get svc -n $NAMESPACE | grep agent

echo -e "\n${YELLOW}📊 Pods:${NC}"
kubectl get pods -n $NAMESPACE | grep agent

# Step 3: Setup Connectivity Based on Mode
if [ "$DEPLOYMENT_MODE" = "kubernetes" ]; then
    echo -e "${BLUE}🎨 Step 3: Deploying Streamlit in Kubernetes...${NC}"
    
    # Deploy Streamlit in Kubernetes for proper service discovery
    kubectl apply -f k8s/agents/streamlit-app.yaml
    
    # Wait for Streamlit to be ready
    wait_for_deployment "streamlit-a2a-app" "$NAMESPACE" 60
    
    echo -e "${GREEN}✅ Streamlit deployed in Kubernetes${NC}"
    echo -e "${YELLOW}🌐 Setting up port-forward to access Streamlit...${NC}"
    
    # Setup port-forward to Streamlit service
    pkill -f "kubectl port-forward.*streamlit" 2>/dev/null || true
    kubectl port-forward -n $NAMESPACE svc/streamlit-a2a-service $STREAMLIT_PORT:8501 >/dev/null 2>&1 &
    
    echo -e "${GREEN}🎉 Streamlit accessible at: http://localhost:$STREAMLIT_PORT${NC}"
    
else
    echo -e "${BLUE}🔗 Step 3: Setting up local port-forwards...${NC}"
    
    # Kill existing port-forwards
    pkill -f "kubectl port-forward" 2>/dev/null || true
    sleep 2
    
    # Setup correct port-forwards based on actual service ports
    echo -e "${YELLOW}📡 Setting up agent port-forwards...${NC}"
    
    # Correct port mapping: local_port -> service:service_port
    declare -A port_mappings=(
        ["8000"]="base-agent-service:8080"
        ["8001"]="weather-agent-service:8082"      # Note: service runs on 8082, map to local 8001
        ["8002"]="calculator-agent-service:8081"   # Note: service runs on 8081, map to local 8002  
        ["8003"]="research-agent-service:8083"     # Note: service runs on 8083, map to local 8003
        ["8004"]="move-orchestrator-agent-service:8004"
        ["8005"]="infrastructure-monitor-agent-service:8005"
    )
    
    for local_port in "${!port_mappings[@]}"; do
        service_info="${port_mappings[$local_port]}"
        IFS=':' read -r service_name service_port <<< "$service_info"
        
        if kubectl get svc $service_name -n $NAMESPACE >/dev/null 2>&1; then
            echo -e "${YELLOW}   Port-forward: localhost:$local_port -> $service_name:$service_port${NC}"
            kubectl port-forward -n $NAMESPACE svc/$service_name $local_port:$service_port >/dev/null 2>&1 &
            sleep 1
        else
            echo -e "${YELLOW}   ⚠️ Service $service_name not found${NC}"
        fi
    done
    
    # Step 4: Start Local Streamlit
    echo -e "${BLUE}🎨 Step 4: Starting local Streamlit...${NC}"
    
    # Create proper environment configuration
    cat > .env << EOF
# A2A Agent Endpoints - Corrected for port-forward mapping
BASE_AGENT_URL=http://localhost:8000
WEATHER_AGENT_URL=http://localhost:8001
CALCULATOR_AGENT_URL=http://localhost:8002
RESEARCH_AGENT_URL=http://localhost:8003
MOVE_ORCHESTRATOR_URL=http://localhost:8004
INFRASTRUCTURE_MONITOR_URL=http://localhost:8005

# Streamlit Configuration
STREAMLIT_PORT=$STREAMLIT_PORT
EOF
    
    # Install dependencies
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install streamlit httpx python-dotenv a2a-sdk --quiet 2>/dev/null || true
    
    echo -e "${GREEN}🚀 Starting Streamlit locally...${NC}"
fi

# Step 4: Verify Connectivity
echo -e "${BLUE}🔍 Step 4: Verifying agent connectivity...${NC}"
sleep 5  # Wait for port-forwards to establish

if [ "$DEPLOYMENT_MODE" = "local" ]; then
    # Test local port-forwards
    test_ports=("8000" "8001" "8002" "8003")
    working_agents=0
    
    for port in "${test_ports[@]}"; do
        if curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Agent on port $port responding${NC}"
            working_agents=$((working_agents + 1))
        else
            echo -e "${YELLOW}⚠️ Agent on port $port not responding (may still be starting)${NC}"
        fi
    done
    
    echo -e "${BLUE}📊 Connectivity: $working_agents/4 agents responding${NC}"
fi

# Step 5: Final Information
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                              🎉 DEPLOYMENT COMPLETE                              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DEPLOYMENT_MODE" = "kubernetes" ]; then
    echo -e "${GREEN}🌐 Streamlit URL: http://localhost:$STREAMLIT_PORT${NC}"
    echo -e "${BLUE}📝 Note: Streamlit is running in Kubernetes with proper internal service discovery${NC}"
    echo -e "${YELLOW}💡 All agents will be accessible through the Streamlit interface${NC}"
else
    echo -e "${GREEN}🌐 Streamlit URL: http://localhost:$STREAMLIT_PORT${NC}"
    echo -e "${BLUE}🔗 Agent Endpoints:${NC}"
    echo -e "   Base Agent:        http://localhost:8000"
    echo -e "   Weather Agent:     http://localhost:8001"
    echo -e "   Calculator Agent:  http://localhost:8002"
    echo -e "   Research Agent:    http://localhost:8003"
fi

echo ""
echo -e "${BLUE}🛠️ Management Commands:${NC}"
echo -e "   Check pods:     ${YELLOW}kubectl get pods -n $NAMESPACE${NC}"
echo -e "   Check services: ${YELLOW}kubectl get svc -n $NAMESPACE${NC}"
echo -e "   View logs:      ${YELLOW}kubectl logs -f deployment/base-agent -n $NAMESPACE${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up port-forwards...${NC}"
    pkill -f "kubectl port-forward" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

if [ "$DEPLOYMENT_MODE" = "local" ]; then
    trap cleanup EXIT INT TERM
    echo -e "${BLUE}🎨 Launching Streamlit application...${NC}"
    streamlit run streamlit_a2a_app.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0
else
    echo -e "${GREEN}✨ Deployment complete! Access your A2A system at: http://localhost:$STREAMLIT_PORT${NC}"
fi