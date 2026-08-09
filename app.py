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

# ── Sketch detail options ──────────────────────────────────────────────────────
_LINE_WEIGHT_OPTIONS = ["fine", "medium", "bold"]
_BACKGROUND_OPTIONS = ["white", "kraft paper", "grid paper", "dark canvas"]
_SHADING_OPTIONS = ["none", "hatching", "cel shading"]

# Mapping to natural-language prompt fragments
_LINE_WEIGHT_PROMPTS = {
    "fine": "fine hairline ink strokes",
    "medium": "medium-weight ink lines",
    "bold": "bold thick ink lines",
}
_BACKGROUND_PROMPTS = {
    "white": "clean white background",
    "kraft paper": "warm kraft paper texture background",
    "grid paper": "graph-paper grid background",
    "dark canvas": "dark charcoal canvas background",
}
_SHADING_PROMPTS = {
    "none": "no shading, outline only",
    "hatching": "cross-hatched pencil shading",
    "cel shading": "flat cel shading with hard shadows",
}

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

# 3D sketch styles with dedicated prompt templates
_STYLE_OPTIONS_3D_SKETCH = [
    "wireframe sketch",
    "pencil concept",
    "clay model sketch",
    "ink-line turnaround",
    "cross-section sketch",
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

_STYLE_OPTIONS = _STYLE_OPTIONS_3D_SKETCH + _STYLE_OPTIONS_3D_PRINT + _STYLE_OPTIONS_GENERAL

# Subject presets — sketch-specific first, then general 3D
_SUBJECT_OPTIONS_SKETCH = [
    "character turnaround sheet",
    "orthographic front / side / back views",
    "detail close-up",
    "assembly exploded view",
]

_SUBJECT_OPTIONS_GENERAL = [
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

_SUBJECT_OPTIONS = _SUBJECT_OPTIONS_SKETCH + _SUBJECT_OPTIONS_GENERAL

# Aspect ratio presets (label → (width, height))
_ASPECT_PRESETS = {
    "1:1 Square — single piece (1024×1024)": (1024, 1024),
    "3:4 Portrait — tall figurine (768×1024)": (768, 1024),
    "4:3 Landscape — terrain tile (1024×768)": (1024, 768),
    "16:9 Wide — panoramic scene (1024×576)": (1024, 576),
}

# ── Prompt templates per 3D-sketch style ──────────────────────────────────────

_SKETCH_STYLE_PROMPTS = {
    "wireframe sketch": (
        "wireframe 3D sketch concept art, {concept}. "
        "Technical wireframe line drawing, polygon cage visible, "
        "construction lines and edge loops highlighted, "
        "{line_weight}, {background}, {shading}, "
        "clean professional illustration, CAD-style aesthetics."
    ),
    "pencil concept": (
        "pencil concept sketch, 3D form study, {concept}. "
        "Hand-drawn pencil strokes conveying volume and depth, "
        "gesture lines indicating 3D geometry, "
        "{line_weight}, {background}, {shading}, "
        "concept art sketchbook style."
    ),
    "clay model sketch": (
        "clay model maquette sketch, {concept}. "
        "Sculpting concept illustration, clay-like matte surfaces, "
        "visible thumb-push texture marks, neutral warm grey material, "
        "{line_weight}, {background}, {shading}, "
        "soft ambient occlusion, artist turntable reference style."
    ),
    "ink-line turnaround": (
        "ink-line character / object turnaround sheet, {concept}. "
        "Multiple rotation views (front, 3/4, side) on a single sheet, "
        "clean inking with consistent proportions, registration marks, "
        "{line_weight}, {background}, {shading}, "
        "professional concept art model sheet."
    ),
    "cross-section sketch": (
        "cross-section engineering sketch, {concept}. "
        "Cutaway view revealing internal structure, "
        "annotated detail callouts, orthographic projection, "
        "{line_weight}, {background}, {shading}, "
        "technical illustration style."
    ),
}

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


# ── Utilities ──────────────────────────────────────────────────────────────────

def _safe_filename(*parts: str) -> str:
    """Build a clean PNG filename from style, sketch details, and concept."""
    joined = "_".join(p.replace(" ", "_").replace("/", "-") for p in parts if p)
    return joined[:80] + ".png"


# ── Image generation ───────────────────────────────────────────────────────────

def build_prompt(
    concept: str,
    style: str,
    line_weight: str = "medium",
    background: str = "white",
    shading: str = "none",
) -> str:
    """Construct the full image-generation prompt for the given style."""
    lw = _LINE_WEIGHT_PROMPTS.get(line_weight, line_weight)
    bg = _BACKGROUND_PROMPTS.get(background, background)
    sh = _SHADING_PROMPTS.get(shading, shading)

    if style in _SKETCH_STYLE_PROMPTS:
        return _SKETCH_STYLE_PROMPTS[style].format(
            concept=concept, line_weight=lw, background=bg, shading=sh
        )
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
    line_weight: str = "medium",
    background: str = "white",
    shading: str = "none",
) -> tuple[bytes, str]:
    """Fetch a 3D concept art image from Pollinations.AI.

    Returns a tuple of (image_bytes, prompt_used).
    """
    prompt = build_prompt(concept, style, line_weight=line_weight, background=background, shading=shading)
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
            <p>Design, sketch, and visualize 3D printable concepts — instantly.</p>
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
    turnaround_mode = st.sidebar.checkbox("Multi-view turnaround (2×2 grid)", value=False)

    # ── Sketch Details ─────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.subheader("Sketch Details")
    st.sidebar.caption("Applied to 3D Sketch styles.")
    line_weight = st.sidebar.selectbox("Line weight", _LINE_WEIGHT_OPTIONS, index=1)
    background = st.sidebar.selectbox("Background", _BACKGROUND_OPTIONS, index=0)
    shading = st.sidebar.selectbox("Shading style", _SHADING_OPTIONS, index=0)

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
    st.caption("3D Sketch styles appear first, then 3D-print styles, then general styles.")
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

    if compare_mode and not turnaround_mode:
        style2 = st.selectbox("Second style (comparison)", _STYLE_OPTIONS, index=1, key="style2")
    else:
        style2 = _STYLE_OPTIONS[1]

    # ── Shared kwargs for generate_image ───────────────────────────
    gen_kwargs = dict(
        width=width,
        height=height,
        seed=seed,
        line_weight=line_weight,
        background=background,
        shading=shading,
    )

    if st.button("Generate Concept Art"):
        if not concept.strip():
            st.warning("Please enter or select a concept first.")
            st.stop()

        concept_clean = concept.strip()

        # ── Multi-view turnaround mode ─────────────────────────────
        if turnaround_mode:
            views = ["front view", "side view", "back view", "top view"]
            st.markdown('<div class="section-label">Multi-View Turnaround</div>', unsafe_allow_html=True)
            row1_cols = st.columns(2)
            row2_cols = st.columns(2)
            cols_grid = [row1_cols[0], row1_cols[1], row2_cols[0], row2_cols[1]]
            for i, (view, col) in enumerate(zip(views, cols_grid)):
                with col:
                    view_concept = f"{concept_clean}, {view}"
                    try:
                        with st.spinner(f"Rendering {view}…"):
                            img, used_prompt = generate_image(view_concept, style, **gen_kwargs)
                        st.markdown(
                            f'<div class="section-label">{view.title()}</div>',
                            unsafe_allow_html=True,
                        )
                        st.image(img, caption=f"{style} — {view}", use_container_width=True)
                        fname = _safe_filename(style, line_weight, background, shading, concept_clean[:20], view)
                        st.download_button(
                            label="⬇ Download PNG",
                            data=img,
                            file_name=fname,
                            mime="image/png",
                            key=f"dl_tv_{i}",
                        )
                        with st.expander(f"Prompt — {view}"):
                            st.code(used_prompt, language=None)
                    except Exception as exc:
                        st.error(f"Error on {view}: {exc}")

        # ── Side-by-side comparison mode ───────────────────────────
        elif compare_mode:
            col1, col2 = st.columns(2)
            for i, (col, s) in enumerate(zip([col1, col2], [style, style2])):
                with col:
                    try:
                        with st.spinner(f"Rendering {s}…"):
                            img, used_prompt = generate_image(concept_clean, s, **gen_kwargs)
                        st.markdown(
                            f'<div class="section-label">{s.capitalize()}</div>',
                            unsafe_allow_html=True,
                        )
                        st.image(img, caption=f"{s} — {concept_clean.capitalize()}", use_container_width=True)
                        fname = _safe_filename(s, line_weight, background, shading, concept_clean[:20])
                        st.download_button(
                            label="⬇ Download PNG",
                            data=img,
                            file_name=fname,
                            mime="image/png",
                            key=f"dl_{i}_{s}",
                        )
                        with st.expander("Prompt used"):
                            st.code(used_prompt, language=None)
                    except Exception as exc:
                        st.error(f"Something went wrong: {exc}")

        # ── Single image mode ──────────────────────────────────────
        else:
            try:
                with st.spinner("Rendering your concept art…"):
                    image_bytes, used_prompt = generate_image(concept_clean, style, **gen_kwargs)

                st.markdown('<div class="section-label">Generated Art</div>', unsafe_allow_html=True)
                st.image(
                    image_bytes,
                    caption=f"{style.capitalize()} — {concept_clean.capitalize()}",
                    use_container_width=True,
                )
                fname = _safe_filename(style, line_weight, background, shading, concept_clean[:20])
                st.download_button(
                    label="⬇ Download PNG",
                    data=image_bytes,
                    file_name=fname,
                    mime="image/png",
                )
                with st.expander("Prompt used"):
                    st.code(used_prompt, language=None)

            except Exception as exc:
                st.error(f"Something went wrong: {exc}")


if __name__ == "__main__":
    main()
