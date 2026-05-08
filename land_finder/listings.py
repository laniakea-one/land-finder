"""
Cross-reference parcels against real estate listings (Domain API).

Domain developer portal: https://developer.domain.com.au/
Set DOMAIN_API_KEY in a .env file or environment variable.
"""

import os
import requests
from geopandas import GeoDataFrame


########
# Issue: Need greater API access for this to work (specifically the "Agents & Listings" package).
# This requires disclosing an ABN to Domain.com, and possibly paying for API requests.
########

DOMAIN_LISTINGS_URL = "https://api.domain.com.au/v1/listings/residential/_search"


def _get_api_key() -> str:
    key = os.getenv("DOMAIN_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "DOMAIN_API_KEY not set. Register at https://developer.domain.com.au/"
        )
    return key


def fetch_listings_for_suburb(suburb: str, state: str = "VIC") -> list[dict]:
    """Return active land listings from Domain for one suburb."""
    payload = {
        "listingType": "Sale",
        "propertyTypes": ["Land"],
        "locations": [{"state": state, "suburb": suburb}],
        "pageSize": 200,
    }
    headers = {"X-Api-Key": _get_api_key(), "Content-Type": "application/json"}
    resp = requests.post(DOMAIN_LISTINGS_URL, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def tag_for_sale(parcels: GeoDataFrame, suburbs: list[str]) -> GeoDataFrame:
    """
    Add a boolean 'for_sale' column by matching parcel addresses to Domain listings.

    Matching is address-string based (best-effort). For production use, spatial
    join on listing coordinates is more reliable.
    """
    listed_addresses: set[str] = set()

    for suburb in suburbs:
        try:
            listings = fetch_listings_for_suburb(suburb)
            for item in listings:
                listing = item.get("listing", {})
                addr = listing.get("propertyDetails", {}).get("displayableAddress", "")
                if addr:
                    listed_addresses.add(addr.upper().strip())
        except Exception as e:
            print(f"Warning: could not fetch listings for {suburb}: {e}")

    result = parcels.copy()
    result["for_sale"] = result["PROP_ADDRESS"].str.upper().str.strip().isin(listed_addresses)
    return result
