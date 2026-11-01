
import rasterio

file_path = (
    "data/raw/"
    "THEMIS_DayIR_ControlledMosaic_SyrtisMajor_00N45E_100mpp.tif"
)

with rasterio.open(file_path) as src:
    print("\n--- THEMIS FILE INFORMATION ---")

    print("Width:", src.width)
    print("Height:", src.height)
    print("Bands:", src.count)
    print("Coordinate system:", src.crs)
    print("Bounds:", src.bounds)
    print("Resolution:", src.res)
    print("Data type:", src.dtypes)
    print("NoData:", src.nodata)

    print("\n--- IMAGE STATISTICS ---")

    band = src.read(1, masked=True)

    print("Minimum:", band.min())
    print("Maximum:", band.max())
    print("Mean:", band.mean())
# we need to crop the themis image to the jezero crater area. The center of the crater is at approximately 18.38°N, 77.58°E. The THEMIS image covers a much larger area, so we will define a bounding box around the crater and crop the image accordingly.

