
import rasterio
import numpy as np
from rasterio.warp import reproject, Resampling

source_path = "data/raw/jezero_ctx_ortho.tif"
reference_path = "data/raw/jezero_elevation.tif"
output_path = "data/processed/jezero_ctx_aligned.tif"

with rasterio.open(reference_path) as reference:
    destination_profile = {
        "driver": "GTiff",
        "height": reference.height,
        "width": reference.width,
        "count": 1,
        "dtype": "uint8",
        "crs": reference.crs,
        "transform": reference.transform,
        "compress": "deflate",
        "tiled": True
    }

    destination = np.zeros(
        (reference.height, reference.width),
        dtype=np.uint8
    )

    with rasterio.open(source_path) as source:
        reproject(
            source=rasterio.band(source, 1),
            destination=destination,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=reference.transform,
            dst_crs=reference.crs,
            resampling=Resampling.average
        )

with rasterio.open(output_path, "w", **destination_profile) as output:
    output.write(destination, 1)

print("CTX alignment completed!")
print("Output:", output_path)
print("Dimensions:", destination.shape)
