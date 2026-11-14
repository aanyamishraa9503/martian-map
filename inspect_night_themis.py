
import rasterio

input_file = (
    "data/raw/"
    "THEMIS_NightIR_ControlledMosaic_SyrtisMajor_00N45E_100mpp.tif"
)

with rasterio.open(input_file) as src:
    print("Width:", src.width)
    print("Height:", src.height)
    print("Bands:", src.count)
    print("Coordinate system:", src.crs)
    print("Bounds:", src.bounds)
    print("Resolution:", src.res)
    print("Data type:", src.dtypes)
    print("NoData:", src.nodata)

    image = src.read(1)

    print("Minimum pixel value:", image.min())
    print("Maximum pixel value:", image.max())