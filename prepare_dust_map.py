
from netCDF4 import Dataset
import numpy as np

input_file = "data/raw/dustscenario_MY36_v2-5.nc"
output_file = "data/raw/jezero_regional_dust.npz"

with Dataset(input_file, "r") as dataset:

    longitude = dataset.variables["longitude"][:]
    latitude = dataset.variables["latitude"][:]
    dust = dataset.variables["cdod610"][:]

    # Average dust optical depth across all available time entries
    mean_dust = np.ma.mean(dust, axis=0)
    mean_dust = np.ma.filled(mean_dust, np.nan)

    # Select regional coverage around Jezero
    lon_indices = np.where(
        (longitude >= 45) & (longitude <= 105)
    )[0]

    lat_indices = np.where(
        (latitude >= 0) & (latitude <= 45)
    )[0]

    # Sort latitude from south to north
    lat_indices = lat_indices[
        np.argsort(latitude[lat_indices])
    ]

    regional_dust = mean_dust[
        np.ix_(lat_indices, lon_indices)
    ]

    regional_lon = longitude[lon_indices]
    regional_lat = latitude[lat_indices]

    np.savez_compressed(
        output_file,
        longitude=regional_lon,
        latitude=regional_lat,
        dust=regional_dust
    )

    print("Regional dust map prepared!")
    print("Output:", output_file)
    print("Map dimensions:", regional_dust.shape)
    print("Longitude:", regional_lon.min(), "to", regional_lon.max())
    print("Latitude:", regional_lat.min(), "to", regional_lat.max())
    print("Mean optical depth:", np.nanmean(regional_dust))
    print("Minimum:", np.nanmin(regional_dust))
    print("Maximum:", np.nanmax(regional_dust))
