import rasterio

file_path = "data/raw/jezero_elevation.tif"

with rasterio.open(file_path) as src:
    print("CRS:")
    print(src.crs)

    print("\nFull CRS definition:")
    print(src.crs.to_wkt())

    print("\nBounds:")
    print(src.bounds)

    print("\nAffine transform:")
    print(src.transform)

    print("\nDimensions:")
    print(src.width, src.height)