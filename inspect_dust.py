
from netCDF4 import Dataset

file_path = "data/raw/dustscenario_MY36_v2-5.nc"

with Dataset(file_path, "r") as dataset:
    print("Dimensions:")
    for name, dimension in dataset.dimensions.items():
        print(name, len(dimension))

    print("\nVariables:")
    for name, variable in dataset.variables.items():
        print(
            name,
            variable.dimensions,
            variable.shape,
            variable.units,
            variable.long_name
        )

    print("\nGlobal attributes:")
    for name in dataset.ncattrs():
        print(name, ":", getattr(dataset, name))
