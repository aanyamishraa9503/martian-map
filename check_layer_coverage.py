
import rasterio
import numpy as np

files = {
    "CTX Surface": "data/processed/jezero_ctx_aligned.tif",
    "Elevation DEM": "data/raw/jezero_elevation.tif",
    "THEMIS Day IR": "data/processed/jezero_themis_day_aligned.tif",
    "THEMIS Night IR": "data/processed/jezero_themis_night_aligned.tif",
}

reference = None

for name, path in files.items():
    with rasterio.open(path) as src:
        data = src.read(1, masked=True)

        valid = data.compressed()
        valid_count = len(valid)
        total_count = src.width * src.height
        coverage = (valid_count / total_count) * 100

        print("\n" + "=" * 45)
        print(name)
        print("=" * 45)

        print("Dimensions:", src.width, "x", src.height)
        print("Resolution:", src.res)
        print("Valid pixels:", valid_count)
        print("Coverage:", round(coverage, 2), "%")

        if valid_count > 0:
            print("Minimum:", valid.min())
            print("Maximum:", valid.max())
            print("Mean:", round(float(valid.mean()), 3))

        if reference is None:
            reference = (src.crs, src.transform, src.width, src.height)
            print("Reference layer established.")
        else:
            matches = (
                src.crs == reference[0]
                and src.transform == reference[1]
                and src.width == reference[2]
                and src.height == reference[3]
            )
            print("Same pixel grid:", matches)
