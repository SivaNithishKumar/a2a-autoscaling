#!/bin/bash

# 🚀 Quick A2A Multi-Agent System Deployment (Monitoring Optional)
# This script deploys the core A2A agents first, then optionally adds monitoring

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
SKIP_MONITORING="${SKIP_MONITORING:-false}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-120}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"

echo -e "${CYAN}🚀 Quick A2A Multi-Agent System Deployment${NC}"
echo -e "${CYAN}===========================================${NC}"
echo ""
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   Namespace:        ${YELLOW}$NAMESPACE${NC}"
echo -e "   Skip Monitoring:  ${YELLOW}$SKIP_MONITORING${NC}"
echo -e "   Streamlit Port:   ${YELLOW}$STREAMLIT_PORT${NC}"
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
    
    echo -e "${YELLOW}⏳ Waiting for deployment $deployment (timeout: ${timeout}s)...${NC}"
    
    if kubectl wait --for=condition=available --timeout=${timeout}s deployment/$deployment -n $namespace 2>/dev/null; then
        echo -e "${GREEN}✅ $deployment is ready${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ $deployment not ready yet, but continuing...${NC}"
        return 0  # Don't fail, just warn
    fi
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

# Step 1: Deploy Namespace and RBAC
echo -e "${BLUE}🏗️ Step 1: Deploying namespace and RBAC...${NC}"
kubectl apply -f k8s/agents/namespace.yaml
echo -e "${GREEN}✅ Namespace deployed${NC}"

# Step 2: Deploy Core A2A Agents
echo -e "${BLUE}🤖 Step 2: Deploying A2A agents...${NC}"
kubectl apply -f k8s/agents/
echo -e "${GREEN}✅ Agent manifests applied${NC}"

# Wait for agents to be ready
echo -e "${YELLOW}⏳ Waiting for agents to start...${NC}"
agents=("base-agent" "calculator-agent" "weather-agent" "research-agent")
for agent in "${agents[@]}"; do
    if kubectl get deployment $agent -n $NAMESPACE >/dev/null 2>&1; then
        wait_for_deployment "$agent" "$NAMESPACE" "$WAIT_TIMEOUT"
    fi
done

# Step 3: Deploy Autoscaling (without metrics dependency)
echo -e "${BLUE}📈 Step 3: Deploying autoscaling...${NC}"
kubectl apply -f k8s/autoscaling/ || echo -e "${YELLOW}⚠️ Some autoscaling configs failed (metrics server might not be available)${NC}"

# Step 4: Optional Monitoring
if [ "$SKIP_MONITORING" = "false" ]; then
    echo -e "${BLUE}📊 Step 4: Deploying monitoring (optional)...${NC}"
    kubectl apply -f k8s/monitoring/ || echo -e "${YELLOW}⚠️ Monitoring deployment had issues, but core system is working${NC}"
else
    echo -e "${YELLOW}⏭️ Skipping monitoring deployment${NC}"
fi

# Step 5: Check system status
echo -e "${BLUE}🔍 Step 5: System status check...${NC}"
echo -e "${YELLOW}📋 Pod Status:${NC}"
kubectl get pods -n $NAMESPACE

echo -e "\n${YELLOW}🌐 Service Status:${NC}"
kubectl get svc -n $NAMESPACE

# Step 6: Setup port-forwards for agents
echo -e "${BLUE}🔗 Step 6: Setting up port-forwards...${NC}"
echo -e "${YELLOW}   Setting up agent port-forwards...${NC}"

# Kill any existing port-forwards
pkill -f "kubectl port-forward" 2>/dev/null || true
sleep 2

# Setup port-forwards for available services
declare -A agent_ports=(
    ["base-agent-service"]="8000:8080"
    ["calculator-agent-service"]="8002:8080"
    ["weather-agent-service"]="8001:8080"
    ["research-agent-service"]="8003:8080"
    ["move-orchestrator-agent-service"]="8004:8080"
    ["infrastructure-monitor-agent-service"]="8005:8080"
)

for service in "${!agent_ports[@]}"; do
    port_mapping="${agent_ports[$service]}"
    if kubectl get svc $service -n $NAMESPACE >/dev/null 2>&1; then
        echo -e "${YELLOW}   Port-forward: localhost:${port_mapping% *} -> $service${NC}"
        kubectl port-forward -n $NAMESPACE svc/$service $port_mapping >/dev/null 2>&1 &
        sleep 1
    else
        echo -e "${YELLOW}   ⚠️ Service $service not found${NC}"
    fi
done

# Step 7: Verify agent connectivity
echo -e "${BLUE}🔍 Step 7: Verifying agent connectivity...${NC}"
sleep 5  # Wait for port-forwards to establish

agent_endpoints=("8000" "8001" "8002" "8003")
working_agents=0

for port in "${agent_endpoints[@]}"; do
    if curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Agent on port $port is responding${NC}"
        working_agents=$((working_agents + 1))
    else
        echo -e "${YELLOW}⚠️ Agent on port $port not responding yet${NC}"
    fi
done

echo -e "${BLUE}📊 Agent Status: $working_agents/4 agents responding${NC}"

# Step 8: Start Streamlit App
echo -e "${BLUE}🎨 Step 8: Starting Streamlit application...${NC}"

# Check if Streamlit app exists
if [ ! -f "streamlit_a2a_app.py" ]; then
    echo -e "${RED}❌ streamlit_a2a_app.py not found${NC}"
    exit 1
fi

# Install dependencies if needed
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install streamlit httpx python-dotenv --quiet 2>/dev/null || echo -e "${YELLOW}⚠️ Some dependencies may already be installed${NC}"

# Create environment file
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
EOF

echo -e "${GREEN}✅ Environment configured${NC}"

# Check if port is available
if lsof -i :$STREAMLIT_PORT >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Port $STREAMLIT_PORT is in use, trying port 8502...${NC}"
    STREAMLIT_PORT=8502
fi

echo -e "${GREEN}🚀 Starting Streamlit on http://localhost:$STREAMLIT_PORT${NC}"
echo -e "${YELLOW}   You can now interact with your A2A agents through the web interface!${NC}"
echo ""

# Final status
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                              🎉 DEPLOYMENT COMPLETE                              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo -e "   Streamlit App:     ${GREEN}http://localhost:$STREAMLIT_PORT${NC}"
echo -e "   Base Agent:        ${GREEN}http://localhost:8000${NC}"
echo -e "   Weather Agent:     ${GREEN}http://localhost:8001${NC}"
echo -e "   Calculator Agent:  ${GREEN}http://localhost:8002${NC}"
echo -e "   Research Agent:    ${GREEN}http://localhost:8003${NC}"
echo ""
echo -e "${BLUE}🛠️ Management Commands:${NC}"
echo -e "   Check pods:        ${YELLOW}kubectl get pods -n $NAMESPACE${NC}"
echo -e "   Check services:    ${YELLOW}kubectl get svc -n $NAMESPACE${NC}"
echo -e "   View logs:         ${YELLOW}kubectl logs -f deployment/base-agent -n $NAMESPACE${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up port-forwards...${NC}"
    pkill -f "kubectl port-forward" 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}
trap cleanup EXIT INT TERM

# Start Streamlit
echo -e "${BLUE}🎨 Launching Streamlit application...${NC}"
streamlit run streamlit_a2a_app.py --server.port $STREAMLIT_PORT --server.address 0.0.0.0