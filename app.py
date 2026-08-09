"""Streamlit entrypoint for the 3D Concept Art Generator.

Generates 3D concept art images via Pollinations.AI directly from a Streamlit
Cloud-compatible single-file app.  No external API key is required.

Run locally:
  pip install -r requirements.txt
  streamlit run app.py

Deploy on Streamlit Cloud:
  Point the app at this repository and set the main file to app.py.
"""

import urllib.parse

import requests
import streamlit as st

# ── Constants ──────────────────────────────────────────────────────────────────
_GITHUB_URL = "https://github.com/gituserc1140/3D-Concept-Art"
_SPONSOR_URL = "https://github.com/sponsors/gituserc1140"
_STREAMLIT_APP_URL = "https://3d-concept-art-u9nsolcjujhw9ngtx9vxks.streamlit.app/"
_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}"

# ── CSS ────────────────────────────────────────────────────────────────────────
_CSS = """
<style>
/* ── Page background ───────────────────────────────────────────── */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0a1a, #1a1040, #0d1b2a);
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent; }

/* ── Hero banner ───────────────────────────────────────────────── */
.hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
}
.hero h1 {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, #a78bfa, #38bdf8, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
}
.hero p {
    color: #94a3b8;
    font-size: 1.05rem;
    margin-top: 0;
}

/* ── Result card ───────────────────────────────────────────────── */
.result-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(167,139,250,0.35);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    color: #e2e8f0;
    font-size: 1rem;
    line-height: 1.8;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
.section-label {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #38bdf8;
    margin-bottom: 0.4rem;
}

/* ── Error card ────────────────────────────────────────────────── */
.error-card {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.45);
    border-radius: 14px;
    padding: 1.2rem 1.6rem;
    color: #fca5a5;
    font-size: 0.97rem;
    margin-top: 1rem;
}

/* ── Buttons ───────────────────────────────────────────────────── */
[data-testid="stButton"] button {
    background: linear-gradient(135deg, #7c3aed, #0ea5e9) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.45rem 1.4rem !important;
    font-weight: 600 !important;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] button:hover { opacity: 0.85 !important; }

/* ── Sidebar ───────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(10,10,26,0.9);
    border-right: 1px solid rgba(167,139,250,0.2);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div { color: #94a3b8 !important; }
[data-testid="stSidebar"] h2 {
    color: #a78bfa !important;
    font-size: 1.1rem;
}

/* ── GitHub buttons ────────────────────────────────────────────── */
.gh-buttons {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 1rem;
}
.gh-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    text-decoration: none !important;
    transition: opacity 0.2s;
}
.gh-btn:hover { opacity: 0.82; }
.gh-btn-github {
    background: #24292f;
    color: #ffffff !important;
    border: 1px solid #444c56;
}
.gh-btn-sponsor {
    background: #bf3989;
    color: #ffffff !important;
    border: 1px solid #9e2d6f;
}
.gh-btn-streamlit {
    background: #ff4b4b;
    color: #ffffff !important;
    border: 1px solid #cc3c3c;
}

/* ── Warning / spinner ─────────────────────────────────────────── */
[data-testid="stAlert"] p { color: #ffffff !important; }
[data-testid="stSpinner"] p { color: #a78bfa !important; }

/* ── Selects / text inputs ─────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select,
textarea {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(167,139,250,0.3) !important;
    color: #f1f5f9 !important;
    border-radius: 8px !important;
}
</style>
"""

# ── Style options exposed to the user ──────────────────────────────────────────
# Generic art styles
_STYLE_OPTIONS_GENERAL = [
    "cinematic",
    "sci-fi",
    "fantasy",
    "cyberpunk",
    "steampunk",
    "post-apocalyptic",
    "dark fantasy",
    "photorealistic",
]

# 3D-print-focused styles with dedicated prompt templates
_STYLE_OPTIONS_3D_PRINT = [
    "3D print ready",
    "miniature figurine",
    "architectural model",
    "technical blueprint",
    "resin print concept",
    "sketch 3D print",
]

_STYLE_OPTIONS = _STYLE_OPTIONS_3D_PRINT + _STYLE_OPTIONS_GENERAL

