#!/bin/bash

# Enhanced Multi-Agent A2A System Startup Script
# Starts complete monitoring stack with all AI-Ops agents
# Production-ready deployment for Just Move In interview demo

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS_DIR="${PROJECT_DIR}/logs"
MONITORING_DIR="${PROJECT_DIR}/monitoring"

# Agent ports
BASE_AGENT_PORT=8080
CALCULATOR_AGENT_PORT=8081
WEATHER_AGENT_PORT=8082
RESEARCH_AGENT_PORT=8083
MOVE_ORCHESTRATOR_PORT=8004
INFRASTRUCTURE_MONITOR_PORT=8005

# Monitoring ports
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Agent PIDs
declare -a AGENT_PIDS=()

echo -e "${CYAN}🚀 Multi-Agent A2A System - Enhanced Startup${NC}"
echo -e "${CYAN}============================================${NC}"
echo "Starting complete AI-Ops system with monitoring stack..."
echo "Project Directory: ${PROJECT_DIR}"
echo ""

# Function to clean up on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down all services...${NC}"
    
    # Kill all agent processes
    for pid in "${AGENT_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping process $pid..."
            kill "$pid" 2>/dev/null || true
        fi
    done
    
    # Kill monitoring stack
    echo "Stopping monitoring stack..."
    pkill -f prometheus 2>/dev/null || true
    pkill -f grafana 2>/dev/null || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
}

# Set up signal handlers
trap cleanup EXIT
trap cleanup INT
trap cleanup TERM

# Create logs directory
mkdir -p "${LOGS_DIR}"

# Function to wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1
    
    echo -n "Waiting for ${service_name} to be ready"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e " ${RED}❌ Failed${NC}"
    return 1
}

# Function to start agent
start_agent() {
    local agent_name="$1"
    local agent_module="$2"
    local port="$3"
    local description="$4"
    
    echo -e "${BLUE}📦 Starting ${agent_name}...${NC}"
    echo "   Description: ${description}"
    echo "   Port: ${port}"
    echo "   Module: ${agent_module}"
    
    cd "${PROJECT_DIR}"
    nohup uv run python -m "${agent_module}" > "${LOGS_DIR}/${agent_name}.log" 2>&1 &
    local pid=$!
    AGENT_PIDS+=($pid)
    
    echo "   PID: ${pid}"
    
    # Wait for agent to be ready
    if wait_for_service "${agent_name}" "http://localhost:${port}/health" || wait_for_service "${agent_name}" "http://localhost:${port}/.well-known/agent-card.json"; then
        echo -e "   ${GREEN}✅ ${agent_name} started successfully${NC}"
    else
        echo -e "   ${RED}❌ ${agent_name} failed to start${NC}"
        return 1
    fi
    echo ""
}

# Function to start monitoring
start_monitoring() {
    echo -e "${YELLOW}📊 Starting Monitoring Stack...${NC}"
    
    # Check if monitoring tools are available
    if ! command -v prometheus > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Prometheus not installed - monitoring will be limited to agent metrics${NC}"
        echo "   Install Prometheus for full monitoring capabilities"
        echo "   Agent metrics available at: http://localhost:8080-8085/metrics"
        return 0
    fi
    
    # Start Prometheus
    echo -e "${BLUE}🔍 Starting Prometheus...${NC}"
    cd "${PROJECT_DIR}"
    nohup prometheus --config.file="${MONITORING_DIR}/prometheus/config.yml" \
                    --storage.tsdb.path="${LOGS_DIR}/prometheus" \
                    --web.console.libraries=/usr/share/prometheus/console_libraries \
                    --web.console.templates=/usr/share/prometheus/consoles \
                    --web.listen-address="0.0.0.0:${PROMETHEUS_PORT}" \
                    > "${LOGS_DIR}/prometheus.log" 2>&1 &
    local prometheus_pid=$!
    AGENT_PIDS+=($prometheus_pid)
    
    if wait_for_service "Prometheus" "http://localhost:${PROMETHEUS_PORT}"; then
        echo -e "   ${GREEN}✅ Prometheus started on port ${PROMETHEUS_PORT}${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Prometheus may take longer to start${NC}"
    fi
    
    # Start Grafana if available
    if command -v grafana-server > /dev/null 2>&1; then
        echo -e "${BLUE}📈 Starting Grafana...${NC}"
        nohup grafana-server --homepath=/usr/share/grafana \
                           --config=/etc/grafana/grafana.ini \
                           cfg:default.server.http_port=${GRAFANA_PORT} \
                           > "${LOGS_DIR}/grafana.log" 2>&1 &
        local grafana_pid=$!
        AGENT_PIDS+=($grafana_pid)
        
        if wait_for_service "Grafana" "http://localhost:${GRAFANA_PORT}"; then
            echo -e "   ${GREEN}✅ Grafana started on port ${GRAFANA_PORT}${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Grafana may take longer to start${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Grafana not installed - skipping dashboard setup${NC}"
    fi
    
    echo ""
}

