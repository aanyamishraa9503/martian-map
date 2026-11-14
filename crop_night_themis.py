
import math
import rasterio
from rasterio.windows import from_bounds

input_file = (
    "data/raw/"
    "THEMIS_NightIR_ControlledMosaic_SyrtisMajor_00N45E_100mpp.tif"
)

output_file = "data/raw/jezero_themis_night_ir.tif"

# Jezero Crater crop boundaries
west = 76.9
east = 78.6
south = 17.5
north = 19.3

mars_radius = 3396190

def mars_projection(longitude, latitude):
    x = mars_radius * math.radians(longitude - 180)
    y = mars_radius * math.radians(latitude)
    return x, y

left, bottom = mars_projection(west, south)
right, top = mars_projection(east, north)

print("Projected crop boundaries:")
print("Left:", left)
print("Right:", right)
print("Bottom:", bottom)
print("Top:", top)

with rasterio.open(input_file) as src:
    window = from_bounds(
        left, bottom, right, top,
        transform=src.transform
    )

    window = window.round_offsets().round_lengths()

    # Read only the Jezero region
    cropped_image = src.read(1, window=window)

    profile = src.profile.copy()
    profile.update(
        height=cropped_image.shape[0],
        width=cropped_image.shape[1],
        transform=src.window_transform(window),
        compress="deflate"
    )

    with rasterio.open(output_file, "w", **profile) as dst:
        dst.write(cropped_image, 1)

print("\nNight IR crop completed!")
print("Output:", output_file)
print("Width:", cropped_image.shape[1])
print("Height:", cropped_image.shape[0])
print("Minimum pixel value:", cropped_image.min())
print("Maximum pixel value:", cropped_image.max())