# 3D-print-relevant subject presets
_SUBJECT_OPTIONS = [
    "figurine character",
    "terrain tile",
    "terrain scatter piece",
    "architectural facade detail",
    "mechanical assembly",
    "miniature creature",
    "jewellery / ring design",
    "cosplay prop",
    "abstract sculpture",
    "modular dungeon tile",
]

# Aspect ratio presets (label → (width, height))
_ASPECT_PRESETS = {
    "1:1 Square — single piece (1024×1024)": (1024, 1024),
    "3:4 Portrait — tall figurine (768×1024)": (768, 1024),
    "4:3 Landscape — terrain tile (1024×768)": (1024, 768),
    "16:9 Wide — panoramic scene (1024×576)": (1024, 576),
}

# ── Prompt templates per 3D-print style ───────────────────────────────────────

_PRINT_STYLE_PROMPTS = {
    "3D print ready": (
        "3D print ready concept art, {concept}. "
        "Clean geometry optimised for FDM printing, visible wall thickness, "
        "minimal overhangs, support-free design where possible, "
        "uniform neutral lighting to reveal surface topology, white studio background, "
        "professional product render, sharp edges."
    ),
    "miniature figurine": (
        "miniature figurine concept art, {concept}. "
        "Tabletop-scale figurine design, heroic proportions, "
        "exaggerated detail for small-scale printing, textured base included, "
        "neutral grey material preview, soft studio lighting, "
        "28mm scale miniature aesthetic."
    ),
    "architectural model": (
        "architectural scale model concept art, {concept}. "
        "Cross-section view showing internal structure, "
        "clean white model aesthetic, layer lines suggested, "
        "precise geometric forms, professional architectural illustration, "
        "isometric perspective, monochrome with accent colour highlights."
    ),
    "technical blueprint": (
        "technical blueprint concept art, {concept}. "
        "Engineering drawing style, orthographic projection, "
        "dimension lines and annotations, grid paper background, "
        "cyan-on-navy blueprint colour scheme, fine line detail, "
        "sectional view, 3D printable assembly breakdown."
    ),
    "resin print concept": (
        "resin 3D print concept art, {concept}. "
        "High-detail resin print aesthetic, ultra-fine surface detail, "
        "smooth organic curves, translucent material preview, "
        "SLA/MSLA layer resolution implied, dramatic backlit studio lighting, "
        "jewellery-quality finish, intricate filigree detail."
    ),
    "sketch 3D print": (
        "sketch-style 3D print concept art, {concept}. "
        "Hand-drawn pencil sketch aesthetic, 3D printable figurine design, "
        "detailed line art, blueprint style, technical illustration, "
        "white background with fine ink lines."
    ),
}


# ── Image generation ───────────────────────────────────────────────────────────

def build_prompt(concept: str, style: str) -> str:
    """Construct the full image-generation prompt for the given style."""
    if style in _PRINT_STYLE_PROMPTS:
        return _PRINT_STYLE_PROMPTS[style].format(concept=concept)
    return (
        f"3D concept art, {style} style, {concept}. "
        "Highly detailed, dramatic lighting, cinematic composition, "
        "professional 3D render, 8K resolution."
    )


def generate_image(
    concept: str,
    style: str,
    width: int = 1024,
    height: int = 1024,
    seed: int | None = None,
) -> tuple[bytes, str]:
    """Fetch a 3D concept art image from Pollinations.AI.

    Returns a tuple of (image_bytes, prompt_used).
    """
    prompt = build_prompt(concept, style)
    query: dict = {
        "width": width,
        "height": height,
        "nologo": "true",
        "model": "flux",
    }
    if seed is not None:
        query["seed"] = seed
    params = urllib.parse.urlencode(query)
    url = f"{_POLLINATIONS_BASE.format(prompt=urllib.parse.quote(prompt))}?{params}"
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            "Could not connect to Pollinations.AI — check your internet connection."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "Request to Pollinations.AI timed out — please try again."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Pollinations.AI returned an error ({exc.response.status_code}). "
            "Please try a different prompt or try again later."
        ) from exc
    return response.content, prompt


