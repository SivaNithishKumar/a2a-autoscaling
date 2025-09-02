#!/bin/bash

# Multi-Agent A2A System - Health Check Script
# Checks the health status of independent A2A agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 Multi-Agent A2A System - Health Check${NC}"
echo "=========================================="
echo -e "${YELLOW}📝 Note: Checking independent A2A agents (no centralized engine)${NC}"

# Agent endpoints (removed centralized engine)
AGENTS=(
    "Base Agent:http://localhost:8000"
    "Weather Agent:http://localhost:8001"
    "Calculator Agent:http://localhost:8002"
    "Research Agent:http://localhost:8003"
)

# Function to check agent health
check_agent_health() {
    local agent_name=$1
    local url=$2
    
    echo -e "\n${YELLOW}🔍 Checking $agent_name...${NC}"
    
    # Check if the port is listening
    local port=$(echo $url | grep -o '[0-9]\+$')
    if ! nc -z localhost $port 2>/dev/null; then
        echo -e "${RED}❌ $agent_name is not running (port $port not listening)${NC}"
        return 1
    fi
    
    # Make health check request
    local health_url="$url/health"
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$health_url" 2>/dev/null || echo "HTTPSTATUS:000")
    local body=$(echo $response | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    local status=$(echo $response | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status" = "200" ]; then
        echo -e "${GREEN}✅ $agent_name is healthy${NC}"
        if [ ! -z "$body" ]; then
            echo -e "   Response: $body"
        fi
        return 0
    else
        echo -e "${RED}❌ $agent_name health check failed (HTTP $status)${NC}"
        if [ ! -z "$body" ]; then
            echo -e "   Error: $body"
        fi
        return 1
    fi
}

# Function to test agent functionality
test_agent_functionality() {
    local agent_name=$1
    local url=$2
    
    echo -e "\n${BLUE}🧪 Testing $agent_name functionality...${NC}"
    
    case $agent_name in
        "Agent Engine")
            test_data='{"message": "test request", "context": {}}'
            ;;
        "Weather Agent")
            test_data='{"message": "What is the weather in New York?", "context": {}}'
            ;;
        "Calculator Agent")
            test_data='{"message": "What is 2 + 2?", "context": {}}'
            ;;
        "Research Agent")
            test_data='{"message": "Search for information about AI", "context": {}}'
            ;;
        *)
            echo -e "${YELLOW}⚠️  No test defined for $agent_name${NC}"
            return 0
            ;;
    esac
    
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$test_data" \
        "$url/execute" 2>/dev/null || echo '{"error": "connection_failed"}')
    
    if echo "$response" | grep -q '"success".*true'; then
        echo -e "${GREEN}✅ $agent_name functionality test passed${NC}"
        echo -e "   Sample response: $(echo $response | head -c 100)..."
    else
        echo -e "${YELLOW}⚠️  $agent_name functionality test inconclusive${NC}"
        echo -e "   Response: $(echo $response | head -c 100)..."
    fi
}

# Main health check
total_agents=${#AGENTS[@]}
healthy_agents=0
failed_agents=()

echo -e "\n${BLUE}📊 Checking $total_agents agents...${NC}"

for agent in "${AGENTS[@]}"; do
    IFS=':' read -r name url <<< "$agent"
    
    if check_agent_health "$name" "$url"; then
        ((healthy_agents++))
        
        # Test functionality if agent is healthy
        test_agent_functionality "$name" "$url"
    else
        failed_agents+=("$name")
    fi
done

# Summary
echo -e "\n${BLUE}📋 Health Check Summary${NC}"
echo "========================="
echo -e "Total agents: $total_agents"
echo -e "Healthy agents: ${GREEN}$healthy_agents${NC}"
echo -e "Failed agents: ${RED}$((total_agents - healthy_agents))${NC}"

if [ ${#failed_agents[@]} -gt 0 ]; then
    echo -e "\n${RED}Failed agents:${NC}"
    for agent in "${failed_agents[@]}"; do
        echo -e "  • $agent"
    done
    echo -e "\n${YELLOW}💡 To start missing agents, run: ./scripts/run_agents.sh${NC}"
fi

if [ $healthy_agents -eq $total_agents ]; then
    echo -e "\n${GREEN}🎉 All agents are healthy and operational!${NC}"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some agents are not available${NC}"
    exit 1
fi
