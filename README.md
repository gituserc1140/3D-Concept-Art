# 3D Concept Art

Create 3D concept art prompts and generate Pollinations image URLs from a simple Streamlit interface.

[![View on GitHub](https://img.shields.io/badge/GitHub-Repository-181717?logo=github)](https://github.com/gituserc1140/3D-Concept-Art)
[![Sponsor on GitHub](https://img.shields.io/badge/GitHub-Sponsors-ea4aaa?logo=github-sponsors)](https://github.com/sponsors/gituserc1140)
[![Run with Streamlit](https://img.shields.io/badge/Streamlit-Run%20Locally-FF4B4B?logo=streamlit)](#run-locally)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=gituserc1140/3D-Concept-Art&branch=main&mainModule=app.py)

## What the app does

- Accepts a concept prompt and optional image parameters
- Builds a Pollinations image endpoint URL for 3D concept art generation
- Lets users test API settings from the Streamlit UI

## Project files

- `app.py` — Streamlit entrypoint and top-level controls
- `api_client.py` — API request helpers and Pollinations URL generation
- `ui.py` — result rendering helpers
- `config/settings.py` — configurable API defaults

## Run locally

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Start Streamlit
   ```bash
   streamlit run app.py
   ```

## Using the app

1. Set `API_BASE_URL` to your image API endpoint
2. For Pollinations, use a base URL such as `https://image.pollinations.ai`
3. Enter parameters as JSON, for example:
   ```json
   {
     "prompt": "cinematic 3D concept art spaceship hangar",
     "model": "flux",
     "width": 1024,
     "height": 1024
   }
   ```
4. Click **Generate concept**

## Configuration

- `config/settings.py` provides defaults for `API_BASE_URL`, `API_KEY`, and `DEFAULT_TIMEOUT`
- You can override `API_BASE_URL` and `API_KEY` with environment variables or by entering values in the Streamlit UI

## Notes

- If the app is still pointed at the placeholder example API, it returns sample content so the UI remains usable.

## License

This repository does not currently include a LICENSE file.
