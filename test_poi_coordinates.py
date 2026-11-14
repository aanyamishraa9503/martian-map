
import rasterio
from rasterio.warp import transform
from rasterio.crs import CRS

file_path = "data/raw/jezero_elevation.tif"

points = {
    "Octavia E. Butler": (18.4446, 77.4509),
    "Three Forks": (18.4528, 77.4082),
}

with rasterio.open(file_path) as src:

    mars_projected = src.crs

    # Define the geographic Mars coordinate system.
    mars_geographic = CRS.from_proj4(
        "+proj=longlat +R=3396190 +no_defs +type=crs"
    )

    bounds = src.bounds

    print("POI COORDINATE TRANSFORMATION")
    print("=" * 45)

    for name, (latitude, longitude) in points.items():

        east_values, north_values = transform(
            mars_geographic,
            mars_projected,
            [longitude],
            [latitude]
        )

        east = east_values[0]
        north = north_values[0]

        local_x = (east - bounds.left) / 1000
        local_y = (north - bounds.bottom) / 1000

        inside = (
            bounds.left <= east <= bounds.right
            and bounds.bottom <= north <= bounds.top
        )

        print(f"\n{name}")
        print(f"Projected Easting: {east:.2f} m")
        print(f"Projected Northing: {north:.2f} m")
        print(f"Local X: {local_x:.3f} km")
        print(f"Local Y: {local_y:.3f} km")
        print(f"Inside DEM coverage: {inside}")
