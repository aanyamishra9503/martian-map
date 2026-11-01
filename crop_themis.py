
import math
import rasterio
from rasterio.windows import from_bounds

# Input and output files
input_file = (
    "data/raw/"
    "THEMIS_DayIR_ControlledMosaic_SyrtisMajor_00N45E_100mpp.tif"
)

output_file = "data/raw/jezero_themis_day_ir.tif"

# Jezero Crater geographic boundaries
west = 76.9
east = 78.6
south = 17.5
north = 19.3

# Mars radius from the USGS product metadata
mars_radius = 3396190

# Convert longitude and latitude into projected metres
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

# Open the original THEMIS image
with rasterio.open(input_file) as src:

    # Find the pixel window corresponding to Jezero
    window = from_bounds(
        left,
        bottom,
        right,
        top,
        transform=src.transform
    )

    # Keep the window inside the original image
    window = window.round_offsets().round_lengths()

    print("\nCropping THEMIS image...")

    # Read only the required region
    cropped_image = src.read(1, window=window)

    # Update metadata for the smaller image
    profile = src.profile.copy()
    profile.update(
        height=cropped_image.shape[0],
        width=cropped_image.shape[1],
        transform=src.window_transform(window),
        compress="deflate"
    )

    # Save the cropped GeoTIFF
    with rasterio.open(output_file, "w", **profile) as dst:
        dst.write(cropped_image, 1)

    print("\nCrop completed!")
    print("Output:", output_file)
    print("Width:", cropped_image.shape[1])
    print("Height:", cropped_image.shape[0])
    print("Minimum pixel value:", cropped_image.min())
    print("Maximum pixel value:", cropped_image.max())
# The crop is approximately 100.8 km × 106.7 km