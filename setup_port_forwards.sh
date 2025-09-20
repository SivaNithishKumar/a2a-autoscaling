#!/bin/bash

# 🔗 A2A Agent Port-Forward Setup Script
# Sets up correct port-forwards for local development

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

NAMESPACE="${NAMESPACE:-multi-agent-a2a}"

echo -e "${BLUE}🔗 Setting up A2A Agent Port-Forwards${NC}"
echo -e "${BLUE}====================================${NC}"
echo ""

# Kill existing port-forwards
echo -e "${YELLOW}🧹 Cleaning up existing port-forwards...${NC}"
pkill -f "kubectl port-forward" 2>/dev/null || true
sleep 2

# Setup correct port-forwards
# Format: local_port:service_name:service_port
declare -A agents=(
    ["8000"]="base-agent-service:8080"
    ["8001"]="weather-agent-service:8082"
    ["8002"]="calculator-agent-service:8081"
    ["8003"]="research-agent-service:8083"
    ["8004"]="move-orchestrator-service:8004"
    ["8005"]="infrastructure-monitor-service:8005"
    ["8501"]="streamlit-a2a-service:8501"
)

echo -e "${BLUE}🚀 Setting up port-forwards...${NC}"

for local_port in "${!agents[@]}"; do
    service_info="${agents[$local_port]}"
    IFS=':' read -r service_name service_port <<< "$service_info"
    
    if kubectl get svc $service_name -n $NAMESPACE >/dev/null 2>&1; then
        echo -e "${YELLOW}   localhost:$local_port -> $service_name:$service_port${NC}"
        kubectl port-forward -n $NAMESPACE svc/$service_name $local_port:$service_port >/dev/null 2>&1 &
        sleep 1
    else
        echo -e "${RED}   ❌ Service $service_name not found${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ Port-forwards established!${NC}"
echo ""
echo -e "${BLUE}🌐 Access URLs:${NC}"
echo -e "   Streamlit:         ${GREEN}http://localhost:8501${NC}"
echo -e "   Base Agent:        ${GREEN}http://localhost:8000${NC}"
echo -e "   Weather Agent:     ${GREEN}http://localhost:8001${NC}"
echo -e "   Calculator Agent:  ${GREEN}http://localhost:8002${NC}"
echo -e "   Research Agent:    ${GREEN}http://localhost:8003${NC}"
echo ""

# Test connectivity
echo -e "${BLUE}🔍 Testing agent connectivity...${NC}"
sleep 3

test_ports=("8000" "8001" "8002" "8003" "8501")
for port in "${test_ports[@]}"; do
    if curl -s -f "http://localhost:$port" >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Port $port responding${NC}"
    else
        echo -e "${YELLOW}   ⚠️ Port $port not responding yet${NC}"
    fi
done

echo ""
echo -e "${YELLOW}💡 Keep this terminal open to maintain port-forwards${NC}"
echo -e "${YELLOW}   Press Ctrl+C to stop all port-forwards${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Stopping port-forwards...${NC}"
    pkill -f "kubectl port-forward" 2>/dev/null || true
    echo -e "${GREEN}✅ All port-forwards stopped${NC}"
}

# Set up signal handling
trap cleanup EXIT INT TERM

# Wait for interrupt
echo -e "${BLUE}🔄 Port-forwards are running. Waiting for stop signal...${NC}"
while true; do
    sleep 10
    # Check if any port-forwards are still running
    if ! pgrep -f "kubectl port-forward" >/dev/null; then
        echo -e "${RED}❌ Port-forwards stopped unexpectedly${NC}"
        break
    fi
done