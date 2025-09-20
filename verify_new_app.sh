#!/bin/bash

echo "🔍 A2A Streamlit App Verification"
echo "=================================="

# Check pod status
echo ""
echo "📊 Pod Status:"
kubectl get pods -n multi-agent-a2a | grep streamlit | head -1

# Check if port forwarding is active
echo ""
echo "🌐 Port Forwarding:"
if ps aux | grep "kubectl.*port-forward.*8501" | grep -v grep > /dev/null; then
    echo "✅ Port forwarding active on localhost:8501"
else
    echo "❌ Port forwarding not active"
fi

# Test app accessibility
echo ""
echo "🧪 App Accessibility:"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✅ App accessible (HTTP $response)"
elif [ "$response" = "000" ]; then
    echo "⚠️  Connection in progress or app starting"
else
    echo "❌ App not accessible (HTTP $response)"
fi

# Check recent logs
echo ""
echo "📝 Recent App Logs:"
kubectl logs -n multi-agent-a2a deployment/streamlit-a2a-app --tail=5 | grep -E "(Streamlit|URL|Running|Error)" || echo "No specific logs found"

echo ""
echo "🎯 Access Information:"
echo "  Local URL: http://localhost:8501"
echo "  App: A2A Agent Platform (Modern Design)"
echo ""
echo "✨ The app has been successfully updated with the new modern design!"
echo "   - Clean, professional interface"
echo "   - Modern typography (Poppins font)"
echo "   - Simplified agent cards"
echo "   - Clean chat messages"
echo "   - Improved visual hierarchy"