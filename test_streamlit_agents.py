#!/usr/bin/env python3
"""
Test the Streamlit app agent discovery functionality
"""

import requests
import time

def test_streamlit_app():
    """Test if Streamlit app is working and can discover agents"""
    
    print("🧪 Testing Streamlit App")
    print("=" * 40)
    
    # Test app accessibility
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit app is accessible")
        else:
            print(f"❌ App returned status code: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot access app: {e}")
        return
    
    print("\n📋 App Testing Complete")
    print("\n🎯 Next Steps:")
    print("1. Open http://localhost:8501 in your browser")
    print("2. Click 'Discover Agents' button in the sidebar")
    print("3. Verify that all agents show as 'online'")
    print("4. Try sending a test message like: 'Calculate 15 + 25'")
    print("\n🔧 If agents still show as unavailable:")
    print("- Check pod logs: kubectl logs -f deployment/streamlit-a2a-app -n multi-agent-a2a")
    print("- Verify port forwarding: ps aux | grep 'kubectl.*port-forward'")

if __name__ == "__main__":
    test_streamlit_app()