#raster img analysis trial version


from pathlib import Path
import sys
import json
import math
import platform
from datetime import datetime, timezone

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import transform_bounds


# --------------------------------------------------
# MARSCOPE: Mars raster inspection tool
# --------------------------------------------------

DEFAULT_FOLDER = Path("data/raw")
REPORT_FOLDER = Path("reports")
PREVIEW_MAX_SIZE = 1200  # Maximum dimension for sampled statistics


def json_safe(value):
    """Convert values into JSON-compatible Python types."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def clean_tags(tags):
    """Return metadata tags as a normal dictionary."""
    return {str(k): str(v) for k, v in tags.items()}


def inspect_raster(path):
    print(f"\nInspecting: {path.name}")

    report = {
        "file": path.name,
        "path": str(path.resolve()),
        "file_size_bytes": path.stat().st_size,
        "file_size_mib": round(path.stat().st_size / (1024 ** 2), 3),
        "inspection_time_utc": datetime.now(timezone.utc).isoformat(),
        "status": "success",
    }

    try:
        with rasterio.open(path) as src:
            report["driver"] = src.driver
            report["dimensions"] = {
                "width_pixels": src.width,
                "height_pixels": src.height,
                "band_count": src.count,
                "total_cells_per_band": src.width * src.height,
            }

            report["raster"] = {
                "data_types": list(src.dtypes),
                "band_descriptions": list(src.descriptions),
                "band_units": list(src.units),
                "nodata_values": list(src.nodatavals),
                "scales": list(src.scales),
                "offsets": list(src.offsets),
                "color_interpretation": [
                    str(c) for c in src.colorinterp
                ],
                "block_shapes": [list(s) for s in src.block_shapes],
                "overviews_per_band": [
                    src.overviews(i)
                    for i in range(1, src.count + 1)
                ],
                "compression": (
                    src.compression.name if src.compression else None
                ),
                "is_tiled": src.is_tiled,
            }

            report["coordinate_system"] = {
                "crs": str(src.crs) if src.crs else None,
                "crs_wkt": src.crs.to_wkt() if src.crs else None,
                "transform": list(src.transform),
                "bounds_projected": {
                    "left": src.bounds.left,
                    "bottom": src.bounds.bottom,
                    "right": src.bounds.right,
                    "top": src.bounds.top,
                },
                "pixel_size_x": src.res[0],
                "pixel_size_y": src.res[1],
            }

            # Attempt conversion to the CRS's own geographic coordinates.
            # For Mars data, these are planetary coordinates, NOT Earth GPS.
            geographic_bounds = None
            if src.crs and src.crs.geodetic_crs:
                try:
                    geographic_bounds = transform_bounds(
                        src.crs,
                        src.crs.geodetic_crs,
                        *src.bounds,
                        densify_pts=21,
                    )
                except Exception as exc:
                    report["coordinate_system"][
                        "geographic_bounds_conversion_note"
                    ] = str(exc)

            if geographic_bounds:
                report["coordinate_system"][
                    "bounds_in_geodetic_crs"
                ] = {
                    "crs": str(src.crs.geodetic_crs),
                    "left": geographic_bounds[0],
                    "bottom": geographic_bounds[1],
                    "right": geographic_bounds[2],
                    "top": geographic_bounds[3],
                    "note": (
                        "Coordinates in the raster's planetary geodetic CRS; "
                        "not necessarily Earth longitude/latitude."
                    ),
                }

            report["metadata"] = {
                "dataset_tags": clean_tags(src.tags()),
                "band_tags": {
                    str(i): clean_tags(src.tags(i))
                    for i in range(1, src.count + 1)
                },
                "subdatasets": list(src.subdatasets),
            }

            band_reports = []

            for band in range(1, src.count + 1):
                # Stream the entire raster in windows. This calculates
                # exact valid-pixel count, min, max, mean and standard
                # deviation without loading the entire band into RAM.
                valid_count = 0
                nodata_count = 0
                total = 0.0
                total_squares = 0.0
                minimum = float("inf")
                maximum = float("-inf")

                for _, window in src.block_windows(band):
                    data = src.read(band, window=window, masked=True)
                    values = np.asarray(data.compressed(), dtype=np.float64)

                    # Also reject non-finite floating point values.
                    values = values[np.isfinite(values)]

                    if values.size == 0:
                        continue

                    valid_count += int(values.size)
                    minimum = min(minimum, float(values.min()))
                    maximum = max(maximum, float(values.max()))
                    total += float(np.sum(values, dtype=np.float64))
                    total_squares += float(
                        np.sum(values * values, dtype=np.float64)
                    )

                total_cells = src.width * src.height
                nodata_count = total_cells - valid_count

                if valid_count:
                    mean = total / valid_count
                    variance = max(
                        0.0,
                        total_squares / valid_count - mean * mean
                    )
                    std_dev = math.sqrt(variance)

                    stats = {
                        "valid_pixel_count": valid_count,
                        "invalid_or_nodata_count": nodata_count,
                        "valid_pixel_percent": (
                            100 * valid_count / total_cells
                        ),
                        "minimum": minimum,
                        "maximum": maximum,
                        "mean": mean,
                        "standard_deviation": std_dev,
                    }
                else:
                    stats = {
                        "valid_pixel_count": 0,
                        "invalid_or_nodata_count": nodata_count,
                    }

                # Sample a downsampled overview for approximate
                # percentiles. These are estimates, not exact quantiles.
                out_height = min(src.height, PREVIEW_MAX_SIZE)
                out_width = min(src.width, PREVIEW_MAX_SIZE)

                preview = src.read(
                    band,
                    out_shape=(out_height, out_width),
                    masked=True,
                    resampling=Resampling.nearest,
                )

                sample = np.asarray(
                    preview.compressed(), dtype=np.float64
                )
                sample = sample[np.isfinite(sample)]

                if sample.size:
                    stats["sampled_percentiles_approximate"] = {
                        "sample_pixel_count": int(sample.size),
                        "p02": float(np.percentile(sample, 2)),
                        "p25": float(np.percentile(sample, 25)),
                        "p50_median": float(np.percentile(sample, 50)),
                        "p75": float(np.percentile(sample, 75)),
                        "p98": float(np.percentile(sample, 98)),
                        "method": (
                            "Nearest-neighbour downsample; approximate "
                            "percentiles, not full-resolution quantiles."
                        ),
                    }

                band_reports.append({
                    "band_number": band,
                    "statistics": stats,
                })

            report["bands"] = band_reports

    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"

    return json_safe(report)


def find_tiffs(arguments):
    """Accept TIFF file paths or folders."""
    if not arguments:
        targets = [DEFAULT_FOLDER]
    else:
        targets = [Path(arg) for arg in arguments]

    files = []

    for target in targets:
        if target.is_file():
            if target.suffix.lower() in {".tif", ".tiff"}:
                files.append(target)
            else:
                print(f"Skipping non-TIFF file: {target}")

        elif target.is_dir():
            files.extend(
                p for p in target.rglob("*")
                if p.is_file() and p.suffix.lower() in {".tif", ".tiff"}
            )
        else:
            print(f"Not found: {target}")

    # Deduplicate and sort file paths.
    return sorted(set(files), key=lambda p: str(p).lower())


def main():
    REPORT_FOLDER.mkdir(parents=True, exist_ok=True)
    files = find_tiffs(sys.argv[1:])

    if not files:
        print("No TIFF files found.")
        print("Usage: python inspect_mars_raster.py data/raw")
        print("Or:    python inspect_mars_raster.py path/to/file.tif")
        return

    print(f"Found {len(files)} TIFF file(s).")
    print(f"Python: {platform.python_version()}")

    summary = []

    for path in files:
        result = inspect_raster(path)
        summary.append(result)

        output = REPORT_FOLDER / f"{path.stem}_report.json"
        output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"Report saved: {output}")
        print(f"Status: {result['status']}")

        if result["status"] == "success":
            print(f"Dimensions: {result['dimensions']}")
            print(f"CRS: {result['coordinate_system']['crs']}")

            for band in result.get("bands", []):
                print(
                    f"Band {band['band_number']} statistics: "
                    f"{band['statistics']}"
                )
        else:
            print(result.get("error", "Unknown error"))

    summary_path = REPORT_FOLDER / "all_rasters_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nFinished. Combined report: {summary_path}")


if __name__ == "__main__":
    main()


import csv
import numpy as np
import rasterio


def export_elevation_coordinates(
    tif_path,
    output_csv="reports/elevation_coordinate_samples.csv",
    samples_per_axis=100,
):
    with rasterio.open(tif_path) as src:
        # Sample pixel centres across the raster extent
        rows = np.linspace(
            0, src.height - 1, samples_per_axis, dtype=int
        )
        cols = np.linspace(
            0, src.width - 1, samples_per_axis, dtype=int
        )

        output_rows = []

        for row in rows:
            for col in cols:
                value = src.read(
                    1,
                    window=((row, row + 1), (col, col + 1)),
                    masked=True,
                )[0, 0]

                if np.ma.is_masked(value) or not np.isfinite(value):
                    continue

                # Convert pixel index to its centre coordinate
                x, y = rasterio.transform.xy(
                    src.transform, row, col, offset="center"
                )

                output_rows.append({
                    "row": int(row),
                    "column": int(col),
                    "x_projected": x,
                    "y_projected": y,
                    "elevation_raw": float(value),
                    "crs": str(src.crs),
                })

        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "row",
                    "column",
                    "x_projected",
                    "y_projected",
                    "elevation_raw",
                    "crs",
                ],
            )
            writer.writeheader()
            writer.writerows(output_rows)

    print(f"Saved {len(output_rows)} samples to {output_csv}")