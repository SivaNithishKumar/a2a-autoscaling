#!/usr/bin/env python3
"""
Test Streamlit app to check dependencies
"""
import streamlit as st

st.set_page_config(
    page_title="Test A2A App",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Test A2A Multi-Agent App")
st.write("Testing basic functionality...")

# Test imports one by one
try:
    import asyncio
    st.success("✅ asyncio imported successfully")
except Exception as e:
    st.error(f"❌ asyncio error: {e}")

try:
    import httpx
    st.success("✅ httpx imported successfully")
except Exception as e:
    st.error(f"❌ httpx error: {e}")

try:
    from dotenv import load_dotenv
    st.success("✅ dotenv imported successfully")
except Exception as e:
    st.error(f"❌ dotenv error: {e}")

try:
    from openai import AzureOpenAI
    st.success("✅ openai imported successfully")
except Exception as e:
    st.error(f"❌ openai error: {e}")

try:
    from a2a.client import A2ACardResolver
    st.success("✅ a2a.client imported successfully")
except Exception as e:
    st.error(f"❌ a2a.client error: {e}")

st.write("If you see this, basic Streamlit is working!")