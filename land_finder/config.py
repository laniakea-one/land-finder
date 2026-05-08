from dataclasses import dataclass, field


# Zone code prefixes to include (matched against Vicmap Planning ZONE_CODE).
# GRZ = General Residential Zone, RGZ = Residential Growth Zone.
# Subcategories (GRZ1, GRZ2, RGZ1, etc.) are matched automatically by prefix.
ALLOWED_ZONES = {"GRZ", "RGZ"}

# Target suburbs (must match LOCALITY_NAME values in Vicmap Address — uppercase).
SUBURBS = [
    "BEAUMARIS",
    "BENTLEIGH",
    "BENTLEIGH EAST",
    "BRIGHTON",
    "BRIGHTON EAST",
    "CARNEGIE",
    "CAULFIELD",
    "CAULFIELD SOUTH",
    "CLARINDA",
    "CLAYTON",
    "CLAYTON SOUTH",
    "GLEN HUNTLY",
    "HAMPTON",
    "HEATHERTON",
    "HUGHESDALE",
    "HUNTINGDALE",
    "MCKINNON",
    "MENTONE",
    "MOORABBIN",
    "MORDIALLOC",
    "MURRUMBEENA",
    "OAKLEIGH",
    "OAKLEIGH SOUTH",
    "ORMOND",
    "PARKDALE"      
]

@dataclass
class SearchCriteria:
    min_area: float = 600.0        # m²
    max_area: float = 700.0        # m²
    min_frontage: float = 15.0     # m
    max_frontage: float | None = None
    max_fall: float | None = None  # m, elevation difference across parcel
    suburbs: list[str] = field(default_factory=lambda: SUBURBS)

DEFAULT_CRITERIA = SearchCriteria()

# Vicmap coordinate reference system (GDA2020 / MGA zone 55)
VICMAP_CRS = "EPSG:7855"
# Working CRS for metric calculations
METRIC_CRS = "EPSG:7855"
