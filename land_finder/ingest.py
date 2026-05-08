"""
Load and pre-filter Vicmap data.

Downloads from Victorian Spatial Datamart (https://datashare.maps.vic.gov.au/):
  - Vicmap Property  → VMPROP.gdb
  - Vicmap Transport → VMTRANS.gdb
  - Vicmap Planning  → VMPLAN.gdb
"""

import pyogrio
import geopandas as gpd
from pathlib import Path
from .config import METRIC_CRS, SearchCriteria


def list_layers(gdb_path: str | Path) -> list:
    """List all layers in a .gdb with their geometry types."""
    return pyogrio.list_layers(str(gdb_path)).tolist()


def _geometry_layers(gdb_path: Path) -> list[str]:
    """Return only layers that have geometry (skip attribute-only tables)."""
    return [row[0] for row in pyogrio.list_layers(str(gdb_path)) if row[1] is not None]


def load_zones(gdb_path: str | Path, bbox: tuple) -> gpd.GeoDataFrame:
    """Load planning zone polygons clipped to a bounding box."""
    path = Path(gdb_path)
    if not path.exists():
        raise FileNotFoundError(f"Vicmap Planning .gdb not found at {path}")

    return gpd.read_file(path, layer="PLAN_ZONE", engine="pyogrio", bbox=bbox).to_crs(METRIC_CRS)


def load_parcels(gdb_path: str | Path, bbox: tuple) -> gpd.GeoDataFrame:
    """
    Load parcel polygons clipped to a bounding box.

    bbox: (minx, miny, maxx, maxy) in METRIC_CRS — use zones.total_bounds.
    """
    path = Path(gdb_path)
    if not path.exists():
        raise FileNotFoundError(f"Vicmap Property .gdb not found at {path}")

    gdf = gpd.read_file(path, layer="PARCEL_VIEW", engine="pyogrio", bbox=bbox)
    gdf = gdf.to_crs(METRIC_CRS)
    gdf["area_m2"] = gdf.geometry.area
    return gdf.reset_index(drop=True)


def load_road_casements(gdb_path: str | Path, bbox: tuple) -> gpd.GeoDataFrame:
    """
    Load road casement polygons from VMPROP.gdb clipped to a bounding box.

    Road casements represent the legal road reserve boundary. Parcels share an
    edge directly with casement polygons, making them the most accurate source
    for frontage measurement — no buffer guessing required.
    """
    path = Path(gdb_path)
    if not path.exists():
        raise FileNotFoundError(f"Vicmap Property .gdb not found at {path}")

    return gpd.read_file(
        path, layer="ROAD_CASEMENT_POLYGON", engine="pyogrio", bbox=bbox
    ).to_crs(METRIC_CRS)


def load_addresses(gdb_path: str | Path, suburbs: list[str]) -> gpd.GeoDataFrame:
    """
    Load address points from Vicmap Address (VMADD) filtered to target suburbs.

    Download from: https://datashare.maps.vic.gov.au/
    Product: Vicmap Address → ESRI File Geodatabase → save as data/raw/VMADD.gdb

    Key output columns: EZI_ADDRESS (full address string), LOCALITY_NAME (suburb).
    The returned GeoDataFrame's bounding box defines the spatial extent for all
    subsequent data loads.
    """
    path = Path(gdb_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Vicmap Address .gdb not found at {path}\n"
            "Download from: https://datashare.maps.vic.gov.au/\n"
            "Product: Vicmap Address → ESRI File Geodatabase"
        )

    available = _geometry_layers(path)
    layer = next((l for l in available if "ADDRESS" in l.upper()), None)
    if layer is None:
        raise ValueError(f"No ADDRESS layer found in {path}. Geometry layers: {available}")

    gdf = gpd.read_file(path, layer=layer, engine="pyogrio").to_crs(METRIC_CRS)
    upper = [s.upper() for s in suburbs]
    gdf = gdf[gdf["LOCALITY_NAME"].str.upper().isin(upper)].copy()
    return gdf.reset_index(drop=True)


def filter_by_area(gdf: gpd.GeoDataFrame, criteria: SearchCriteria) -> gpd.GeoDataFrame:
    mask = gdf["area_m2"] >= criteria.min_area
    if criteria.max_area is not None:
        mask &= gdf["area_m2"] <= criteria.max_area
    return gdf[mask].copy()
