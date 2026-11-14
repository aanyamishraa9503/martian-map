
from pathlib import Path
import rasterio
import heapq
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image


# --------------------------------------------------
# DATA LOADING FUNCTIONS
# --------------------------------------------------

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


@st.cache_data
def load_aligned_raster(file_path):
    with rasterio.open(file_path) as src:
        height = src.height
        width = src.width
        bounds = src.bounds

        # Reduce resolution for faster interactive plotting.
        out_height = (height + 5) // 6
        out_width = (width + 5) // 6

        data = src.read(
            1,
            out_shape=(out_height, out_width),
            resampling=rasterio.enums.Resampling.average,
            masked=True,
        ).astype(np.float32)

        data = np.asarray(
            np.ma.filled(data, np.nan),
            dtype=np.float32,
        )

    # Remove invalid elevation values, if present.
    data[data < -10000] = np.nan

    # Calculate local distances from the southwest edge, in km.
    pixel_width = (bounds.right - bounds.left) / out_width
    pixel_height = (bounds.top - bounds.bottom) / out_height

    x = (
        np.arange(out_width) * pixel_width + pixel_width / 2
    ) / 1000

    y = (
        np.arange(out_height) * pixel_height + pixel_height / 2
    ) / 1000

    # Align the array orientation with the map's upward y-axis.
    data = np.flipud(data)

    return x, y, data


@st.cache_data
def load_native_slope(file_path):
    with rasterio.open(file_path) as src:

        # Read the original DEM without downsampling.
        elevation = src.read(
            1,
            masked=True
        ).astype(np.float32)

        elevation = np.asarray(
            np.ma.filled(elevation, np.nan),
            dtype=np.float32
        )

        elevation[elevation < -10000] = np.nan

        # Get the original pixel dimensions in metres.
        dx_m = abs(src.transform.a)
        dy_m = abs(src.transform.e)

        height, width = elevation.shape

        # Generate local map coordinates.
        x = (
            np.arange(width) + 0.5
        ) * dx_m / 1000

        y = (
            np.arange(height) + 0.5
        ) * dy_m / 1000

        # Match the upward-facing map orientation.
        elevation = np.flipud(elevation)

        # Calculate terrain gradients.
        dz_dy, dz_dx = np.gradient(
            elevation,
            dy_m,
            dx_m
        )

        # Convert gradients into slope angles.
        slope_native = np.degrees(
            np.arctan(np.hypot(dz_dx, dz_dy))
        )

        slope_native[~np.isfinite(elevation)] = np.nan

    return x, y, slope_native, dx_m, dy_m


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="MARSCOPE | Jezero Crater",
    page_icon="🔴",
    layout="wide",
)


# --------------------------------------------------
# MARSCOPE VISUAL DESIGN
# --------------------------------------------------

