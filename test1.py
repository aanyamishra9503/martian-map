#streamlit folium trial version


import folium
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(page_title="Mars Tile Test", layout="wide")
st.title("MARSCOPE — Mars Tile Alignment Test")

# Initial view is centered approximately on the Jezero HiRISE mosaic.
mars_map = folium.Map(
    location=[18.49, 77.40],
    zoom_start=10,
    crs="EPSG4326",
    tiles=None,
)

# Global MOLA/HRSC hillshade: use the supplied WMTS template.
mola_url = (
    "https://trek.nasa.gov/tiles/Mars/EQ/"
    "Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw/"
    "1.0.0//default/default028mm/{z}/{y}/{x}.jpg"
)

folium.TileLayer(
    tiles=mola_url,
    name="MOLA / HRSC hillshade",
    attr="NASA Mars Trek — MOLA / HRSC",
    overlay=True,
    control=True,
    opacity=1.0,
    max_zoom=17,
    max_native_zoom=8,
).add_to(mars_map)

# Controlled Jezero HiRISE mosaic.
hirise_url = (
    "https://trek.nasa.gov/tiles/Mars/EQ/"
    "JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/"
    "1.0.0//default/default028mm/{z}/{y}/{x}.png"
)

folium.TileLayer(
    tiles=hirise_url,
    name="HiRISE — Jezero mosaic",
    attr="NASA Mars Trek — MRO HiRISE",
    overlay=True,
    control=True,
    opacity=1.0,
    max_zoom=17,
    max_native_zoom=17,
).add_to(mars_map)

folium.LayerControl(collapsed=False).add_to(mars_map)

st.caption(
    "Experimental Mars geographic tile-grid test. "
    "Layer alignment and zoom behavior have not yet been validated."
)

st_folium(mars_map, width=None, height=650, key="mars_tile_test")
