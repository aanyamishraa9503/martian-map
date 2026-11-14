# MARSCOPE
### Mars Exploration & Surface Observation Platform

MARSCOPE is an interactive Mars exploration and visualization prototype focused on Jezero Crater, the landing region of NASA's Perseverance rover.

The platform integrates surface imagery, elevation data, derived terrain characteristics, infrared observations, atmospheric dust information, documented mission landmarks, and experimental terrain-aware route comparison into a unified interface.

## Key Features

- **Surface Exploration:** Browse Jezero Crater using CTX imagery.
- **Elevation Mapping:** Visualize regional elevation using a USGS digital elevation model.
- **Slope Analysis:** Derive terrain slope from elevation measurements.
- **Daytime Thermal Explorer:** Explore daytime THEMIS infrared imagery.
- **Nighttime Thermal Explorer:** Explore nighttime THEMIS infrared imagery.
- **Day–Night Comparison:** Compare qualitative infrared signals across daytime and nighttime observations.
- **Atmospheric Dust Explorer:** Visualize regional atmospheric dust optical depth using a Mars dust climatology dataset.
- **Science Points of Interest:** Explore selected Perseverance mission landmarks and geological features.
- **Terrain Hazard Screening:** Classify terrain into illustrative slope categories.
- **Terrain-Aware Route Planner:** Compare a shortest-grid path with an experimental A* route that applies a slope-dependent movement penalty.
- **Demonstration Exploration Targets:** Interact with simulated exploration points to demonstrate the interface.

## Technology Stack

- Python
- Streamlit
- NumPy
- Pandas
- Plotly
- Rasterio
- NetCDF4
- Requests
- Pillow

## Scientific Data Sources

### 1. Surface Imagery and Elevation

**United States Geological Survey (USGS)**

- [Jezero Crater CTX Browse Mosaic](https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/browse_M20_JezeroCrater_CTXortho_mosaic_5m.jpg)
- [Jezero Crater CTX Digital Elevation Model](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif)

### 2. Thermal Infrared Observations

**NASA THEMIS / USGS Controlled Mosaics**

- [THEMIS Day IR Mosaic](https://planetarymaps.usgs.gov/mosaic/Mars/THEMIS_controlled_mosaics/SyrtisMajor_DayIR_31July2014/THEMIS_DayIR_ControlledMosaic_SyrtisMajor_00N45E_100mpp.tif)
- [THEMIS Night IR Mosaic](https://planetarymaps.usgs.gov/mosaic/Mars/THEMIS_controlled_mosaics/SyrtisMajor_NightIR_30April2015/THEMIS_NightIR_ControlledMosaic_SyrtisMajor_00N45E_100mpp.tif)

### 3. Atmospheric Dust Dataset

- [Mars Dust Climatology Dataset – MY36 Version 2.5](https://www-mars.lmd.jussieu.fr/mars/dust_climatology/dataset_v2/dustscenario_MY36_v2-5.nc)
- Based on Mars Climate Sounder observations and reconstructed atmospheric dust distributions.
- Associated research: Montabone et al. (2015, 2020).

## Methodology

### Terrain Processing
Elevation data are processed using Rasterio and NumPy. Slope is derived from elevation gradients and expressed in degrees.

### Thermal Visualization
Daytime and nighttime THEMIS infrared imagery are cropped to the Jezero region and visualized as separate qualitative signal layers. These image values are not presented as calibrated surface temperatures.

### Atmospheric Dust Processing
The MY36 Version 2.5 dataset is processed to create a regional dust optical depth layer. The regional visualization represents an average across the available reconstructed entries rather than current atmospheric conditions.

### Terrain-Aware Route Comparison
An experimental A* algorithm compares grid-based shortest paths with paths that incorporate a slope-dependent movement penalty.

The route planner is a prototype visualization tool and does not incorporate all factors required for real rover navigation.

## Project Structure

```text
martian-map/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── metadata/
│   │   └── dataset_inventory.csv
│   │
│   └── raw/
│       ├── jezero_ctx_browse.jpg
│       ├── jezero_elevation.tif
│       ├── jezero_regional_dust.npz
│       ├── jezero_themis_day_ir.tif
│       └── jezero_themis_night_ir.tif
│
├── crop_themis.py
├── crop_night_themis.py
├── prepare_dust_map.py
├── inspect_dust.py
├── inspect_dust_details.py
└── ...
```

## Installation and Execution

### Prerequisites
- Python 3.10 or later
- Git

### 1. Clone the repository

```bash
git clone https://github.com/aanyamishraa9503/martian-map.git
cd martian-map
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run MARSCOPE

```bash
python -m streamlit run app.py
```

The application will be available at:

`http://localhost:8501`

**Note:** The processed Jezero datasets are included in the repository. The original regional THEMIS mosaics and dust NetCDF source file are not included because of their size. Their source links are provided above.

## Limitations

- The platform is a research and visualization prototype, not a certified rover navigation system.
- THEMIS infrared image values are qualitative and should not be interpreted as calibrated temperatures.
- Atmospheric dust visualization represents historical climatological data, not live Martian weather.
- Slope-based terrain classification uses illustrative screening categories, not official NASA rover safety thresholds.
- Route planning does not fully account for obstacles, loose sediment, rock distribution, rover mobility constraints, or other operational hazards.
- Demonstration exploration targets are simulated and are not verified geological locations.
- Scientific datasets have different spatial resolutions, acquisition periods, and processing characteristics.

## Future Scope

- Integration of additional NASA planetary datasets.
- More comprehensive terrain and obstacle analysis.
- Improved route-cost models incorporating multiple terrain parameters.
- Expanded scientific points of interest and mission context.
- Enhanced interactive 3D terrain visualization.
- Improved data provenance and reproducibility.

## Development Acknowledgment

AI-assisted tools were used during parts of the development process for coding support, debugging, and documentation. Scientific data sources and project limitations are identified separately.

---

**MARSCOPE — Exploring the Martian Surface Through Integrated Scientific Data.**