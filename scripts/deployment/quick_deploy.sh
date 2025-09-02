#!/bin/bash
# Quick deployment script for development and testing
# Deploys only the essential components for rapid iteration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-multi-agent-a2a}"
AGENTS="${AGENTS:-base,calculator}"  # Default to essential agents only

echo -e "${BLUE}⚡ Quick Deploy - Kubernetes A2A Multi-Agent System${NC}"
echo "Namespace: $NAMESPACE"
echo "Agents: $AGENTS"
echo ""

# Function to deploy specific agent
deploy_agent() {
    local agent=$1
    echo -e "${YELLOW}🤖 Deploying ${agent} agent...${NC}"
    
    if [ -f "k8s/agents/${agent}-agent.yaml" ]; then
        kubectl apply -f "k8s/agents/${agent}-agent.yaml"
        echo -e "${GREEN}✅ ${agent} agent deployed${NC}"
    else
        echo -e "${RED}❌ ${agent} agent manifest not found${NC}"
    fi
}

# Step 1: Deploy namespace
echo -e "${BLUE}🏗️ Deploying namespace...${NC}"
kubectl apply -f k8s/agents/namespace.yaml

# Step 2: Deploy selected agents
echo -e "${BLUE}🤖 Deploying selected agents...${NC}"
IFS=',' read -ra AGENT_ARRAY <<< "$AGENTS"
for agent in "${AGENT_ARRAY[@]}"; do
    deploy_agent "$agent"
done

# Step 3: Wait for deployments
echo -e "${BLUE}⏳ Waiting for deployments...${NC}"
sleep 10

# Step 4: Show status
echo -e "${BLUE}📋 Current status:${NC}"
kubectl get pods -n $NAMESPACE
echo ""
kubectl get svc -n $NAMESPACE

echo ""
echo -e "${GREEN}⚡ Quick deployment completed!${NC}"
echo ""
echo -e "${YELLOW}🔗 Test endpoints:${NC}"
if [[ "$AGENTS" == *"base"* ]]; then
    echo "  Base Agent: kubectl port-forward -n $NAMESPACE svc/base-agent-service 8000:8080"
fi
if [[ "$AGENTS" == *"calculator"* ]]; then
    echo "  Calculator: kubectl port-forward -n $NAMESPACE svc/calculator-agent-service 8002:8080"
fi
echo ""
echo -e "${BLUE}ℹ️ For full deployment with monitoring, run:${NC}"
echo "  ./scripts/deployment/deploy_complete_system.sh"