# Function to show system status
show_status() {
    echo -e "${CYAN}📋 System Status Overview${NC}"
    echo -e "${CYAN}========================${NC}"
    echo ""
    
    echo -e "${GREEN}🤖 AI-Ops Agents:${NC}"
    echo "   • Base Agent:              http://localhost:${BASE_AGENT_PORT}/"
    echo "   • Calculator Agent:        http://localhost:${CALCULATOR_AGENT_PORT}/"
    echo "   • Weather Agent:           http://localhost:${WEATHER_AGENT_PORT}/"
    echo "   • Research Agent:          http://localhost:${RESEARCH_AGENT_PORT}/"
    echo "   • Move Orchestrator:       http://localhost:${MOVE_ORCHESTRATOR_PORT}/"
    echo "   • Infrastructure Monitor:  http://localhost:${INFRASTRUCTURE_MONITOR_PORT}/"
    echo ""
    
    echo -e "${YELLOW}📊 Monitoring & Metrics:${NC}"
    echo "   • Agent Metrics:"
    echo "     - Base Agent:            http://localhost:${BASE_AGENT_PORT}/metrics"
    echo "     - Calculator Agent:      http://localhost:${CALCULATOR_AGENT_PORT}/metrics"
    echo "     - Weather Agent:         http://localhost:${WEATHER_AGENT_PORT}/metrics"
    echo "     - Research Agent:        http://localhost:${RESEARCH_AGENT_PORT}/metrics"
    echo "     - Move Orchestrator:     http://localhost:8084/metrics"
    echo "     - Infrastructure Monitor: http://localhost:8085/metrics"
    
    if command -v prometheus > /dev/null 2>&1; then
        echo "   • Prometheus:            http://localhost:${PROMETHEUS_PORT}/"
    fi
    
    if command -v grafana-server > /dev/null 2>&1; then
        echo "   • Grafana Dashboard:     http://localhost:${GRAFANA_PORT}/"
        echo "     (admin/admin for login)"
    fi
    echo ""
    
    echo -e "${BLUE}🎯 Demo Capabilities:${NC}"
    echo "   • Complete Move Orchestration with AI optimization"
    echo "   • Infrastructure Monitoring with anomaly detection"
    echo "   • Predictive failure analysis and recommendations"
    echo "   • Real-time metrics collection and visualization"
    echo "   • Production-ready A2A agent communication"
    echo ""
    
    echo -e "${GREEN}🚀 System Ready for Just Move In Demo!${NC}"
    echo ""
}

# Function to run system tests
run_quick_tests() {
    echo -e "${BLUE}🧪 Running Quick System Tests...${NC}"
    
    # Test each agent's health
    local agents=(
        "Base Agent:localhost:${BASE_AGENT_PORT}"
        "Calculator Agent:localhost:${CALCULATOR_AGENT_PORT}"
        "Weather Agent:localhost:${WEATHER_AGENT_PORT}"
        "Research Agent:localhost:${RESEARCH_AGENT_PORT}"
        "Move Orchestrator:localhost:${MOVE_ORCHESTRATOR_PORT}"
        "Infrastructure Monitor:localhost:${INFRASTRUCTURE_MONITOR_PORT}"
    )
    
    local test_passed=0
    local test_total=${#agents[@]}
    
    for agent_info in "${agents[@]}"; do
        IFS=':' read -r name host port <<< "$agent_info"
        
        echo -n "Testing ${name}... "
        if curl -s "http://${host}:${port}/.well-known/agent-card.json" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ PASS${NC}"
            ((test_passed++))
        else
            echo -e "${RED}❌ FAIL${NC}"
        fi
    done
    
    echo ""
    echo -e "${CYAN}Test Results: ${test_passed}/${test_total} agents responding${NC}"
    
    if [ $test_passed -eq $test_total ]; then
        echo -e "${GREEN}🎉 All agents are healthy and ready!${NC}"
    else
        echo -e "${YELLOW}⚠️  Some agents may need more time to start${NC}"
    fi
    echo ""
}

# Main execution
main() {
    # Change to project directory
    cd "${PROJECT_DIR}"
    
    echo -e "${BLUE}🔧 Environment Setup${NC}"
    echo "Syncing dependencies..."
    uv sync --quiet
    echo -e "${GREEN}✅ Dependencies ready${NC}"
    echo ""
    
    # Start monitoring stack first
    start_monitoring
    
    # Start all agents
    echo -e "${GREEN}🤖 Starting AI-Ops Agents${NC}"
    echo -e "${GREEN}========================${NC}"
    
    # Core agents
    start_agent "Base Agent" "src.multi_agent_a2a.agents.base" $BASE_AGENT_PORT "General purpose AI assistant"
    start_agent "Calculator Agent" "src.multi_agent_a2a.agents.calculator" $CALCULATOR_AGENT_PORT "Mathematical calculations and computations"
    start_agent "Weather Agent" "src.multi_agent_a2a.agents.weather" $WEATHER_AGENT_PORT "Weather information and forecasts"
    start_agent "Research Agent" "src.multi_agent_a2a.agents.research" $RESEARCH_AGENT_PORT "Research and information gathering"
    
    # AI-Ops specialized agents
    start_agent "Move Orchestrator" "src.multi_agent_a2a.agents.move_orchestrator" $MOVE_ORCHESTRATOR_PORT "AI-powered move orchestration with timeline optimization"
    start_agent "Infrastructure Monitor" "src.multi_agent_a2a.agents.infrastructure_monitor" $INFRASTRUCTURE_MONITOR_PORT "Infrastructure monitoring with anomaly detection"
    
    # Show system status
    show_status
    
    # Run quick tests
    run_quick_tests
    
    # Keep the script running
    echo -e "${CYAN}💫 System is running... Press Ctrl+C to stop${NC}"
    echo "View logs in: ${LOGS_DIR}/"
    echo ""
    
    # Wait for user interrupt
    while true; do
        sleep 10
        # Optional: Could add periodic health checks here
    done
}

# Run main function
main "$@"