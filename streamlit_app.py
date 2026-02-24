import streamlit as st
import os
import re
import requests
from playwright.sync_api import sync_playwright

# --- CONFIGURATION & DATA (From your original file) ---
SVG_SOURCE_URL = "https://api.shn.gob.ar/imagenes-modelo/curvas_altura-total/Alturatotal_Palermo.svg"
DRAFT_BY_TIDE = {
    -0.1: 7.30, 0.0: 7.40, 0.1: 7.50, 0.2: 7.60, 0.3: 7.70,
    0.4: 7.80, 0.5: 7.90, 0.6: 8.00, 0.7: 8.10, 0.8: 8.20,
    0.9: 8.30, 1.0: 8.40, 1.1: 8.50, 1.2: 8.60, 1.3: 8.70,
    1.4: 8.80, 1.5: 8.90, 1.6: 9.00, 1.7: 9.10, 1.8: 9.20,
    1.9: 9.30, 2.0: 9.40, 2.1: 9.50, 2.2: 9.60
}

TOLERANCE = 0.051

# --- LOGIC FUNCTIONS (Unchanged from your file) ---
def parse_tick(raw):
    raw = raw.strip().replace(",", ".")
    if raw.endswith("m"): raw = raw[:-1]
    try: return float(raw)
    except: return None

def snap_to_key(v):
    best, err = None, 999
    for k in DRAFT_BY_TIDE:
        e = abs(v - k)
        if e < err: best, err = k, e
    return best if err <= TOLERANCE else None

def modify_svg(svg):
    text_re = re.compile(r'(<text[^>]*x=["\']-5["\'][^>]*y=["\']([\d.]+)[^>]*>)(.*?)(</text>)')
    out = svg
    for full, y, raw, _ in text_re.findall(svg):
        tide = parse_tick(raw)
        if tide is None: continue
        key = snap_to_key(tide)
        if key is None: continue
        draft = DRAFT_BY_TIDE[key]
        repl = f'<text x="115" y="{y}" text-anchor="end" font-size="20" fill="blue">Tide {key:.1f} = Draft with Gangway {draft:.2f} m</text>'
        out = out.replace(full + raw + "</text>", repl)
    
    new_title = "BUENOS AIRES Wind Corrected Tides with Drafts"
    out = re.sub(r"Altura del nivel del agua.*?\)", new_title, out, flags=re.DOTALL | re.IGNORECASE)
    return out

# --- STREAMLIT UI ---
st.title("🚢 Buenos Aires Draft Calculator")
st.write("Click below to fetch the latest SHN data and apply sailing drafts.")
import subprocess
subprocess.run(["playwright", "install", "chromium"])
if st.button('Generate Report'):
    with st.spinner('Fetching and converting data...'):
        try:
            # 1. Get SVG
            r = requests.get(SVG_SOURCE_URL, timeout=30)
            r.raise_for_status()
            
            # 2. Modify SVG
            svg_final = modify_svg(r.text)
            
            # 3. Create PNG via Playwright
            html_content = f"<html><body style='margin:0'>{svg_final}</body></html>"
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1400, "height": 1000})
                page.set_content(html_content)
                img_bytes = page.screenshot(full_page=True)
                browser.close()
            
            # 4. Show Result
            st.image(img_bytes, caption="Updated Oyarbide Forecast")
            st.download_button("Download Report (PNG)", img_bytes, "Punta_Indio.png", "image/png")
            
        except Exception as e:
            st.error(f"Error: {e}")