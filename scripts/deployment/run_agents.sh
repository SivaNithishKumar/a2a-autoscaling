#!/bin/bash

# Multi-Agent A2A System - Distributed Agent Runner
# This script starts independent A2A agents (no centralized engine)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_EXEC="uv run python"

echo -e "${BLUE}🚀 Multi-Agent A2A System - Distributed Agent Runner${NC}"
echo "====================================================="
echo -e "${YELLOW}📝 Note: This runs independent A2A agents (no centralized engine)${NC}"

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to start an agent
start_agent() {
    local agent_name=$1
    local port=$2
    local module_path=$3
    
    echo -e "\n${YELLOW}🤖 Starting $agent_name on port $port...${NC}"
    
    if ! check_port $port; then
        echo -e "${RED}Skipping $agent_name - port conflict${NC}"
        return 1
    fi
    
    # Start the agent in background using module execution
    cd "$PROJECT_ROOT"
    $PYTHON_EXEC -m "$module_path" --port $port &
    local pid=$!
    
    # Store PID for cleanup
    echo $pid >> /tmp/a2a_agents.pids
    
    echo -e "${GREEN}✅ $agent_name started with PID $pid${NC}"
    return 0
}

# Function to check if agents are implemented
check_implementation() {
    local agent_path=$1
    local agent_name=$2
    
    if [ ! -f "$agent_path" ]; then
        echo -e "${YELLOW}⚠️  $agent_name not implemented yet - skipping${NC}"
        return 1
    fi
    return 0
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up agents...${NC}"
    if [ -f /tmp/a2a_agents.pids ]; then
        while read pid; do
            if kill -0 $pid 2>/dev/null; then
                echo -e "${YELLOW}Stopping agent with PID $pid${NC}"
                kill $pid
            fi
        done < /tmp/a2a_agents.pids
        rm -f /tmp/a2a_agents.pids
    fi
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Create PID file
rm -f /tmp/a2a_agents.pids
touch /tmp/a2a_agents.pids

echo -e "\n${BLUE}📋 Checking implementation status...${NC}"

# Check environment
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}❌ .env file not found. Please copy .env.example and configure it.${NC}"
    exit 1
fi

# Check if virtual environment is activated
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv package manager not found. Please install uv.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment checks passed${NC}"

# Start agents (checking if they're implemented)
echo -e "\n${BLUE}🚀 Starting independent A2A agents...${NC}"

# Base Agent - Port 8000
if check_implementation "$PROJECT_ROOT/src/multi_agent_a2a/agents/base/__main__.py" "Base Agent"; then
    start_agent "Base Agent" 8000 "multi_agent_a2a.agents.base"
fi

# Weather Agent - Port 8001
if check_implementation "$PROJECT_ROOT/src/multi_agent_a2a/agents/weather/main.py" "Weather Agent"; then
    start_agent "Weather Agent" 8001 "multi_agent_a2a.agents.weather.main"
fi

# Calculator Agent - Port 8002  
if check_implementation "$PROJECT_ROOT/src/multi_agent_a2a/agents/calculator/main.py" "Calculator Agent"; then
    start_agent "Calculator Agent" 8002 "multi_agent_a2a.agents.calculator.main"
fi

# Research Agent - Port 8003
if check_implementation "$PROJECT_ROOT/src/multi_agent_a2a/agents/research/main.py" "Research Agent"; then
    start_agent "Research Agent" 8003 "multi_agent_a2a.agents.research.main"
fi

echo -e "\n${GREEN}🎉 All available independent agents started!${NC}"
echo -e "${BLUE}📊 Agent Status:${NC}"
echo "  • Base Agent (General AI): http://localhost:8000" 
echo "  • Weather Agent: http://localhost:8001" 
echo "  • Calculator Agent: http://localhost:8002"
echo "  • Research Agent: http://localhost:8003"

echo -e "\n${YELLOW}💡 Tips:${NC}"
echo "  • Use Ctrl+C to stop all agents"
echo "  • Check logs for debugging information"
echo "  • Test A2A communication: ./scripts/test_agents.sh"
echo "  • Monitor health: ./scripts/health_check.sh"
echo "  • No centralized engine - agents run independently"

echo -e "\n${BLUE}🔄 Independent agents running... Press Ctrl+C to stop${NC}"

# Wait for interrupt
while true; do
    sleep 1
done
