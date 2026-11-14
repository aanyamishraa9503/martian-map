
import rasterio
from PIL import Image

files = {
    "CTX Elevation DEM": "data/raw/jezero_elevation.tif",
    "THEMIS Day IR": "data/raw/jezero_themis_day_ir.tif",
    "THEMIS Night IR": "data/raw/jezero_themis_night_ir.tif",
}

for name, path in files.items():
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    with rasterio.open(path) as src:
        print("CRS:", src.crs)
        print("Dimensions:", src.width, "x", src.height)
        print("Bounds:", src.bounds)
        print("Resolution:", src.res)
        print("Transform:", src.transform)
        print("NoData:", src.nodata)
        print("Data type:", src.dtypes)
        print("Band count:", src.count)

print("\n" + "=" * 60)
print("CTX BROWSE IMAGE")
print("=" * 60)

image_path = "data/raw/jezero_ctx_browse.jpg"

with Image.open(image_path) as image:
    print("Dimensions:", image.size)
    print("Format:", image.format)
    print("Metadata:", image.info)

from rasterio.warp import transform_bounds

print("\n" + "=" * 60)
print("THEMIS TO DEM COORDINATE TRANSFORMATION")
print("=" * 60)

with rasterio.open("data/raw/jezero_elevation.tif") as dem:
    dem_crs = dem.crs
    dem_bounds = dem.bounds

    print("\nDEM bounds:")
    print(dem_bounds)

    for name, path in [
        ("THEMIS Day IR", "data/raw/jezero_themis_day_ir.tif"),
        ("THEMIS Night IR", "data/raw/jezero_themis_night_ir.tif"),
    ]:
        with rasterio.open(path) as src:
            transformed = transform_bounds(
                src.crs,
                dem_crs,
                *src.bounds,
                densify_pts=21
            )

            print(f"\n{name}")
            print("Transformed bounds:")
            print(transformed)

            left = max(dem_bounds.left, transformed[0])
            bottom = max(dem_bounds.bottom, transformed[1])
            right = min(dem_bounds.right, transformed[2])
            top = min(dem_bounds.top, transformed[3])

            if left < right and bottom < top:
                print("Overlap with DEM: YES")
                print("Intersection:")
                print((left, bottom, right, top))
            else:
                print("Overlap with DEM: NO")
