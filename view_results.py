from pathlib import Path
import geopandas as gpd

RESULTS_PATH = Path("data/processed/results.gpkg")

if not RESULTS_PATH.exists():
    print(f"No results file found at {RESULTS_PATH}. Run main.py first.")
    raise SystemExit(1)

gdf = gpd.read_file(RESULTS_PATH, engine="pyogrio")

cols = [c for c in ["address", "suburb", "area_m2", "frontage_m", "fall_m"] if c in gdf.columns]
results = gdf[cols].copy()
results = results.sort_values(["suburb", "address"]).reset_index(drop=True)

print(f"{len(results)} matching parcels\n")
print(results.to_string(
    index=True,
    max_rows=None,
    float_format=lambda x: f"{x:.1f}",
))
