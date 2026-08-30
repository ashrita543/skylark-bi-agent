"""
Root-level Streamlit entry point for Streamlit Cloud deployment.
This file ensures the 'app' package is properly recognized by Streamlit's module loader.
Imports and runs the actual application from app/main.py.
"""

# Import everything from the actual Streamlit app
from app.main import *  # noqa: F401, F403
