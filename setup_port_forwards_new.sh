#!/bin/bash

# 🚀 A2A Multi-Agent System - Access URLs Setup
# This script sets up port forwarding for easy access to all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

NAMESPACE="multi-agent-a2a"

echo -e "${CYAN}🌐 A2A Multi-Agent System - Access Setup${NC}"
echo -e "${CYAN}=======================================${NC}"
echo ""

echo -e "${BLUE}📊 System Status Overview${NC}"
kubectl get deployments -n $NAMESPACE

echo ""
echo -e "${BLUE}🔗 Setting up port forwarding for easy access...${NC}"
echo ""

# Function to start port forwarding
start_port_forward() {
    local service=$1
    local local_port=$2
    local remote_port=$3
    local description=$4
    
    echo -e "${YELLOW}🔗 Starting port-forward for $description...${NC}"
    kubectl port-forward -n $NAMESPACE svc/$service $local_port:$remote_port >/dev/null 2>&1 &
    echo -e "${GREEN}✅ $description available at: http://localhost:$local_port${NC}"
}

echo -e "${BLUE}🎨 Web Interfaces${NC}"
echo "=================="

# Start port forwarding for web interfaces
start_port_forward "grafana-service" "3000" "3000" "Grafana Dashboard"
start_port_forward "prometheus-service" "9090" "9090" "Prometheus Metrics"
start_port_forward "alertmanager-service" "9093" "9093" "AlertManager"
start_port_forward "streamlit-a2a-service" "8501" "8501" "Streamlit A2A App"

echo ""
echo -e "${BLUE}🤖 Agent Services${NC}"
echo "=================="

start_port_forward "base-agent-service" "8080" "8080" "Base Agent"
start_port_forward "calculator-agent-service" "8081" "8081" "Calculator Agent"
start_port_forward "weather-agent-service" "8082" "8082" "Weather Agent"
start_port_forward "research-agent-service" "8083" "8083" "Research Agent"
start_port_forward "move-orchestrator-service" "8004" "8004" "Move Orchestrator"
start_port_forward "infrastructure-monitor-service" "8005" "8005" "Infrastructure Monitor"

echo ""
echo -e "${CYAN}🌟 Quick Access URLs${NC}"
echo "==================="
echo -e "${GREEN}🎨 Streamlit A2A App:${NC}     http://localhost:8501"
echo -e "${GREEN}📊 Grafana Dashboard:${NC}     http://localhost:3000"
echo -e "${GREEN}🔍 Prometheus:${NC}            http://localhost:9090"
echo -e "${GREEN}🚨 AlertManager:${NC}          http://localhost:9093"
echo ""
echo -e "${BLUE}🤖 Agent Endpoints:${NC}"
echo "=================="
echo -e "${YELLOW}🔧 Base Agent:${NC}            http://localhost:8080"
echo -e "${YELLOW}🧮 Calculator Agent:${NC}      http://localhost:8081"
echo -e "${YELLOW}🌤️  Weather Agent:${NC}        http://localhost:8082"
echo -e "${YELLOW}🔬 Research Agent:${NC}        http://localhost:8083"
echo -e "${YELLOW}🎯 Move Orchestrator:${NC}     http://localhost:8004"
echo -e "${YELLOW}📈 Infrastructure Monitor:${NC} http://localhost:8005"
echo ""
echo -e "${BLUE}🔗 Useful Health Check URLs:${NC}"
echo "============================"
echo -e "${CYAN}Health Endpoints:${NC}"
echo "  • http://localhost:8080/health (Base Agent)"
echo "  • http://localhost:8081/health (Calculator)"
echo "  • http://localhost:8082/health (Weather)"
echo "  • http://localhost:8083/health (Research)"
echo "  • http://localhost:8004/health (Move Orchestrator)"
echo "  • http://localhost:8005/health (Infrastructure Monitor)"
echo ""
echo -e "${CYAN}Agent Cards:${NC}"
echo "  • http://localhost:8080/.well-known/agent-card.json"
echo "  • http://localhost:8081/.well-known/agent-card.json"
echo "  • http://localhost:8082/.well-known/agent-card.json"
echo "  • http://localhost:8083/.well-known/agent-card.json"
echo ""
echo -e "${GREEN}🎉 All services are now accessible!${NC}"
echo ""
echo -e "${YELLOW}📝 Note: Port forwarding is running in the background.${NC}"
echo -e "${YELLOW}   To stop all port forwards, run: pkill -f 'kubectl port-forward'${NC}"
echo ""
echo -e "${BLUE}🛠️  Management Commands:${NC}"
echo "====================="
echo -e "${CYAN}• Check system health:${NC}       ./scripts/validation/simple_health_check.sh"
echo -e "${CYAN}• View pod status:${NC}           kubectl get pods -n multi-agent-a2a"
echo -e "${CYAN}• View HPA status:${NC}           kubectl get hpa -n multi-agent-a2a"
echo -e "${CYAN}• View services:${NC}             kubectl get services -n multi-agent-a2a"
echo -e "${CYAN}• Kill port forwards:${NC}        pkill -f 'kubectl port-forward'"
echo ""