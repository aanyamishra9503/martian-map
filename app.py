
from pathlib import Path
import rasterio

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image

@st.cache_data
def load_elevation():
    file_path = "data/raw/jezero_elevation.tif"

    with rasterio.open(file_path) as src:
        height = src.height
        width = src.width
        bounds = src.bounds

        # Reduce resolution to keep the interactive plot responsive.
        out_height = (height + 5) // 6
        out_width = (width + 5) // 6

        elevation = src.read(
            1,
            out_shape=(out_height, out_width),
            resampling=rasterio.enums.Resampling.average,
            masked=True,
        )

    elevation = np.asarray(
        np.ma.filled(elevation, np.nan),
        dtype=np.float32,
    )

    # Remove invalid or missing elevation values.
    elevation[elevation < -10000] = np.nan

    # Distances from the western and southern dataset edges, in km.
    pixel_width = (bounds.right - bounds.left) / out_width
    pixel_height = (bounds.top - bounds.bottom) / out_height

    x = (
        np.arange(out_width) * pixel_width + pixel_width / 2
    ) / 1000

    y = (
        np.arange(out_height) * pixel_height + pixel_height / 2
    ) / 1000

    # Raster rows start at the north; the chart's y-axis increases upward.
    elevation = np.flipud(elevation)

    return x, y, elevation

st.set_page_config(
    page_title="MARSCOPE",
    page_icon="🔴",
    layout="wide",
)

st.title("🔴 MARSCOPE")
st.subheader("Interplanetary Survival Guide: Martian Map")

st.write(
    "Explore Jezero Crater on Mars, inspect terrain, "
    "and compare potential exploration sites."
)

# --------------------------------------------------
# 1. Load an official USGS Jezero surface-image preview
# --------------------------------------------------

IMAGE_URL = (
    "https://asc-pds-services.s3.us-west-2.amazonaws.com/"
    "mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/"
    "browse_M20_JezeroCrater_CTXortho_mosaic_5m.jpg"
)
# The USGS Astrogeology Science Center provides this image as a preview of the full-resolution raster.
# Found from the index page: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/CTX/index.html; image- https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/browse_M20_JezeroCrater_CTXortho_mosaic_5m.jpg

IMAGE_PATH = Path("data/raw/jezero_ctx_browse.jpg")

# Approximate bounds of the matching broad-area USGS mosaic.
WEST, EAST = 76.99, 78.58
SOUTH, NORTH = 17.58, 19.29


@st.cache_data
def load_jezero_image():
    IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not IMAGE_PATH.exists():
        response = requests.get(IMAGE_URL, timeout=60)
        response.raise_for_status()
        IMAGE_PATH.write_bytes(response.content)

    with Image.open(IMAGE_PATH) as image:
        return np.array(image.convert("RGB"))


st.subheader("Jezero Crater — Surface Imagery")

try:
    image_array = load_jezero_image()

    image_height, image_width = image_array.shape[:2]

    fig = go.Figure(
        go.Image(
            z=image_array,
            x0=WEST,
            dx=(EAST - WEST) / image_width,
            y0=NORTH,
            dy=-(NORTH - SOUTH) / image_height,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=20, b=10),
        dragmode="pan",
        xaxis_title="Longitude (degrees east)",
        yaxis_title="Latitude (degrees north)",
        xaxis=dict(range=[WEST, EAST]),
        yaxis=dict(
            range=[SOUTH, NORTH],
            scaleanchor="x",
            scaleratio=1,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
        },
    )

    st.caption(
        "Source: USGS Astrogeology Science Center, "
        "Mars 2020 CTX orthomosaic browse image. "
        "This is a preview, not the full-resolution raster."
    )

except Exception as error:
    st.error(
        "The Jezero preview could not be loaded. "
        "Check your internet connection and try again."
    )
    st.caption(f"Technical details: {error}")

# --------------------------------------------------
# 2. Demonstration targets — not real science locations
# --------------------------------------------------

