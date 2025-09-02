#!/bin/bash
# Complete A2A Multi-Agent System Kubernetes Deployment with Autoscaling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="multi-agent-a2a"
TIMEOUT="300s"

echo -e "${BLUE}🚀 Deploying Complete A2A Multi-Agent System with Autoscaling${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Namespace: $NAMESPACE"
echo "Timeout: $TIMEOUT"
echo ""

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
        exit 1
    fi
    
    # Check if we can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ kubectl is available and connected to cluster${NC}"
}

# Function to create namespace
create_namespace() {
    echo -e "${YELLOW}📁 Creating namespace...${NC}"
    
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Namespace $NAMESPACE created/updated${NC}"
    else
        echo -e "${RED}❌ Failed to create namespace${NC}"
        exit 1
    fi
}

# Function to apply configuration
apply_config() {
    echo -e "${YELLOW}⚙️  Applying secrets and configuration...${NC}"
    
    # Apply namespace and basic config first
    kubectl apply -f "$PROJECT_ROOT/k8s/agents/namespace.yaml"
    
    # Wait a moment for namespace to be ready
    sleep 2
    
    echo -e "${GREEN}✅ Configuration applied${NC}"
}

# Function to deploy monitoring stack
deploy_monitoring() {
    echo -e "${YELLOW}📊 Deploying monitoring stack...${NC}"
    
    # Apply monitoring components
    if [ -d "$PROJECT_ROOT/k8s/monitoring" ]; then
        kubectl apply -f "$PROJECT_ROOT/k8s/monitoring/"
        
        echo -e "${CYAN}⏳ Waiting for Prometheus to be ready...${NC}"
        kubectl wait --for=condition=ready pod -l app=prometheus -n "$NAMESPACE" --timeout="$TIMEOUT" || true
        
        echo -e "${GREEN}✅ Monitoring stack deployed${NC}"
    else
        echo -e "${YELLOW}⚠️  Monitoring directory not found, skipping...${NC}"
    fi
}

# Function to deploy agents
deploy_agents() {
    echo -e "${YELLOW}🤖 Deploying A2A agents...${NC}"
    
    # Apply agent deployments
    if [ -d "$PROJECT_ROOT/k8s/agents" ]; then
        # Apply all agent manifests except namespace (already applied)
        find "$PROJECT_ROOT/k8s/agents" -name "*.yaml" ! -name "namespace.yaml" -exec kubectl apply -f {} \;
        
        echo -e "${CYAN}⏳ Waiting for agents to be ready...${NC}"
        
        # Wait for each agent deployment
        local agents=("base-agent" "calculator-agent" "weather-agent" "research-agent" "move-orchestrator-agent" "infrastructure-monitor-agent")
        
        for agent in "${agents[@]}"; do
            echo -e "${CYAN}Waiting for $agent...${NC}"
            kubectl wait --for=condition=available deployment/"$agent" -n "$NAMESPACE" --timeout="$TIMEOUT" || true
        done
        
        echo -e "${GREEN}✅ A2A agents deployed${NC}"
    else
        echo -e "${RED}❌ Agents directory not found${NC}"
        exit 1
    fi
}

# Function to deploy autoscaling
deploy_autoscaling() {
    echo -e "${YELLOW}📈 Applying autoscaling configuration...${NC}"
    
    if [ -d "$PROJECT_ROOT/k8s/autoscaling" ]; then
        kubectl apply -f "$PROJECT_ROOT/k8s/autoscaling/"
        
        echo -e "${CYAN}⏳ Waiting for HPA to be ready...${NC}"
        sleep 10
        
        echo -e "${GREEN}✅ Autoscaling configuration applied${NC}"
    else
        echo -e "${YELLOW}⚠️  Autoscaling directory not found, skipping...${NC}"
    fi
}

# Function to deploy ingress
deploy_ingress() {
    echo -e "${YELLOW}🌐 Deploying ingress...${NC}"
    
    if [ -f "$PROJECT_ROOT/k8s/ingress/ingress.yaml" ]; then
        kubectl apply -f "$PROJECT_ROOT/k8s/ingress/"
        echo -e "${GREEN}✅ Ingress deployed${NC}"
    else
        echo -e "${YELLOW}⚠️  Ingress configuration not found, skipping...${NC}"
    fi
}

