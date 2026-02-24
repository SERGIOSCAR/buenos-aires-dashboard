import streamlit as st
import re
import requests

# -------------------------------
# CONFIGURATION
# -------------------------------

SVG_SOURCE_URL = "https://api.shn.gob.ar/imagenes-modelo/curvas_altura-total/Alturatotal_Palermo.svg"

DRAFT_BY_TIDE = {
    -0.1: 7.30, 0.0: 7.40, 0.1: 7.50, 0.2: 7.60, 0.3: 7.70,
    0.4: 7.80, 0.5: 7.90, 0.6: 8.00, 0.7: 8.10, 0.8: 8.20,
    0.9: 8.30, 1.0: 8.40, 1.1: 8.50, 1.2: 8.60, 1.3: 8.70,
    1.4: 8.80, 1.5: 8.90, 1.6: 9.00, 1.7: 9.10, 1.8: 9.20,
    1.9: 9.30, 2.0: 9.40, 2.1: 9.50, 2.2: 9.60
}

TOLERANCE = 0.051

# -------------------------------
# LOGIC
# -------------------------------

def parse_tick(raw):
    raw = raw.strip().replace(",", ".")
    if raw.endswith("m"):
        raw = raw[:-1]
    try:
        return float(raw)
    except:
        return None


def snap_to_key(v):
    best = None
    err = 999
    for k in DRAFT_BY_TIDE:
        e = abs(v - k)
        if e < err:
            best = k
            err = e
    return best if err <= TOLERANCE else None


def modify_svg(svg):
    text_re = re.compile(
        r'(<text[^>]*x=["\']-5["\'][^>]*y=["\']([\d.]+)[^>]*>)(.*?)(</text>)'
    )

    out = svg

    for full, y, raw, _ in text_re.findall(svg):
        tide = parse_tick(raw)
        if tide is None:
            continue

        key = snap_to_key(tide)
        if key is None:
            continue

        draft = DRAFT_BY_TIDE[key]

        replacement = (
            f'<text x="115" y="{y}" '
            f'text-anchor="end" font-size="20" fill="blue">'
            f'Tide {key:.1f} = Draft with Gangway {draft:.2f} m'
            f'</text>'
        )

        out = out.replace(full + raw + "</text>", replacement)

    new_title = "BUENOS AIRES Wind Corrected Tides with Sailing Drafts"

    out = re.sub(
        r"Altura del nivel del agua.*?\)",
        new_title,
        out,
        flags=re.DOTALL | re.IGNORECASE
    )

    return out


# -------------------------------
# STREAMLIT UI
# -------------------------------

st.set_page_config(page_title="Buenos Aires Draft Calculator", layout="wide")

st.title("🚢 Buenos Aires Draft Calculator")
st.write("Click below to fetch the latest SHN data and apply sailing drafts.")

if st.button("Generate Report"):

    with st.spinner("Fetching latest SHN data..."):

        try:
            response = requests.get(SVG_SOURCE_URL, timeout=30)
            response.raise_for_status()

            svg_modified = modify_svg(response.text)

            # Styled container to control size and keep it professional
            styled_svg = f"""
            <div style="
                display:flex;
                justify-content:center;
                width:100%;
            ">
                <div style="
                    width:1000px;
                    border-radius:12px;
                    box-shadow:0 4px 12px rgba(0,0,0,0.08);
                    overflow:hidden;
                    background:white;
                    padding:10px;
                ">
                    {svg_modified}
                </div>
            </div>
            """

            st.components.v1.html(styled_svg, height=600, scrolling=True)

            st.download_button(
                label="Download Report (SVG)",
                data=svg_modified,
                file_name="Buenos_Aires_Draft_Report.svg",
                mime="image/svg+xml"
            )

        except Exception as e:
            st.error(f"Error generating report: {e}")