st.markdown("""
<style>

    /* Main application layout */

    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* Main typography */

    h1, h2, h3 {
        letter-spacing: -0.4px;
    }

    h2 {
        font-size: 1.55rem !important;
        font-weight: 650 !important;
        margin-top: 1.8rem !important;
        margin-bottom: 0.8rem !important;
    }

    h3 {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        margin-top: 1.4rem !important;
    }

    /* Mission header */

    .marscope-hero {
        background: linear-gradient(
            120deg,
            #151D2B 0%,
            #202E40 55%,
            #344354 100%
        );
        border: 1px solid #394B60;
        border-radius: 16px;
        padding: 34px 38px;
        margin-bottom: 22px;
    }

    .marscope-kicker {
        color: #E58A59;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 3px;
        margin-bottom: 12px;
    }

    .marscope-title {
        color: #F4F6FA !important;
        font-size: 43px;
        font-weight: 750;
        letter-spacing: 2px;
        line-height: 1.15;
        margin: 0;
    }

    .marscope-subtitle {
        color: #C4CEDB;
        font-size: 17px;
        margin-top: 9px;
    }

    .marscope-description {
        color: #AAB8C9;
        font-size: 14px;
        line-height: 1.8;
        max-width: 780px;
        margin-top: 20px;
    }

    .marscope-status {
        display: inline-block;
        color: #9AD9B8;
        background: #18382F;
        border: 1px solid #28634D;
        border-radius: 20px;
        padding: 6px 12px;
        font-size: 10px;
        font-weight: 650;
        letter-spacing: 1px;
        margin-top: 18px;
    }

    /* Section labels */

    .section-label {
        color: #E58A59;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 5px;
    }

    /* Metric cards */

    [data-testid="stMetric"] {
        background: rgba(128, 128, 128, 0.07);
        border: 1px solid rgba(128, 128, 128, 0.20);
        border-radius: 12px;
        padding: 17px 18px;
        min-height: 112px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.82rem;
        font-weight: 550;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
    }

    /* Expanders */

    [data-testid="stExpander"] {
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 10px;
    }

    /* Dataframes */

    [data-testid="stDataFrame"] {
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 10px;
        overflow: hidden;
    }

    /* Buttons and controls */

    .stButton > button {
        border-radius: 8px;
    }

    /* Dividers */

    hr {
        border-color: rgba(128, 128, 128, 0.20);
    }

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# MARSCOPE HERO HEADER
# --------------------------------------------------

st.html("""
<div class="marscope-hero">

    <div class="marscope-kicker">
        PLANETARY EXPLORATION SYSTEMS
    </div>

    <h1 class="marscope-title">
        MARSCOPE
    </h1>

    <div class="marscope-subtitle">
        Interplanetary Survival Guide · Jezero Crater
    </div>

    <div class="marscope-description">
        An integrated planetary exploration and visualization
        platform for examining Martian surface characteristics,
        terrain conditions, atmospheric context, and experimental
        terrain-aware exploration routes.
    </div>

    <div class="marscope-status">
        RESEARCH & VISUALIZATION PROTOTYPE
    </div>

</div>
""")


st.info(
    "MARSCOPE is an experimental planetary exploration and "
    "visualization platform. Its terrain screening and route "
    "recommendations are not certified for real rover navigation."
)


with st.expander("DATA SOURCES & METHODOLOGY", expanded=False):

    st.markdown("""
    **1. Surface and Terrain**
    - USGS CTX browse imagery
    - USGS Jezero CTX Digital Elevation Model
    - Derived slope analysis

    **2. Thermal Environment**
    - USGS THEMIS Day IR Controlled Mosaic
    - USGS THEMIS Night IR Controlled Mosaic
    - Qualitative infrared signal visualization

    **3. Atmospheric Environment**
    - Montabone et al. MY36 Dust Scenario, Version 2.5
    - Mars Climate Sounder observations
    - Reconstructed column dust optical depth

    **4. Exploration and Route Planning**
    - Documented Perseverance mission landmarks
    - DEM-derived terrain screening
    - Experimental A* route comparison
    """)

    st.caption(
        "Data products have different spatial resolutions, "
        "temporal coverage, and scientific limitations. "
        "Derived visualizations should not be interpreted "
        "as direct operational measurements."
    )


# --------------------------------------------------
# 1. UNIFIED JEZERO CRATER MAP
# --------------------------------------------------

st.html('<div class="section-label">01 / SURFACE EXPLORATION</div>')

st.subheader("Jezero Crater — Unified Exploration Map")

st.caption(
    "Explore the surface, elevation, derived slope and infrared "
    "imagery using the same local map reference."
)

try:
    # Load all aligned raster layers.
    map_x, map_y, ctx_surface = load_aligned_raster(
        "data/processed/jezero_ctx_aligned.tif"
    )

    _, _, elevation_layer = load_aligned_raster(
        "data/raw/jezero_elevation.tif"
    )

    _, _, day_ir_layer = load_aligned_raster(
        "data/processed/jezero_themis_day_aligned.tif"
    )

    _, _, night_ir_layer = load_aligned_raster(
        "data/processed/jezero_themis_night_aligned.tif"
    )

    # Derive slope from the elevation layer.
    dx_m = (map_x[1] - map_x[0]) * 1000
    dy_m = (map_y[1] - map_y[0]) * 1000

    dz_dy, dz_dx = np.gradient(
        elevation_layer,
        dy_m,
        dx_m,
    )

    slope_layer = np.degrees(
        np.arctan(np.hypot(dz_dx, dz_dy))
    )

    slope_layer[~np.isfinite(elevation_layer)] = np.nan

    # Keep the existing downstream terrain and route sections working.
    x = map_x
    y = map_y
    elevation = elevation_layer
    slope = slope_layer

    # Let the user choose which layer to display.
    selected_layer = st.selectbox(
        "Select map layer",
        [
            "CTX Surface",
            "Elevation",
            "Slope",
            "THEMIS Day IR",
            "THEMIS Night IR",
        ],
    )

    show_slope_overlay = False

    if selected_layer == "CTX Surface":
        show_slope_overlay = st.checkbox(
            "Overlay slope screening on CTX surface",
            value=False,
        )

    # Configure the selected layer.
    if selected_layer == "CTX Surface":
        active_data = ctx_surface
        colorscale = "Greys"
        colorbar_title = "Image value"
        hover_label = "Image value"
        hover_format = ".0f"

    elif selected_layer == "Elevation":
        active_data = elevation_layer
        colorscale = "Viridis"
        colorbar_title = "Elevation (m)"
        hover_label = "Elevation"
        hover_format = ".1f"

    elif selected_layer == "Slope":
        active_data = slope_layer
        colorscale = "YlOrRd"
        colorbar_title = "Slope (degrees)"
        hover_label = "Slope"
        hover_format = ".1f"

    elif selected_layer == "THEMIS Day IR":
        active_data = day_ir_layer
        colorscale = "Inferno"
        colorbar_title = "8-bit image value"
        hover_label = "Day IR image value"
        hover_format = ".0f"

    else:
        active_data = night_ir_layer
        colorscale = "Inferno"
        colorbar_title = "8-bit image value"
        hover_label = "Night IR image value"
        hover_format = ".0f"

    # Display the selected raster.
    fig_map = go.Figure(
        data=go.Heatmap(
            x=map_x,
            y=map_y,
            z=active_data,
            colorscale=colorscale,
            colorbar={"title": colorbar_title},
            hovertemplate=(
                "East: %{x:.2f} km<br>"
                "North: %{y:.2f} km<br>"
                + hover_label + ": %{z:" + hover_format + "}"
                "<extra></extra>"
            ),
            connectgaps=False,
        )
    )

    if show_slope_overlay:
        fig_map.add_trace(
            go.Heatmap(
                x=map_x,
                y=map_y,
                z=slope_layer,
                colorscale="YlOrRd",
                zmin=0,
                zmax=45,
                opacity=0.35,
                showscale=False,
                hovertemplate=(
                    "East: %{x:.2f} km<br>"
                    "North: %{y:.2f} km<br>"
                    "Slope: %{z:.1f}°"
                    "<extra></extra>"
                ),
                connectgaps=False,
            )
        )

    fig_map.update_layout(
        height=650,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Distance from western edge (km)",
        yaxis_title="Distance from southern edge (km)",
        yaxis=dict(
            scaleanchor="x",
            scaleratio=1,
        ),
    )

    # Scientific Points of Interest
    fig_map.add_trace(go.Scatter(
        x=[25.495, 23.094],
        y=[51.218, 51.704],
        mode="markers+text",
        text=["Octavia E. Butler", "Three Forks"],
        textposition="top center",
        marker=dict(
            size=11,
            color=["red", "cyan"],
            symbol="star"
        ),
        customdata=[
            [
                "Perseverance landing site",
                "18 Feb 2021",
                "Approximate landing-site coordinates",
                "NASA / Science Advances"
            ],
            [
                "Perseverance sample depot",
                "10 sample tubes deposited",
                "Approximate depot-centre coordinates",
                "NASA Three Forks depot documentation"
            ]
        ],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Feature: %{customdata[0]}<br>"
            "Mission information: %{customdata[1]}<br>"
            "Coordinate status: %{customdata[2]}<br>"
            "Local X: %{x:.3f} km<br>"
            "Local Y: %{y:.3f} km<br>"
            "Source: %{customdata[3]}<br>"
            "<extra></extra>"
        ),
        name="Scientific Points of Interest"
    ))

    st.plotly_chart(
        fig_map,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displaylogo": False,
        },
    )

    st.markdown("### Perseverance Mission Context")

    st.write(
        "Explore the rover's actual traverse and mission locations "
        "using external scientific mapping resources."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "[NASA — Perseverance Rover Location Map]"
            "(https://science.nasa.gov/mission/mars-2020-perseverance/location-map/)"
        )

    with col2:
        st.markdown(
            "[FU Berlin — Interactive Jezero Crater Map]"
            "(https://maps.planet.fu-berlin.de/jezero/)"
        )

        st.caption(
            "These external maps provide broader mission context. "
            "Their geographic coverage and coordinate systems may differ "
            "from the local DEM displayed above."
        )

    # Explain the selected data layer.
    if selected_layer == "CTX Surface":
        st.caption(
            "Source: USGS CTX orthomosaic. Original imagery "
            "is approximately 5 m/pixel, resampled to the "
            "20 m DEM grid and downsampled for display."
        )

    elif selected_layer == "Elevation":
        st.caption(
            "Source: USGS Jezero CTX DEM, 20 m/pixel. "
            "Elevation is displayed in metres."
        )

    elif selected_layer == "Slope":
        st.caption(
            "Derived from the USGS elevation model. "
            "Slope is calculated from the displayed elevation "
            "grid; it is a terrain-screening indicator, not "
            "a rover safety assessment."
        )

    else:
        st.caption(
            "Source: USGS THEMIS controlled IR mosaic. "
            "The original data resolution is 100 m/pixel. "
            "Displayed values are qualitative 8-bit image "
            "values, not calibrated temperatures."
        )

except Exception as error:
    st.error(f"Could not load the unified map: {error}")


# --------------------------------------------------
# 2. REGIONAL ATMOSPHERIC DUST EXPLORER
# --------------------------------------------------

st.html('<div class="section-label">02 / ATMOSPHERIC CONTEXT</div>')

st.subheader("Regional Atmospheric Dust Explorer")

try:
    dust_data = np.load("data/raw/jezero_regional_dust.npz")

    dust_lon = dust_data["longitude"]
    dust_lat = dust_data["latitude"]
    regional_dust = dust_data["dust"]

    st.markdown(
        "Explore the reconstructed atmospheric dust optical-depth "
        "pattern around Jezero Crater."
    )

    fig_dust = go.Figure()

    fig_dust.add_trace(go.Heatmap(
        x=dust_lon,
        y=dust_lat,
        z=regional_dust,
        colorscale="YlOrRd",
        colorbar={"title": "Dust optical depth"},
        hovertemplate=(
            "Longitude: %{x:.1f}°E<br>"
            "Latitude: %{y:.1f}°N<br>"
            "Mean dust optical depth: %{z:.3f}"
            "<extra></extra>"
        )
    ))

    # Mark the approximate location of Jezero Crater.
    fig_dust.add_trace(go.Scatter(
        x=[77.7],
        y=[18.4],
        mode="markers+text",
        name="Jezero Crater",
        marker={
            "size": 12,
            "color": "cyan",
            "line": {"color": "black", "width": 1}
        },
        text=["Jezero"],
        textposition="top right"
    ))

    fig_dust.update_layout(
        xaxis_title="Longitude (°E)",
        yaxis_title="Latitude (°N)",
        height=550,
        margin={"l": 20, "r": 20, "t": 30, "b": 20}
    )

    st.plotly_chart(
        fig_dust,
        width="stretch"
    )

    st.caption(
        "Source: Montabone et al., MY36 Dust Scenario, Version 2.5 "
        "(2023), based on Mars Climate Sounder observations and "
        "kriging interpolation. Values represent the mean of the "
        "available MY36 reconstructed entries for cdod610, "
        "normalized to 610 Pa. Grid spacing: 3°. "
        "This is historical regional atmospheric context, "
        "not real-time weather or a surface dust map."
    )

except Exception as e:
    st.error(f"Could not load the atmospheric dust explorer: {e}")


# --------------------------------------------------
# 3. SCIENCE POINTS OF INTEREST
# --------------------------------------------------

st.html('<div class="section-label">03 / MISSION LANDMARKS</div>')

st.subheader("Jezero Crater — Science Points of Interest")

science_pois = pd.DataFrame([
    {
        "Location": "Octavia E. Butler",
        "Feature": "Perseverance landing site",
        "Scientific significance": "Landing location of Perseverance on 18 February 2021",
        "Status": "Landing site"
    },
    {
        "Location": "Three Forks",
        "Feature": "Sample depot",
        "Scientific significance": "Sample depot where Perseverance deposited 10 filled sample tubes",
        "Status": "Depot established"
    },
    {
        "Location": "Kodiak",
        "Feature": "Sedimentary hill",
        "Scientific significance": "Flat-topped hill imaged during early rover exploration, revealing ancient layered rocks",
        "Status": "Imaged, not visited"
    },
    {
        "Location": "Pinestand",
        "Feature": "Layered sedimentary hill",
        "Scientific significance": "Layered formation that may preserve evidence of ancient river deposition",
        "Status": "Imaged, not visited"
    },
    {
        "Location": "Bright Angel",
        "Feature": "Layered geological formation",
        "Scientific significance": "Light-toned, layered rock formation investigated by Perseverance in Neretva Vallis",
        "Status": "Visited"
    },
    {
        "Location": "Tuff Cliff",
        "Feature": "Rocky outcrop",
        "Scientific significance": "Outcrop associated with the Bright Angel geological formation, investigated by Perseverance",
        "Status": "Visited"
    }
])

st.dataframe(
    science_pois,
    width="stretch",
    hide_index=True
)

st.caption(
    "Science locations are documented Perseverance mission landmarks. "
    "Descriptions are simplified for regional exploration context. "
    "This catalogue is not a rover navigation database."
)

st.markdown(
    """
    **Sources:**

    - [NASA — Perseverance's landing and exploration of Jezero](https://www.jpl.nasa.gov/news/nasas-perseverance-rover-touches-down-on-mars)
    - [NASA — Three Forks Sample Depot Map](https://science.nasa.gov/resource/perseverances-three-forks-sample-depot-map/)
    - [NASA/JPL — Perseverance's Mid-Climb View of Jezero Crater](https://www.jpl.nasa.gov/images/pia26378-perseverances-mid-climb-view-of-jezero-crater/)
    - [NASA — Perseverance Finds Popcorn on Planet Mars (Bright Angel)](https://science.nasa.gov/missions/mars-2020-perseverance/perseverance-finds-popcorn-on-planet-mars/)
    - [Scientific study — Bright Angel formation and Tuff Cliff](https://doi.org/10.1029/2025JE009123)
    """
)


# --------------------------------------------------
# 4. TERRAIN HAZARD SCREENING
# --------------------------------------------------

st.html('<div class="section-label">04 / TERRAIN INTELLIGENCE</div>')

st.subheader("Terrain Hazard Screening")

st.caption(
    "Quantitative slope analysis derived from the Jezero Crater "
    "Digital Elevation Model. Values below describe the analysis "
    "grid and are not official rover safety classifications."
)

native_x, native_y, native_slope, native_dx, native_dy = (
    load_native_slope("data/raw/jezero_elevation.tif")
)


# Native DEM diagnostics are grouped into an expandable section.
with st.expander("NATIVE DEM RESOLUTION & DATA CHECK", expanded=False):

    native_valid_count = np.count_nonzero(
        np.isfinite(native_slope)
    )

    st.markdown("**Original DEM characteristics**")

    native_col1, native_col2, native_col3 = st.columns(3)

    native_col1.metric(
        "DEM rows × columns",
        f"{native_slope.shape[0]:,} × {native_slope.shape[1]:,}"
    )

    native_col2.metric(
        "Horizontal spacing",
        f"{native_dx:.1f} m"
    )

    native_col3.metric(
        "Vertical spacing",
        f"{native_dy:.1f} m"
    )

    st.markdown("**Native-resolution slope statistics**")

    native_col1, native_col2, native_col3 = st.columns(3)

    native_col1.metric(
        "Valid slope cells",
        f"{native_valid_count:,}"
    )

    native_col2.metric(
        "Mean slope",
        f"{np.nanmean(native_slope):.2f}°"
    )

    native_col3.metric(
        "Maximum slope",
        f"{np.nanmax(native_slope):.2f}°"
    )

    st.caption(
        "Native-resolution slope is calculated from the original "
        "approximately 20 m DEM. It is kept separate from the "
        "downsampled terrain analysis displayed below."
    )
    st.markdown("**Extreme Slope Diagnostics**")
    native_valid = np.isfinite(native_slope)
    native_valid_count = np.count_nonzero(native_valid)
    extreme_thresholds = [30, 45, 60]

    extreme_results = []

    for threshold in extreme_thresholds:

        extreme_count = np.count_nonzero(
            native_valid & (native_slope >= threshold)
        )

        extreme_percentage = (
            extreme_count / native_valid_count
        ) * 100

        extreme_results.append({
            "Slope threshold": f"≥ {threshold}°",
            "Native cells": f"{extreme_count:,}",
            "Percentage": f"{extreme_percentage:.4f}%"
        })

    extreme_table = pd.DataFrame(extreme_results)

    st.dataframe(
        extreme_table,
        hide_index=True,
        width="stretch"
    )

    st.caption(
        "This diagnostic identifies the frequency of high-slope "
        "cells. High values require further spatial inspection "
        "before being interpreted as genuine terrain hazards."
    )


try:
    # Convert slope data to a numerical array.
    slope_array = np.asarray(slope, dtype=float)

    # Identify valid terrain pixels.
    valid_mask = np.isfinite(slope_array)
    valid_slope = slope_array[valid_mask]

    if valid_slope.size == 0:
        st.warning("No valid slope data is available.")

    else:
        # Classify terrain using slope angle.
        lower_mask = valid_mask & (slope_array < 10)
        moderate_mask = valid_mask & (
            (slope_array >= 10) & (slope_array < 20)
        )
        steeper_mask = valid_mask & (slope_array >= 20)

        slope_classes = np.full(
            slope_array.shape,
            np.nan,
            dtype=float
        )

        slope_classes[lower_mask] = 1
        slope_classes[moderate_mask] = 2
        slope_classes[steeper_mask] = 3

        # Calculate terrain statistics.
        total_valid = valid_slope.size

        lower_count = np.count_nonzero(lower_mask)
        moderate_count = np.count_nonzero(moderate_mask)
        steeper_count = np.count_nonzero(steeper_mask)

        lower_pct = (lower_count / total_valid) * 100
        moderate_pct = (moderate_count / total_valid) * 100
        steeper_pct = (steeper_count / total_valid) * 100

        # Compare native-resolution and downsampled slope categories.
        native_valid = np.isfinite(native_slope)

        native_lower = native_valid & (native_slope < 10)
        native_moderate = native_valid & (
            (native_slope >= 10) & (native_slope < 20)
        )
        native_steeper = native_valid & (native_slope >= 20)

        native_total = np.count_nonzero(native_valid)

        if native_total > 0:

            native_lower_pct = (
                np.count_nonzero(native_lower) / native_total
            ) * 100

            native_moderate_pct = (
                np.count_nonzero(native_moderate) / native_total
            ) * 100

            native_steeper_pct = (
                np.count_nonzero(native_steeper) / native_total
            ) * 100

            # Calculate native slope percentiles.
            native_valid_slope = native_slope[native_valid]

            native_percentiles = np.percentile(
                native_valid_slope,
                [50, 90, 95, 99]
            )

            # Keep detailed resolution analysis together.
            with st.expander(
                "NATIVE VS DOWNSAMPLED ANALYSIS",
                expanded=False
            ):

                st.markdown("**Native Slope Percentile Analysis**")

                percentile_table = pd.DataFrame({
                    "Percentile": [
                        "50th percentile (Median)",
                        "90th percentile",
                        "95th percentile",
                        "99th percentile"
                    ],
                    "Slope angle": [
                        f"{value:.2f}°"
                        for value in native_percentiles
                    ]
                })

                st.dataframe(
                    percentile_table,
                    hide_index=True,
                    width="stretch"
                )

                st.caption(
                    "Percentiles show the slope angle below which "
                    "the corresponding percentage of valid native "
                    "slope cells falls."
                )

                st.markdown("**Native vs Downsampled Slope Comparison**")

                comparison = pd.DataFrame({
                    "Slope category": [
                        "Lower (<10°)",
                        "Moderate (10°–<20°)",
                        "Steeper (≥20°)"
                    ],
                    "Downsampled (%)": [
                        lower_pct,
                        moderate_pct,
                        steeper_pct
                    ],
                    "Native resolution (%)": [
                        native_lower_pct,
                        native_moderate_pct,
                        native_steeper_pct
                    ]
                })

                st.dataframe(
                    comparison,
                    hide_index=True,
                    width="stretch"
                )

                st.caption(
                    "The two percentages are calculated from their "
                    "respective valid-cell masks. Differences in valid "
                    "coverage may affect direct comparison."
                )

        else:
            st.warning(
                "No valid native-resolution slope data is available."
            )

        mean_slope = np.mean(valid_slope)
        max_slope = np.max(valid_slope)

        # --------------------------------------------------
        # TERRAIN OVERVIEW METRIC CARDS
        # --------------------------------------------------

        st.markdown("### Terrain Overview")

        st.caption(
            "Statistics calculated from the downsampled DEM slope grid. "
            "Each valid cell represents approximately 120 m of "
            "horizontal spacing."
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Valid terrain cells",
            f"{total_valid:,}",
            help="Number of grid cells with valid calculated slope values."
        )

        col2.metric(
            "Mean slope",
            f"{mean_slope:.2f}°",
            help="Average slope angle across all valid terrain cells."
        )

        col3.metric(
            "Maximum slope",
            f"{max_slope:.2f}°",
            help="Highest calculated slope angle in the downsampled grid."
        )

        col4.metric(
            "Steeper terrain",
            f"{steeper_pct:.2f}%",
            help="Percentage of valid cells with slope angles of 20° or greater."
        )

        st.caption(
            "Valid terrain cells exclude locations with missing or "
            "invalid elevation/slope data. The maximum is a calculated "
            "grid value and should not be interpreted as a verified "
            "physical cliff or rover hazard."
        )

        # --------------------------------------------------
        # SLOPE CLASSIFICATION
        # --------------------------------------------------

        st.markdown("### Slope Classification")

        st.caption(
            "Percentage of valid downsampled terrain cells in each "
            "illustrative slope category."
        )

        stat_col1, stat_col2, stat_col3 = st.columns(3)

        stat_col1.metric(
            "Lower · Below 10°",
            f"{lower_pct:.1f}%"
        )

        stat_col2.metric(
            "Moderate · 10°–20°",
            f"{moderate_pct:.1f}%"
        )

        stat_col3.metric(
            "Steeper · ≥20°",
            f"{steeper_pct:.1f}%"
        )

        # Slope distribution histogram.
        st.markdown("### Slope Angle Distribution")

        st.caption(
            "Histogram showing how frequently different slope angles "
            "occur across the valid downsampled terrain cells."
        )

        fig_distribution = go.Figure()

        fig_distribution.add_trace(go.Histogram(
            x=valid_slope,
            nbinsx=30,
            histnorm="percent",
            marker=dict(
                color="#4682B4",
                line=dict(
                    color="white",
                    width=0.5
                )
            ),
            hovertemplate=(
                "Slope range: %{x}<br>"
                "Percentage of terrain cells: %{y:.2f}%"
                "<extra></extra>"
            )
        ))

        fig_distribution.update_layout(
            xaxis_title="Slope angle (degrees)",
            yaxis_title="Terrain cells (%)",
            height=400,
            bargap=0.05,
            margin={"l": 20, "r": 20, "t": 30, "b": 40}
        )

        st.plotly_chart(
            fig_distribution,
            width="stretch"
        )

        # --------------------------------------------------
        # SPATIAL DISTRIBUTION OF STEEPER TERRAIN
        # --------------------------------------------------

        st.markdown("### Spatial Distribution of Steeper Terrain")

        st.caption(
            "Shows where cells with slope angles of 20° or greater "
            "are concentrated across the Jezero analysis area."
        )

        rows, cols = slope_array.shape

        # Divide the DEM into 80 spatial zones per direction.
        row_groups = np.array_split(
            np.arange(rows),
            min(80, rows)
        )

        col_groups = np.array_split(
            np.arange(cols),
            min(80, cols)
        )

        steep_percentage = np.full(
            (len(row_groups), len(col_groups)),
            np.nan
        )

        valid_counts = np.zeros(
            (len(row_groups), len(col_groups)),
            dtype=int
        )

        zone_x = []
        zone_y = []

        x_values = np.asarray(x)
        y_values = np.asarray(y)

        for i, row_indices in enumerate(row_groups):
            zone_y.append(np.mean(y_values[row_indices]))

            for j, col_indices in enumerate(col_groups):
                zone = slope_array[
                    np.ix_(row_indices, col_indices)
                ]

                valid_zone = zone[np.isfinite(zone)]

                valid_counts[i, j] = valid_zone.size

                if valid_zone.size > 0:
                    steep_percentage[i, j] = (
                        np.count_nonzero(valid_zone >= 20)
                        / valid_zone.size
                    ) * 100

        for col_indices in col_groups:
            zone_x.append(np.mean(x_values[col_indices]))

        fig_spatial = go.Figure(data=go.Heatmap(
            x=zone_x,
            y=zone_y,
            z=steep_percentage,
            customdata=valid_counts,
            colorscale="YlOrRd",
            zmin=0,
            zmax=100,
            colorbar={
                "title": "Steeper terrain (%)"
            },
            hovertemplate=(
                "Local X: %{x:.2f} km<br>"
                "Local Y: %{y:.2f} km<br>"
                "Cells with slope ≥20°: %{z:.1f}%<br>"
                "Valid cells: %{customdata}<extra></extra>"
            )
        ))

        fig_spatial.update_layout(
            xaxis_title="Local distance east (km)",
            yaxis_title="Local distance north (km)",
            height=500,
            margin={"l": 20, "r": 20, "t": 30, "b": 20}
        )

        st.plotly_chart(
            fig_spatial,
            width="stretch",
            config={"scrollZoom": True}
        )

        st.caption(
            "Each zone summarizes the percentage of valid DEM cells "
            "with slope angles of 20° or greater. The map uses "
            "80 × 80 spatial subdivisions where the raster dimensions "
            "permit. It is a terrain concentration indicator, "
            "not a rover traversability or safety assessment."
        )

        # --------------------------------------------------
        # TERRAIN CLASSIFICATION MAP
        # --------------------------------------------------

        st.markdown("### Terrain Classification Map")

        st.caption(
            "Spatial classification of the downsampled slope grid "
            "using the three screening categories."
        )

        fig_hazard = go.Figure(data=go.Heatmap(
            x=x,
            y=y,
            z=slope_classes,
            customdata=slope_array,
            colorscale=[
                [0.00, "#2ca25f"],
                [0.3332, "#2ca25f"],
                [0.3333, "#fdae61"],
                [0.6665, "#fdae61"],
                [0.6666, "#d7191c"],
                [1.00, "#d7191c"]
            ],
            zmin=1,
            zmax=3,
            colorbar={
                "title": "Slope category",
                "tickvals": [1, 2, 3],
                "ticktext": [
                    "Lower",
                    "Moderate",
                    "Steeper"
                ]
            },
            hovertemplate=(
                "Local X: %{x:.2f} km<br>"
                "Local Y: %{y:.2f} km<br>"
                "Slope: %{customdata:.1f}°<extra></extra>"
            )
        ))

        fig_hazard.update_layout(
            xaxis_title="Local distance east (km)",
            yaxis_title="Local distance north (km)",
            height=600,
            margin={"l": 20, "r": 20, "t": 30, "b": 20}
        )

        st.plotly_chart(
            fig_hazard,
            width="stretch",
            config={"scrollZoom": True}
        )

        st.markdown("""
        **Screening categories**

        - 🟢 Lower slope: below 10°
        - 🟠 Moderate slope: 10° to below 20°
        - 🔴 Steeper terrain: 20° and above
        """)

        st.caption(
            "Derived from the USGS Jezero CTX DEM. "
            "Statistics are calculated from valid slope cells only. "
            "Categories are illustrative prototype screening bands, "
            "not official NASA rover safety thresholds. "
            "Slope alone does not establish terrain traversability."
        )

except NameError:
    st.warning(
        "Slope data is unavailable. Check that the DEM and "
        "slope calculation sections execute successfully first."
    )


# --------------------------------------------------
# 5. TERRAIN-AWARE ROUTE PLANNER
# --------------------------------------------------

st.html('<div class="section-label">05 / ROUTE INTELLIGENCE</div>')

st.subheader("Terrain-Aware Route Planner")

st.caption(
    "Compare a shortest-distance route with an experimental "
    "slope-weighted route across the downsampled terrain grid."
)

try:
    # Reduce the grid size to make route calculations faster.
    step = 4

    route_slope = slope[::step, ::step]
    route_x = x[::step]
    route_y = y[::step]

    rows, cols = route_slope.shape

    st.markdown(
        "Select a starting point and destination to compare "
        "a shortest-distance route with a slope-weighted route."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Starting point**")
        start_row = st.slider(
            "Start row",
            0, rows - 1, rows // 2,
            key="route_start_row"
        )
        start_col = st.slider(
            "Start column",
            0, cols - 1, cols // 4,
            key="route_start_col"
        )

    with col2:
        st.markdown("**Destination**")
        end_row = st.slider(
            "Destination row",
            0, rows - 1, rows // 2,
            key="route_end_row"
        )
        end_col = st.slider(
            "Destination column",
            0, cols - 1, 3 * cols // 4,
            key="route_end_col"
        )

    def find_route(start, goal, terrain_aware=False):

        directions = [
            (-1, 0, 1.0),
            (1, 0, 1.0),
            (0, -1, 1.0),
            (0, 1, 1.0),
            (-1, -1, 1.414),
            (-1, 1, 1.414),
            (1, -1, 1.414),
            (1, 1, 1.414)
        ]

        queue = [(0, start)]
        came_from = {}
        cost_so_far = {start: 0}

        while queue:
            _, current = heapq.heappop(queue)

            if current == goal:
                break

            for dr, dc, distance in directions:
                nr = current[0] + dr
                nc = current[1] + dc

                if not (0 <= nr < rows and 0 <= nc < cols):
                    continue

                current_slope = route_slope[current]
                next_slope = route_slope[nr, nc]

                if not np.isfinite(next_slope):
                    continue

                if not np.isfinite(current_slope):
                    continue

                movement_cost = distance

                if terrain_aware:
                    average_slope = (
                        current_slope + next_slope
                    ) / 2

                    movement_cost *= (
                        1 + (average_slope / 15) ** 2
                    )

                new_cost = (
                    cost_so_far[current] + movement_cost
                )

                neighbor = (nr, nc)

                if (
                    neighbor not in cost_so_far
                    or new_cost < cost_so_far[neighbor]
                ):
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current

                    heuristic = np.hypot(
                        nr - goal[0],
                        nc - goal[1]
                    )

                    priority = new_cost + heuristic

                    heapq.heappush(
                        queue,
                        (priority, neighbor)
                    )

        if goal not in came_from and goal != start:
            return None

        path = [goal]
        current = goal

        while current != start:
            current = came_from[current]
            path.append(current)

        path.reverse()
        return path

    start = (start_row, start_col)
    goal = (end_row, end_col)

    if not np.isfinite(route_slope[start]):
        st.warning("The selected starting point has missing terrain data.")

    elif not np.isfinite(route_slope[goal]):
        st.warning("The selected destination has missing terrain data.")

    elif start == goal:
        st.warning("Choose different starting and destination points.")

    else:
        shortest_path = find_route(start, goal, False)
        terrain_path = find_route(start, goal, True)

        if shortest_path is None or terrain_path is None:
            st.warning(
                "A route could not be found between these points."
            )

        else:
            def route_distance(path):
                distance = 0

                for i in range(1, len(path)):
                    r1, c1 = path[i - 1]
                    r2, c2 = path[i]

                    dx = (route_x[c2] - route_x[c1]) * 1000
                    dy = (route_y[r2] - route_y[r1]) * 1000

                    distance += np.hypot(dx, dy)

                return distance / 1000

            shortest_km = route_distance(shortest_path)
            terrain_km = route_distance(terrain_path)

            fig_route = go.Figure()

            fig_route.add_trace(go.Heatmap(
                x=route_x,
                y=route_y,
                z=route_slope,
                colorscale="YlOrRd",
                zmin=0,
                zmax=45,
                opacity=0.65,
                colorbar={"title": "Slope (°)"}
            ))

            for path, name, colour in [
                (shortest_path, "Shortest route", "cyan"),
                (terrain_path, "Terrain-aware route", "blue")
            ]:
                path_rows = [point[0] for point in path]
                path_cols = [point[1] for point in path]

                fig_route.add_trace(go.Scatter(
                    x=route_x[path_cols],
                    y=route_y[path_rows],
                    mode="lines",
                    name=name,
                    line={"color": colour, "width": 3}
                ))

            fig_route.add_trace(go.Scatter(
                x=[route_x[start_col], route_x[end_col]],
                y=[route_y[start_row], route_y[end_row]],
                mode="markers+text",
                name="Endpoints",
                marker={"size": 11, "color": "white"},
                text=["START", "DESTINATION"],
                textposition="top center"
            ))

            fig_route.update_layout(
                xaxis_title="Local distance east (km)",
                yaxis_title="Local distance north (km)",
                height=600,
                margin={"l": 20, "r": 20, "t": 30, "b": 20}
            )

            st.plotly_chart(
                fig_route,
                width="stretch"
            )

            metric1, metric2 = st.columns(2)

            metric1.metric(
                "Shortest route",
                f"{shortest_km:.2f} km"
            )

            metric2.metric(
                "Terrain-aware route",
                f"{terrain_km:.2f} km"
            )

            st.caption(
                "Prototype A* route comparison. The terrain-aware "
                "algorithm applies a slope-based movement penalty. "
                "The grid is downsampled by a factor of four. "
                "Routes are illustrative and are not validated "
                "for actual rover navigation."
            )

except Exception as e:
    st.error(f"Route planner error: {e}")


# --------------------------------------------------
# 6. EXPLORATION TARGETS — DEMONSTRATION DATA
# --------------------------------------------------

st.html('<div class="section-label">06 / EXPLORATION SIMULATION</div>')

st.subheader("Exploration Targets — Demonstration Data")

st.caption(
    "The targets in this section are simulated demonstration "
    "points created to test the exploration interface. "
    "They are not verified geological locations or actual "
    "Perseverance mission targets."
)

st.warning(
    "These three targets are fictional examples. "
    "Their coordinates and science scores have not been verified."
)

targets = pd.DataFrame([
    {
        "Target": "Target A",
        "Latitude": 18.4,
        "Longitude": 77.6,
        "Illustrative Science Score": 8,
    },
    {
        "Target": "Target B",
        "Latitude": 18.6,
        "Longitude": 77.9,
        "Illustrative Science Score": 5,
    },
    {
        "Target": "Target C",
        "Latitude": 18.3,
        "Longitude": 77.7,
        "Illustrative Science Score": 9,
    },
])

st.dataframe(
    targets,
    width="stretch",
    hide_index=True
)

minimum_value = st.slider(
    "Minimum illustrative science score",
    min_value=1,
    max_value=10,
    value=7,
)

filtered_targets = targets[
    targets["Illustrative Science Score"] >= minimum_value
]

st.subheader("Selected Targets")

st.dataframe(
    filtered_targets,
    width="stretch",
    hide_index=True,
)

st.caption(
    "MARSCOPE prototype. The target records are fictional; "
    "the surface-image preview is from USGS."
)
