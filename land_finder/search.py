"""
Main search pipeline: load data, filter, output results.
"""

from pathlib import Path
import geopandas as gpd

from .config import SearchCriteria, DEFAULT_CRITERIA, ALLOWED_ZONES
from .ingest import load_addresses, load_zones, load_parcels, load_road_casements, filter_by_area
from .spatial import join_addresses, filter_by_zone, compute_frontage, filter_by_frontage, compute_fall, filter_by_fall


def run_search(
    parcels_gdb: str | Path,
    planning_gdb: str | Path,
    address_gdb: str | Path,
    dem_path: str | Path | None = None,
    criteria: SearchCriteria = DEFAULT_CRITERIA,
    output_path: str | Path | None = None,
) -> gpd.GeoDataFrame:
    print(f"Loading addresses for suburbs: {criteria.suburbs}")
    addresses = load_addresses(address_gdb, criteria.suburbs)
    print(f"  {len(addresses)} address points loaded")

    bbox = tuple(addresses.total_bounds)

    print("Loading parcels...")
    parcels = load_parcels(parcels_gdb, bbox)
    print(f"  {len(parcels)} parcels in bounding box")

    parcels = filter_by_area(parcels, criteria)
    print(f"  {len(parcels)} after area filter ({criteria.min_area}–{criteria.max_area} m²)")

    print(f"Filtering by zone ({', '.join(sorted(ALLOWED_ZONES))})...")
    zones = load_zones(planning_gdb, bbox)
    parcels = filter_by_zone(parcels, zones, ALLOWED_ZONES)
    print(f"  {len(parcels)} after zone filter")

    print("Computing frontage...")
    casements = load_road_casements(parcels_gdb, bbox)
    parcels = compute_frontage(parcels, casements)
    parcels = filter_by_frontage(parcels, criteria)
    print(f"  {len(parcels)} after frontage filter (≥{criteria.min_frontage} m)")

    print("Joining addresses...")
    parcels = join_addresses(parcels, addresses)
    before = len(parcels)
    parcels = parcels[parcels["address"].notna()].copy()
    print(f"  {len(parcels)} after dropping {before - len(parcels)} unaddressed parcels")

    if dem_path is not None:
        print("Computing fall from DEM...")
        parcels = compute_fall(parcels, str(dem_path))
        parcels = filter_by_fall(parcels, criteria)
        print(f"  {len(parcels)} after fall filter")

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix == ".gpkg":
            parcels.to_file(out, driver="GPKG")
        elif out.suffix == ".geojson":
            parcels.to_file(out, driver="GeoJSON")
        else:
            parcels.drop(columns="geometry").to_csv(out, index=False)
        print(f"Results saved to {out}")

    return parcels
