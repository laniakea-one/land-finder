"""
Entry point.

Edit search criteria and suburbs in land_finder/config.py.
Edit data file paths below.
"""

from pathlib import Path
from land_finder import run_search
from land_finder.config import DEFAULT_CRITERIA

DATA_DIR = Path("data/raw")

results = run_search(
    parcels_gdb=DATA_DIR / "VMPROP.gdb",
    planning_gdb=DATA_DIR / "VMPLAN.gdb",
    address_gdb=DATA_DIR / "VMADD.gdb",
    dem_path=None,
    criteria=DEFAULT_CRITERIA,
    output_path="data/processed/results.gpkg",
)

print(f"\n{len(results)} matching parcels found. Run view_results.py to see full list.")
