"""Test app imports."""

import sys
sys.path.insert(0, 'src')

try:
    import streamlit as st
    print("✅ Streamlit installed")
except ImportError:
    print("❌ Streamlit not installed. Run: pip install streamlit")

# Test imports
from app.manual_entry import get_fx_data
print("✅ App module imports successful")

print("\nTo run app: streamlit run app/manual_entry.py")
