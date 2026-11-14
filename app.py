
from pathlib import Path
import rasterio
import heapq
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

st.markdown("""
### Mars Exploration & Surface Observation Platform

An interactive prototype for exploring the terrain,
thermal characteristics, atmospheric context, and
potential exploration routes of Jezero Crater.
""")

st.info(
    "MARSCOPE is a research and visualization prototype. "
    "Its maps and route recommendations are not certified "
    "for real rover navigation."
)

with st.expander("Data Sources and Methodology", expanded=False):

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



st.subheader("Jezero Crater — Daytime Thermal Explorer")

try:
    themis_path = "data/raw/jezero_themis_day_ir.tif"
    mars_radius = 3396190

    with rasterio.open(themis_path) as src:

        # Read the infrared raster
        day_ir = src.read(1).astype(float)

        # Get the geographic position of every pixel
        width = src.width
        height = src.height

        longitude = (
            (src.bounds.left +
             (np.arange(width) + 0.5) * src.res[0])
            / mars_radius
        ) * (180 / np.pi) + 180

        latitude = (
            (src.bounds.bottom +
             (np.arange(height) + 0.5) * src.res[1])
            * (180 / np.pi) / mars_radius
        )

        # Flip vertically so southern latitudes appear at the bottom
        day_ir = np.flipud(day_ir)

        # Exclude NoData pixels
        day_ir[day_ir == 0] = np.nan

    # Calculate basic statistics
    valid_values = day_ir[np.isfinite(day_ir)]

    st.write(
        "Explore the infrared signal recorded across "
        "the Jezero region."
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("Valid pixels", f"{len(valid_values):,}")
    col2.metric("Lowest signal", f"{valid_values.min():.0f}")
    col3.metric("Highest signal", f"{valid_values.max():.0f}")

    # Display controls
    palette = st.selectbox(
        "Choose colour palette",
        ["Gray", "Inferno", "Viridis"]
    )

    contrast = st.slider(
        "Adjust image contrast",
        min_value=1,
        max_value=255,
        value=(1, 255)
    )

    # Interactive infrared map
    fig_themis = go.Figure(
        data=go.Heatmap(
            x=longitude,
            y=latitude,
            z=day_ir,
            colorscale=palette,
            zmin=contrast[0],
            zmax=contrast[1],
            colorbar={
                "title": "IR signal",
                "tickmode": "auto"
            },
            hovertemplate=(
                "Longitude: %{x:.3f}°E<br>"
                "Latitude: %{y:.3f}°N<br>"
                "Infrared signal: %{z:.0f}"
                "<extra></extra>"
            )
        )
    )

    fig_themis.update_layout(
        xaxis_title="Longitude (°E)",
        yaxis_title="Planetocentric latitude (°N)",
        height=650,
        margin={"l": 20, "r": 20, "t": 30, "b": 20}
    )

    st.plotly_chart(
        fig_themis,
        width="stretch",
        config={"scrollZoom": True}
    )

    # Pixel value distribution
    st.subheader("Infrared Signal Distribution")

    fig_hist = go.Figure(
        data=go.Histogram(
            x=valid_values,
            nbinsx=40
        )
    )

    fig_hist.update_layout(
        xaxis_title="8-bit infrared signal value",
        yaxis_title="Number of pixels",
        height=350
    )

    st.plotly_chart(fig_hist, width="stretch")

    st.caption(
        "Source: USGS Astrogeology THEMIS Day IR Controlled Mosaic. "
        "Band 9, approximately 12.57 µm, 100 m/pixel. "
        "Values are qualitative 8-bit infrared image values, "
        "not calibrated surface temperatures."
    )

except Exception as e:
    st.error(f"Could not load the THEMIS explorer: {e}")

# This themis image isnt just an image but a rastor that contains geospatial information, in the form of a grid of numerical pixel values. The THEMIS image is a single-band raster, meaning it contains only one layer of data, which corresponds to the infrared intensity. The pixel values are stored as 8-bit unsigned integers, ranging from 0 to 255, where higher values indicate stronger infrared emissions.

st.subheader("Jezero Crater — Nighttime Thermal Explorer")

try:
    night_themis_path = "data/raw/jezero_themis_night_ir.tif"
    mars_radius = 3396190

    with rasterio.open(night_themis_path) as src:
        night_ir = src.read(1).astype(float)
        width = src.width
        height = src.height

        longitude = (
            (src.bounds.left +
             (np.arange(width) + 0.5) * src.res[0])
            / mars_radius
        ) * (180 / np.pi) + 180

        latitude = (
            (src.bounds.bottom +
             (np.arange(height) + 0.5) * src.res[1])
            * (180 / np.pi) / mars_radius
        )

        night_ir = np.flipud(night_ir)
        night_ir[night_ir == 0] = np.nan

    valid_night = night_ir[np.isfinite(night_ir)]

    col1, col2, col3 = st.columns(3)
    col1.metric("Valid pixels", f"{len(valid_night):,}")
    col2.metric("Lowest signal", f"{valid_night.min():.0f}")
    col3.metric("Highest signal", f"{valid_night.max():.0f}")

    night_palette = st.selectbox(
        "Choose nighttime colour palette",
        ["Gray", "Inferno", "Viridis"],
        key="night_palette"
    )

    night_contrast = st.slider(
        "Adjust nighttime image contrast",
        min_value=1,
        max_value=255,
        value=(1, 255),
        key="night_contrast"
    )

    fig_night = go.Figure(data=go.Heatmap(
        x=longitude,
        y=latitude,
        z=night_ir,
        colorscale=night_palette,
        zmin=night_contrast[0],
        zmax=night_contrast[1],
        colorbar={"title": "IR signal"},
        hovertemplate=(
            "Longitude: %{x:.3f}°E<br>"
            "Latitude: %{y:.3f}°N<br>"
            "Infrared signal: %{z:.0f}<extra></extra>"
        )
    ))

    fig_night.update_layout(
        xaxis_title="Longitude (°E)",
        yaxis_title="Planetocentric latitude (°N)",
        height=650,
        margin={"l": 20, "r": 20, "t": 30, "b": 20}
    )

    st.plotly_chart(
        fig_night,
        width="stretch",
        config={"scrollZoom": True}
    )

    st.subheader("Nighttime Infrared Signal Distribution")

    fig_night_hist = go.Figure(data=go.Histogram(
        x=valid_night,
        nbinsx=40
    ))

    fig_night_hist.update_layout(
        xaxis_title="8-bit infrared signal value",
        yaxis_title="Number of pixels",
        height=350
    )

    st.plotly_chart(fig_night_hist, width="stretch")

    st.caption(
        "Source: USGS Astrogeology THEMIS Night IR Controlled Mosaic. "
        "100 m/pixel. Values are qualitative 8-bit infrared image "
        "values, not calibrated surface temperatures."
    )

except Exception as e:
    st.error(f"Could not load the nighttime THEMIS explorer: {e}")

st.subheader("Day vs Night — Thermal Comparison")

try:
    col_day, col_night = st.columns(2)

    with col_day:
        st.markdown("#### Daytime Infrared")
        st.plotly_chart(
            go.Figure(data=go.Heatmap(
                x=longitude,
                y=latitude,
                z=day_ir,
                colorscale="Inferno",
                colorbar={"title": "IR signal"},
                hovertemplate=(
                    "Longitude: %{x:.3f}°E<br>"
                    "Latitude: %{y:.3f}°N<br>"
                    "IR signal: %{z:.0f}<extra></extra>"
                )
            )).update_layout(
                height=450,
                margin={"l": 10, "r": 10, "t": 10, "b": 10},
                xaxis_title="Longitude (°E)",
                yaxis_title="Latitude (°N)"
            ),
            width="stretch"
        )

    with col_night:
        st.markdown("#### Nighttime Infrared")
        st.plotly_chart(
            go.Figure(data=go.Heatmap(
                x=longitude,
                y=latitude,
                z=night_ir,
                colorscale="Viridis",
                colorbar={"title": "IR signal"},
                hovertemplate=(
                    "Longitude: %{x:.3f}°E<br>"
                    "Latitude: %{y:.3f}°N<br>"
                    "IR signal: %{z:.0f}<extra></extra>"
                )
            )).update_layout(
                height=450,
                margin={"l": 10, "r": 10, "t": 10, "b": 10},
                xaxis_title="Longitude (°E)",
                yaxis_title="Latitude (°N)"
            ),
            width="stretch"
        )

    st.caption(
        "Both images show qualitative THEMIS infrared signal values. "
        "They are not calibrated temperature measurements. "
        "Differences in brightness should not be interpreted as "
        "quantitative day-to-night temperature changes."
    )

except NameError:
    st.warning(
        "Load both the daytime and nighttime thermal datasets "
        "to display this comparison."
    )

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

    # Mark the approximate location of Jezero Crater
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


st.subheader("Terrain Hazard Screening")

try:
    # Classify terrain using slope angle
    slope_classes = np.select(
        [
            slope < 10,
            (slope >= 10) & (slope < 20),
            slope >= 20
        ],
        [1, 2, 3],
        default=0
    ).astype(float)

    slope_classes[~np.isfinite(slope)] = np.nan

    fig_hazard = go.Figure(data=go.Heatmap(
        x=x,
        y=y,
        z=slope_classes,
        customdata=slope,
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
        "Categories are illustrative prototype screening bands, "
        "not official NASA rover safety thresholds. "
        "Slope alone does not establish terrain traversability."
    )

except NameError:
    st.warning(
        "Slope data is unavailable. Check that the DEM and "
        "slope calculation sections execute successfully first."
    )

st.subheader("Terrain-Aware Route Planner")

try:
    # Reduce the grid size to make route calculations faster
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

st.dataframe(targets, width="stretch", hide_index=True)

minimum_value = st.slider(
    "Minimum illustrative science score",
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
    width="stretch",
    hide_index=True,
)

st.caption(
    "MARSCOPE prototype. The target records are fictional; "
    "the surface-image preview is from USGS."
)
