"""
Spatial calculations: zone filtering, frontage, and fall.
"""

import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask as raster_mask
from shapely.geometry import mapping
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Zone filtering
# ---------------------------------------------------------------------------

def filter_by_zone(
    parcels: gpd.GeoDataFrame,
    zones: gpd.GeoDataFrame,
    allowed_prefixes: set[str],
    zone_code_col: str = "ZONE_CODE",
) -> gpd.GeoDataFrame:
    """
    Keep only parcels whose centroid falls within an allowed planning zone.

    allowed_prefixes: e.g. {"GRZ", "RGZ"} — matches GRZ1, GRZ2, RGZ1, etc.
    zone_code_col: column in the zones layer containing the zone code string.
    """
    if zone_code_col not in zones.columns:
        available = list(zones.columns)
        raise ValueError(
            f"Column '{zone_code_col}' not found in zones layer. "
            f"Available columns: {available}. "
            f"Set zone_code_col to the correct column name."
        )

    centroids = parcels[["geometry"]].copy()
    centroids.geometry = parcels.geometry.centroid

    joined = centroids.sjoin(
        zones[[zone_code_col, "geometry"]],
        how="left",
        predicate="within",
    )

    mask = joined[zone_code_col].apply(
        lambda z: any(str(z).startswith(prefix) for prefix in allowed_prefixes)
    )

    return parcels[mask.values].copy()


# ---------------------------------------------------------------------------
# Address join
# ---------------------------------------------------------------------------

def join_addresses(
    parcels: gpd.GeoDataFrame,
    addresses: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Add 'address' and 'suburb' columns by spatially joining address points to parcels.

    Each address point in VMADD sits within its associated property polygon.
    For parcels with multiple addresses (rare), the first match is kept.
    Vacant/unaddressed parcels get NaN.
    """
    addr_cols = addresses[["EZI_ADDRESS", "LOCALITY_NAME", "geometry"]].copy()

    joined = gpd.sjoin(parcels, addr_cols, how="left", predicate="contains")

    # Drop duplicates keeping first address per parcel
    joined = joined[~joined.index.duplicated(keep="first")]

    result = parcels.copy()
    result["address"] = joined["EZI_ADDRESS"].values
    result["suburb"] = joined["LOCALITY_NAME"].values
    return result


# ---------------------------------------------------------------------------
# Frontage
# ---------------------------------------------------------------------------

def compute_frontage(
    parcels: gpd.GeoDataFrame,
    road_casements: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Add a 'frontage_m' column: length of parcel boundary shared with a road casement.

    Road casement polygons (ROAD_CASEMENT_POLYGON from VMPROP) share a direct
    boundary edge with adjacent parcels, so the frontage is simply the length
    of the parcel boundary that falls inside a casement polygon — no buffering needed.
    """
    casement_union = unary_union(road_casements.geometry)

    frontages = []
    for geom in parcels.geometry:
        shared = geom.boundary.intersection(casement_union)
        frontages.append(shared.length if not shared.is_empty else 0.0)

    result = parcels.copy()
    result["frontage_m"] = frontages
    return result


def filter_by_frontage(gdf: gpd.GeoDataFrame, criteria) -> gpd.GeoDataFrame:
    mask = gdf["frontage_m"] >= criteria.min_frontage
    if criteria.max_frontage is not None:
        mask &= gdf["frontage_m"] <= criteria.max_frontage
    return gdf[mask].copy()


# ---------------------------------------------------------------------------
# Fall (slope / elevation change)
# ---------------------------------------------------------------------------

def compute_fall(
    parcels: gpd.GeoDataFrame,
    dem_path: str,
    sample_resolution: int = 5,
) -> gpd.GeoDataFrame:
    """
    Add a 'fall_m' column: max − min elevation within each parcel.

    dem_path: GeoTIFF DEM in a metric CRS (or will be auto-handled by rasterio).
    sample_resolution: sample every N pixels within the parcel mask.

    DEMs for Victoria: https://elevation.fsdf.org.au/  (1m or 5m resolution)
    """
    falls = []

    with rasterio.open(dem_path) as src:
        for geom in parcels.geometry:
            try:
                out_image, _ = raster_mask(src, [mapping(geom)], crop=True, nodata=src.nodata)
                data = out_image[0]
                valid = data[data != src.nodata] if src.nodata is not None else data.flatten()
                if len(valid) == 0:
                    falls.append(None)
                else:
                    falls.append(float(valid.max() - valid.min()))
            except Exception:
                falls.append(None)

    result = parcels.copy()
    result["fall_m"] = falls
    return result


def filter_by_fall(gdf: gpd.GeoDataFrame, criteria) -> gpd.GeoDataFrame:
    if criteria.max_fall is None:
        return gdf
    return gdf[gdf["fall_m"].notna() & (gdf["fall_m"] <= criteria.max_fall)].copy()
