
from netCDF4 import Dataset
import numpy as np

file_path = "data/raw/dustscenario_MY36_v2-5.nc"

with Dataset(file_path, "r") as dataset:

    longitude = dataset.variables["longitude"][:]
    latitude = dataset.variables["latitude"][:]
    ls = dataset.variables["Ls"][:]
    dust = dataset.variables["cdod610"][:]

    print("LONGITUDE RANGE:")
    print(longitude.min(), "to", longitude.max())
    print("First 10:", longitude[:10])

    print("\nLATITUDE RANGE:")
    print(latitude.min(), "to", latitude.max())
    print("First 10:", latitude[:10])

    # Jezero's approximate coordinates
    jezero_lon = 77.7
    jezero_lat = 18.4

    lon_index = np.abs(longitude - jezero_lon).argmin()
    lat_index = np.abs(latitude - jezero_lat).argmin()

    print("\nNEAREST JEZERO GRID CELL:")
    print("Longitude:", longitude[lon_index])
    print("Latitude:", latitude[lat_index])
    print("Longitude index:", lon_index)
    print("Latitude index:", lat_index)

    print("\nSOLAR LONGITUDE:")
    print("First Ls:", ls[0])
    print("Last Ls:", ls[-1])

    print("\nDUST DATA:")
    print("Shape:", dust.shape)
    print("Minimum:", np.ma.min(dust))
    print("Maximum:", np.ma.max(dust))

    jezero_values = dust[:, lat_index, lon_index]

    print("\nDUST AT NEAREST JEZERO CELL:")
    print("Minimum:", np.ma.min(jezero_values))
    print("Maximum:", np.ma.max(jezero_values))
    print("Mean:", np.ma.mean(jezero_values))