# ── Main app ───────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="3D Concept Art Generator",
        layout="centered",
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Hero header ────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero">
            <h1>3D Concept Art Generator</h1>
            <p>Describe your scene and instantly generate stunning 3D concept art.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Sidebar ────────────────────────────────────────────────────
    st.sidebar.header("Settings")

    aspect_label = st.sidebar.selectbox(
        "Print bed aspect ratio",
        list(_ASPECT_PRESETS.keys()),
        index=0,
    )
    width, height = _ASPECT_PRESETS[aspect_label]

    seed_enabled = st.sidebar.checkbox("Fix random seed (reproducible results)", value=False)
    seed: int | None = None
    if seed_enabled:
        seed = st.sidebar.number_input("Seed", min_value=0, max_value=2**31 - 1, value=42, step=1)

    compare_mode = st.sidebar.checkbox("Side-by-side style comparison", value=False)

    st.sidebar.markdown(
        f"""
        <div class="gh-buttons">
            <a class="gh-btn gh-btn-streamlit" href="{_STREAMLIT_APP_URL}" target="_blank">
                ▶ Open in Streamlit
            </a>
            <a class="gh-btn gh-btn-github" href="{_GITHUB_URL}" target="_blank">
                ⭐ View on GitHub
            </a>
            <a class="gh-btn gh-btn-sponsor" href="{_SPONSOR_URL}" target="_blank">
                ♥ Sponsor on GitHub
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Inputs ─────────────────────────────────────────────────────
    st.markdown("##### Art Style")
    st.caption("3D-print styles appear first; general styles follow.")
    style = st.selectbox("Art style", _STYLE_OPTIONS, label_visibility="collapsed")

    subject_choice = st.selectbox(
        "Pick a subject (or choose 'Custom' to type your own)",
        ["Custom"] + _SUBJECT_OPTIONS,
    )
    if subject_choice == "Custom":
        concept = st.text_input(
            "Describe your concept",
            placeholder="e.g. ancient temple overgrown with bioluminescent plants",
        )
    else:
        concept = subject_choice

    if compare_mode:
        style2 = st.selectbox("Second style (comparison)", _STYLE_OPTIONS, index=1, key="style2")
    else:
        style2 = _STYLE_OPTIONS[1]

    if st.button("Generate Concept Art"):
        if not concept.strip():
            st.warning("Please enter or select a concept first.")
            st.stop()

        concept_clean = concept.strip()

        if compare_mode:
            col1, col2 = st.columns(2)
            for i, (col, s) in enumerate(zip([col1, col2], [style, style2])):
                with col:
                    try:
                        with st.spinner(f"Rendering {s}…"):
                            img, used_prompt = generate_image(
                                concept_clean, s, width=width, height=height, seed=seed
                            )
                        st.markdown(
                            f'<div class="section-label">{s.capitalize()}</div>',
                            unsafe_allow_html=True,
                        )
                        st.image(img, caption=f"{s} — {concept_clean.capitalize()}", use_container_width=True)
                        st.download_button(
                            label="⬇ Download PNG",
                            data=img,
                            file_name=f"{s.replace(' ', '_')}_{concept_clean[:30].replace(' ', '_')}.png",
                            mime="image/png",
                            key=f"dl_{i}_{s}",
                        )
                        with st.expander("Prompt used"):
                            st.code(used_prompt, language=None)
                    except Exception as exc:
                        st.error(f"Something went wrong: {exc}")
        else:
            try:
                with st.spinner("Rendering your concept art…"):
                    image_bytes, used_prompt = generate_image(
                        concept_clean, style, width=width, height=height, seed=seed
                    )

                st.markdown('<div class="section-label">Generated Art</div>', unsafe_allow_html=True)
                st.image(
                    image_bytes,
                    caption=f"{style.capitalize()} — {concept_clean.capitalize()}",
                    use_container_width=True,
                )
                st.download_button(
                    label="⬇ Download PNG",
                    data=image_bytes,
                    file_name=f"{style.replace(' ', '_')}_{concept_clean[:30].replace(' ', '_')}.png",
                    mime="image/png",
                )
                with st.expander("Prompt used"):
                    st.code(used_prompt, language=None)

            except Exception as exc:
                st.error(f"Something went wrong: {exc}")


if __name__ == "__main__":
    main()
