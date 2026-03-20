import streamlit as st
import re
import requests

# -------------------------------
# CONFIGURATION
# -------------------------------

SVG_SOURCE_URL = "https://api.shn.gob.ar/imagenes-modelo/curvas_altura-total/Alturatotal_Palermo.svg"

DRAFT_BY_TIDE = {    
    -0.1: 9.70,
     0.0: 9.80,
     0.1: 9.90,
     0.2: 10.00,
     0.3: 10.10,
     0.4: 10.20,
     0.5: 10.30,
     0.6: 10.37,
     0.7: 10.41,
     0.8: 10.45,
     0.9: 10.49,
     1.0: 10.53,
     1.1: 10.57,
     1.2: 10.61,
     1.3: 10.65,
     1.4: 10.73,
     1.5: 10.82,
     1.6: 10.91,
     1.7: 11.00,
     1.8: 11.09,
     1.9: 11.18,
     2.0: 11.27,
     2.1: 11.36,
     2.2: 11.45,
     2.3: 11.54,
     2.4: 11.63,
     2.5: 11.72,
     2.6: 11.81
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