st.subheader("Jezero Crater — Elevation Map")
#Source: USGS Mars 2020 Science Investigation CTX DEM Mosaic.
#local file-data/raw/jezero_elevation.tif; It contains One band of numerical elevation values, not a normal photograph
#Direct TIFF download- https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif?utm_source=chatgpt.com


try:
    x, y, elevation = load_elevation()

    fig_elevation = go.Figure(
        data=go.Heatmap(
            x=x,
            y=y,
            z=elevation,
            colorscale="Viridis",
            colorbar={"title": "Elevation (m)"},
            hovertemplate=(
                "East: %{x:.1f} km<br>"
                "North: %{y:.1f} km<br>"
                "Elevation: %{z:.1f} m"
                "<extra></extra>"
            ),
            connectgaps=False,
        )
    )

    fig_elevation.update_layout(
        xaxis_title="Distance from western edge (km)",
        yaxis_title="Distance from southern edge (km)",
        height=600,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
    )

    st.plotly_chart(
        fig_elevation,
        use_container_width=True,
    )

    st.caption(
        "Source: USGS Jezero Crater CTX DEM, 20 m/pixel. "
        "The displayed grid is downsampled for performance. "
        "Coordinates are local projected distances, not latitude "
        "and longitude."
    )

except Exception as e:
    st.error(f"Could not load the elevation map: {e}")


st.subheader("Jezero Crater — Slope Map")

try:
    # Calculate the spacing between elevation pixels, in metres
    dx_m = (x[1] - x[0]) * 1000
    dy_m = (y[1] - y[0]) * 1000

    # Calculate elevation change in the east-west and north-south directions
    dz_dy, dz_dx = np.gradient(elevation, dy_m, dx_m)

    # Convert the terrain gradient into slope angles, in degrees
    slope = np.degrees(
        np.arctan(np.hypot(dz_dx, dz_dy))
    )

    # Keep areas without valid elevation data blank
    slope[~np.isfinite(elevation)] = np.nan

    fig_slope = go.Figure(
        data=go.Heatmap(
            x=x,
            y=y,
            z=slope,
            colorscale="YlOrRd",
            zmin=0,
            zmax=45,
            colorbar={"title": "Slope (degrees)"},
            hovertemplate=(
                "East: %{x:.1f} km<br>"
                "North: %{y:.1f} km<br>"
                "Slope: %{z:.1f}°"
                "<extra></extra>"
            ),
            connectgaps=False,
        )
    )

    fig_slope.update_layout(
        xaxis_title="Distance from western edge (km)",
        yaxis_title="Distance from southern edge (km)",
        height=600,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
    )

    st.plotly_chart(fig_slope, width="stretch")

    st.caption(
        "Slope is calculated from the downsampled elevation grid, "
        "with approximately 120 m spacing. Slopes above 45° share "
        "the top display colour. This is a regional terrain overview, "
        "not a rover-safety assessment."
    )

except Exception as e:
    st.error(f"Could not calculate the slope map: {e}")


st.subheader("Exploration Targets — Demonstration Data")

st.warning(
    "These three targets are fictional examples. "
    "Their coordinates and science scores have not been verified."
)

targets = pd.DataFrame([
    {
        "Target": "Target A",
        "Latitude": 18.4,
        "Longitude": 77.6,
        "Science Value": 8,
    },
    {
        "Target": "Target B",
        "Latitude": 18.6,
        "Longitude": 77.9,
        "Science Value": 5,
    },
    {
        "Target": "Target C",
        "Latitude": 18.3,
        "Longitude": 77.7,
        "Science Value": 9,
    },
])

st.dataframe(targets, use_container_width=True, hide_index=True)

minimum_value = st.slider(
    "Minimum science value",
    min_value=1,
    max_value=10,
    value=7,
)

filtered_targets = targets[
    targets["Science Value"] >= minimum_value
]

st.subheader("Selected Targets")
st.dataframe(
    filtered_targets,
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "MARSCOPE prototype. The target records are fictional; "
    "the surface-image preview is from USGS."
)
