"""Streamlit entrypoint for the 3D concept art app.

The app gathers API settings and prompt parameters, then calls
api_client.fetch_data() to build or fetch concept art results. Rendering stays
delegated to ui.render_home().

Run locally:
  pip install -r requirements.txt
  streamlit run app.py
"""

import streamlit as st
from config import settings
import api_client
import ui

REPO_URL = "https://github.com/gituserc1140/3D-Concept-Art"

st.set_page_config(page_title="3D Concept Art", layout="centered")

st.header("3D Concept Art")
st.write("Generate 3D concept art prompts and image URLs from a lightweight Streamlit app.")
if hasattr(st, "link_button"):
    st.link_button("View on GitHub", REPO_URL, use_container_width=True)
else:
    st.markdown(f"[View on GitHub]({REPO_URL})")

# allow overriding API base and API key for quick testing; they default to config values
api_base = st.text_input("API base URL", value=settings.API_BASE_URL or "")
api_key = st.text_input("API key (optional)", value="", type="password")

params_input = st.text_area(
    "Parameters (JSON)",
    value='{"prompt":"cinematic 3D concept art spaceship hangar","model":"flux","width":1024,"height":1024}',
    help="Optional JSON to pass to fetch_data as params",
)

if st.button("Generate concept"):
    # parse params safely
    import json

    try:
        params = json.loads(params_input or "{}")
    except Exception as exc:
        st.error(f"Could not parse parameters as JSON: {exc}")
        params = {}

    # Temporary override of settings for this run (non-persistent)
    if api_base:
        settings.API_BASE_URL = api_base
    if api_key:
        # pass explicit api_key to fetch_data (preferred) and do not modify global settings
        data = api_client.fetch_data(params=params, api_key=api_key)
    else:
        data = api_client.fetch_data(params=params)

    ui.render_home(data)
else:
    st.info("Enter an API base URL or use the default configured in config/settings.py, provide your concept parameters, then click Generate concept.")
