
import os
import rasterio
from rasterio.warp import reproject, Resampling

DEM_PATH = "data/raw/jezero_elevation.tif"

THERMAL_FILES = {
    "day": "data/raw/jezero_themis_day_ir.tif",
    "night": "data/raw/jezero_themis_night_ir.tif",
}

OUTPUT_DIR = "data/processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Use the DEM as the reference grid.
with rasterio.open(DEM_PATH) as dem:
    destination_crs = dem.crs
    destination_transform = dem.transform
    destination_width = dem.width
    destination_height = dem.height

    reference_profile = dem.profile.copy()

for name, source_path in THERMAL_FILES.items():

    output_path = os.path.join(
        OUTPUT_DIR,
        f"jezero_themis_{name}_aligned.tif"
    )

    with rasterio.open(source_path) as src:

        destination = __import__("numpy").zeros(
            (destination_height, destination_width),
            dtype="uint8"
        )

        reproject(
            source=rasterio.band(src, 1),
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=destination_transform,
            dst_crs=destination_crs,
            dst_nodata=0,
            resampling=Resampling.bilinear
        )

        output_profile = reference_profile.copy()
        output_profile.update(
            driver="GTiff",
            count=1,
            dtype="uint8",
            nodata=0,
            compress="deflate"
        )

        with rasterio.open(
            output_path,
            "w",
            **output_profile
        ) as dst:
            dst.write(destination, 1)

    print(f"{name.upper()} alignment completed!")
    print(f"Output: {output_path}")

print("\nBoth THEMIS rasters aligned successfully!")
