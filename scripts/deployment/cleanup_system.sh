#!/bin/bash
# Cleanup script for Kubernetes A2A Multi-Agent System
# This script removes all deployed components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-multi-agent-a2a}"
FORCE="${FORCE:-false}"
KEEP_NAMESPACE="${KEEP_NAMESPACE:-false}"

echo -e "${BLUE}🧹 Cleaning up Kubernetes A2A Multi-Agent System${NC}"
echo "Namespace: $NAMESPACE"
echo "Force: $FORCE"
echo "Keep Namespace: $KEEP_NAMESPACE"
echo ""

# Function to confirm action
confirm_action() {
    if [ "$FORCE" = "true" ]; then
        return 0
    fi
    
    echo -e "${YELLOW}⚠️ This will delete all A2A system components in namespace '$NAMESPACE'${NC}"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️ Cleanup cancelled${NC}"
        exit 0
    fi
}

# Confirm the action
confirm_action

# Step 1: Delete autoscaling configurations
echo -e "${BLUE}📈 Removing autoscaling configurations...${NC}"
if kubectl get hpa -n $NAMESPACE >/dev/null 2>&1; then
    kubectl delete -f k8s/autoscaling/ --ignore-not-found=true
    echo -e "${GREEN}✅ Autoscaling configurations removed${NC}"
else
    echo -e "${YELLOW}⏭️ No autoscaling configurations found${NC}"
fi

# Step 2: Delete monitoring stack
echo -e "${BLUE}📊 Removing monitoring stack...${NC}"
if kubectl get deployment prometheus -n $NAMESPACE >/dev/null 2>&1 || \
   kubectl get deployment grafana -n $NAMESPACE >/dev/null 2>&1; then
    kubectl delete -f k8s/monitoring/ --ignore-not-found=true
    echo -e "${GREEN}✅ Monitoring stack removed${NC}"
else
    echo -e "${YELLOW}⏭️ No monitoring stack found${NC}"
fi

# Step 3: Delete agents
echo -e "${BLUE}🤖 Removing A2A agents...${NC}"
if kubectl get deployment -n $NAMESPACE | grep -q agent; then
    kubectl delete -f k8s/agents/ --ignore-not-found=true
    echo -e "${GREEN}✅ A2A agents removed${NC}"
else
    echo -e "${YELLOW}⏭️ No A2A agents found${NC}"
fi

# Step 4: Wait for pods to terminate
echo -e "${BLUE}⏳ Waiting for pods to terminate...${NC}"
timeout=60
while kubectl get pods -n $NAMESPACE 2>/dev/null | grep -q "Terminating\|Running" && [ $timeout -gt 0 ]; do
    echo -e "${YELLOW}⏳ Waiting for pods to terminate... ($timeout seconds remaining)${NC}"
    sleep 5
    timeout=$((timeout - 5))
done

# Step 5: Delete persistent volumes (if any)
echo -e "${BLUE}💾 Removing persistent volumes...${NC}"
if kubectl get pvc -n $NAMESPACE >/dev/null 2>&1; then
    kubectl delete pvc --all -n $NAMESPACE --ignore-not-found=true
    echo -e "${GREEN}✅ Persistent volumes removed${NC}"
else
    echo -e "${YELLOW}⏭️ No persistent volumes found${NC}"
fi

# Step 6: Delete namespace (if not keeping it)
if [ "$KEEP_NAMESPACE" = "false" ]; then
    echo -e "${BLUE}🗂️ Removing namespace...${NC}"
    if kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
        kubectl delete namespace $NAMESPACE --ignore-not-found=true
        echo -e "${GREEN}✅ Namespace removed${NC}"
    else
        echo -e "${YELLOW}⏭️ Namespace not found${NC}"
    fi
else
    echo -e "${YELLOW}⏭️ Keeping namespace as requested${NC}"
fi

# Step 7: Clean up Docker images (optional)
echo -e "${BLUE}🐳 Docker image cleanup (optional)${NC}"
echo -e "${YELLOW}ℹ️ To remove Docker images, run:${NC}"
echo "  docker rmi \$(docker images | grep 'a2a-.*-agent' | awk '{print \$3}')"
echo ""

# Step 8: Verify cleanup
echo -e "${BLUE}🔍 Verifying cleanup...${NC}"
if kubectl get namespace $NAMESPACE >/dev/null 2>&1; then
    remaining_resources=$(kubectl get all -n $NAMESPACE 2>/dev/null | wc -l)
    if [ $remaining_resources -gt 1 ]; then
        echo -e "${YELLOW}⚠️ Some resources may still exist in namespace $NAMESPACE:${NC}"
        kubectl get all -n $NAMESPACE
    else
        echo -e "${GREEN}✅ Namespace is clean${NC}"
    fi
else
    echo -e "${GREEN}✅ Namespace has been removed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Cleanup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 What was cleaned up:${NC}"
echo "  ✅ HPA configurations"
echo "  ✅ Monitoring stack (Prometheus, Grafana, AlertManager)"
echo "  ✅ A2A agents (all 6 agents)"
echo "  ✅ Services and deployments"
echo "  ✅ ConfigMaps and secrets"
echo "  ✅ Persistent volume claims"
if [ "$KEEP_NAMESPACE" = "false" ]; then
echo "  ✅ Namespace"
fi
echo ""
echo -e "${YELLOW}ℹ️ To redeploy the system, run:${NC}"
echo "  ./scripts/deployment/deploy_complete_system.sh"
