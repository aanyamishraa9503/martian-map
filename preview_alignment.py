
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from rasterio.enums import Resampling

files = {
    "Elevation": "data/raw/jezero_elevation.tif",
    "Day IR": "data/processed/jezero_themis_day_aligned.tif",
    "Night IR": "data/processed/jezero_themis_night_aligned.tif",
}

images = {}

for name, path in files.items():
    with rasterio.open(path) as src:
        # Reduce image size for visualization only.
        new_height = 700
        new_width = round(src.width * new_height / src.height)

        data = src.read(
            1,
            out_shape=(new_height, new_width),
            masked=True,
            resampling=Resampling.average
        )

        images[name] = data

        if name == "Elevation":
            bounds = src.bounds

# Plot all three datasets using the same spatial extent.
fig, axes = plt.subplots(1, 3, figsize=(18, 7))

for ax, (name, data) in zip(axes, images.items()):
    if name == "Elevation":
        cmap = "terrain"
    else:
        cmap = "inferno"

    im = ax.imshow(
        data,
        extent=[
            bounds.left,
            bounds.right,
            bounds.bottom,
            bounds.top
        ],
        origin="upper",
        cmap=cmap
    )

    ax.set_title(name)
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

plt.suptitle(
    "MARSCOPE — Jezero Raster Alignment Inspection",
    fontsize=15
)

plt.tight_layout()

plt.savefig(
    "data/processed/alignment_preview.png",
    dpi=150,
    bbox_inches="tight"
)

plt.show()

print("Preview saved: data/processed/alignment_preview.png")