# Function to verify deployment
verify_deployment() {
    echo -e "${BLUE}🔍 Verifying deployment...${NC}"
    
    echo -e "${CYAN}Pods:${NC}"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    echo -e "\n${CYAN}Services:${NC}"
    kubectl get svc -n "$NAMESPACE"
    
    echo -e "\n${CYAN}HPA Status:${NC}"
    kubectl get hpa -n "$NAMESPACE"
    
    echo -e "\n${CYAN}Deployments:${NC}"
    kubectl get deployments -n "$NAMESPACE"
    
    # Check if all pods are running
    local not_running=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    
    if [ "$not_running" -eq 0 ]; then
        echo -e "\n${GREEN}✅ All pods are running${NC}"
    else
        echo -e "\n${YELLOW}⚠️  $not_running pods are not running${NC}"
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running
    fi
}

# Function to show access information
show_access_info() {
    echo -e "\n${BLUE}🎯 Access Information:${NC}"
    
    # Get service information
    echo -e "${CYAN}Agent Endpoints:${NC}"
    kubectl get svc -n "$NAMESPACE" -o custom-columns="NAME:.metadata.name,TYPE:.spec.type,CLUSTER-IP:.spec.clusterIP,EXTERNAL-IP:.status.loadBalancer.ingress[0].ip,PORT:.spec.ports[0].port"
    
    echo -e "\n${CYAN}Monitoring:${NC}"
    echo "  📊 Grafana: kubectl port-forward svc/grafana 3000:3000 -n $NAMESPACE"
    echo "  🔍 Prometheus: kubectl port-forward svc/prometheus 9090:9090 -n $NAMESPACE"
    
    echo -e "\n${CYAN}Agent Access (via port-forward):${NC}"
    echo "  🤖 Base Agent: kubectl port-forward svc/base-agent-service 8080:8080 -n $NAMESPACE"
    echo "  🧮 Calculator: kubectl port-forward svc/calculator-agent-service 8081:8081 -n $NAMESPACE"
    echo "  🌤️  Weather: kubectl port-forward svc/weather-agent-service 8082:8082 -n $NAMESPACE"
    echo "  🔬 Research: kubectl port-forward svc/research-agent-service 8083:8083 -n $NAMESPACE"
    echo "  🏗️  Move Orchestrator: kubectl port-forward svc/move-orchestrator-service 8004:8004 -n $NAMESPACE"
    echo "  📊 Infrastructure Monitor: kubectl port-forward svc/infrastructure-monitor-service 8005:8005 -n $NAMESPACE"
}

# Function to show next steps
show_next_steps() {
    echo -e "\n${BLUE}🎯 Next Steps:${NC}"
    echo "1. Monitor deployment: watch kubectl get pods -n $NAMESPACE"
    echo "2. Check HPA status: kubectl get hpa -n $NAMESPACE"
    echo "3. View logs: kubectl logs -f deployment/base-agent -n $NAMESPACE"
    echo "4. Run load tests: ./scripts/load_test_autoscaling.py"
    echo "5. Access Grafana dashboard for monitoring"
    
    echo -e "\n${YELLOW}💡 Troubleshooting:${NC}"
    echo "  • Check pod logs: kubectl logs <pod-name> -n $NAMESPACE"
    echo "  • Describe resources: kubectl describe <resource> <name> -n $NAMESPACE"
    echo "  • Check events: kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp'"
}

# Main execution
main() {
    echo -e "${BLUE}Starting deployment process...${NC}\n"
    
    # Step 1: Pre-flight checks
    check_kubectl
    
    # Step 2: Create namespace
    create_namespace
    
    # Step 3: Apply configuration
    apply_config
    
    # Step 4: Deploy monitoring stack
    deploy_monitoring
    
    # Step 5: Deploy agents
    deploy_agents
    
    # Step 6: Deploy autoscaling
    deploy_autoscaling
    
    # Step 7: Deploy ingress
    deploy_ingress
    
    # Step 8: Verify deployment
    verify_deployment
    
    # Step 9: Show access information
    show_access_info
    
    # Step 10: Show next steps
    show_next_steps
    
    echo -e "\n${GREEN}🎉 Deployment complete!${NC}"
    echo -e "${GREEN}✅ A2A Multi-Agent System with Autoscaling is ready!${NC}"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "verify")
        verify_deployment
        ;;
    "info")
        show_access_info
        ;;
    "help")
        echo "Usage: $0 [deploy|verify|info|help]"
        echo "  deploy: Full deployment (default)"
        echo "  verify: Verify existing deployment"
        echo "  info: Show access information"
        echo "  help: Show this help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
