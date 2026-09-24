"""Region-Based Unit Management Service for Veyra (SIH26079 §12, §15, A7).

Supports:
- India Core Meteorological Zones (IN_NORTH, IN_SOUTH, IN_EAST, IN_WEST, IN_CENTRAL, COASTAL, HIMALAYAN).
- State/Administrative Regions (DELHI_NCR, MAHARASHTRA, WEST_BENGAL, etc.).
- Bounded Grid Patches (0.25° x 0.25° / 0.5° x 0.5° uniform tiles) for areal risk evaluation.
"""
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RegionBounds:
    """Geographic bounding box coordinates (WGS84)."""
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    def contains(self, lat: float, lon: float) -> bool:
        return self.min_lat <= lat <= self.max_lat and self.min_lon <= lon <= self.max_lon

    def to_dict(self) -> Dict[str, float]:
        return {
            "min_latitude": round(self.min_lat, 4),
            "max_latitude": round(self.max_lat, 4),
            "min_longitude": round(self.min_lon, 4),
            "max_longitude": round(self.max_lon, 4),
        }


@dataclass
class GridPatch:
    """A single spatial grid patch tile."""
    patch_id: str
    center_latitude: float
    center_longitude: float
    bounds: RegionBounds
    area_sq_km: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "center_latitude": round(self.center_latitude, 4),
            "center_longitude": round(self.center_longitude, 4),
            "bounds": self.bounds.to_dict(),
            "area_sq_km": round(self.area_sq_km, 2),
        }


@dataclass
class RegionDefinition:
    """Authoritative region definition with bounding box and representative stations."""
    region_id: str
    name: str
    region_type: str  # "METEOROLOGICAL_ZONE", "ADMINISTRATIVE", "BASIN"
    bounds: RegionBounds
    centroid_lat: float
    centroid_lon: float
    representative_stations: List[str] = field(default_factory=list)
    climate_classification: str = "Tropical / Subtropical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "region_id": self.region_id,
            "name": self.name,
            "region_type": self.region_type,
            "bounds": self.bounds.to_dict(),
            "centroid": {
                "latitude": round(self.centroid_lat, 4),
                "longitude": round(self.centroid_lon, 4),
            },
            "representative_stations": self.representative_stations,
            "climate_classification": self.climate_classification,
        }


# Authoritative India Meteorological and Administrative Zones (§12, A7)
INDIA_REGIONS: Dict[str, RegionDefinition] = {
    "IN_NORTH": RegionDefinition(
        region_id="IN_NORTH",
        name="Northern Plains & Sub-Himalaya",
        region_type="METEOROLOGICAL_ZONE",
        bounds=RegionBounds(min_lat=24.0, max_lat=32.5, min_lon=73.0, max_lon=84.0),
        centroid_lat=28.5,
        centroid_lon=77.5,
        representative_stations=["Delhi", "Chandigarh", "Lucknow", "Jaipur"],
        climate_classification="Subtropical continental with extreme pre-monsoon heat and winter fog",
    ),
    "IN_SOUTH": RegionDefinition(
        region_id="IN_SOUTH",
        name="Southern Peninsular India",
        region_type="METEOROLOGICAL_ZONE",
        bounds=RegionBounds(min_lat=8.0, max_lat=18.0, min_lon=74.0, max_lon=85.0),
        centroid_lat=13.0,
        centroid_lon=78.5,
        representative_stations=["Bengaluru", "Chennai", "Hyderabad", "Kochi"],
        climate_classification="Tropical maritime to semi-arid Deccan plateau",
    ),
    "IN_EAST": RegionDefinition(
        region_id="IN_EAST",
        name="Eastern & Gangetic Delta",
        region_type="METEOROLOGICAL_ZONE",
        bounds=RegionBounds(min_lat=20.0, max_lat=27.5, min_lon=83.0, max_lon=90.0),
        centroid_lat=23.5,
        centroid_lon=87.0,
        representative_stations=["Kolkata", "Patna", "Bhubaneswar", "Ranchi"],
        climate_classification="Humid subtropical / tropical wet-and-dry with pre-monsoon squalls (Kalbaishakhi)",
    ),
    "IN_WEST": RegionDefinition(
        region_id="IN_WEST",
        name="Western India & Arid Zone",
        region_type="METEOROLOGICAL_ZONE",
        bounds=RegionBounds(min_lat=18.0, max_lat=27.0, min_lon=68.5, max_lon=77.0),
        centroid_lat=22.5,
        centroid_lon=72.5,
        representative_stations=["Mumbai", "Ahmedabad", "Pune", "Jodhpur"],
        climate_classification="Arid Thar to coastal tropical monsoon",
    ),
    "IN_CENTRAL": RegionDefinition(
        region_id="IN_CENTRAL",
        name="Central Plateau & Narmada Basin",
        region_type="METEOROLOGICAL_ZONE",
        bounds=RegionBounds(min_lat=18.0, max_lat=25.0, min_lon=74.5, max_lon=84.0),
        centroid_lat=22.0,
        centroid_lon=78.5,
        representative_stations=["Bhopal", "Nagpur", "Raipur", "Indore"],
        climate_classification="Tropical wet-and-dry with intense monsoon depression tracks",
    ),
    "COASTAL": RegionDefinition(
        region_id="COASTAL",
        name="Maritime Coastline & Littoral Zone",
        region_type="METEOROLOGICAL_ZONE",
        bounds=RegionBounds(min_lat=8.0, max_lat=22.0, min_lon=72.0, max_lon=89.0),
        centroid_lat=15.0,
        centroid_lon=80.0,
        representative_stations=["Mumbai", "Chennai", "Kochi", "Visakhapatnam", "Kolkata"],
        climate_classification="Maritime boundary layer with land-sea breeze circulations",
    ),
    "HIMALAYAN": RegionDefinition(
        region_id="HIMALAYAN",
        name="Western & Central Himalaya",
        region_type="METEOROLOGICAL_ZONE",
        bounds=RegionBounds(min_lat=30.0, max_lat=37.0, min_lon=74.0, max_lon=82.0),
        centroid_lat=33.0,
        centroid_lon=77.0,
        representative_stations=["Srinagar", "Shimla", "Dehradun", "Leh"],
        climate_classification="Alpine / Montane with complex orographic precipitation",
    ),
    # Key Administrative Regions
    "DELHI_NCR": RegionDefinition(
        region_id="DELHI_NCR",
        name="National Capital Region",
        region_type="ADMINISTRATIVE",
        bounds=RegionBounds(min_lat=28.2, max_lat=28.9, min_lon=76.8, max_lon=77.6),
        centroid_lat=28.6139,
        centroid_lon=77.2090,
        representative_stations=["Delhi", "Gurugram", "Noida"],
        climate_classification="Semi-arid subtropical urban heat island",
    ),
    "MAHARASHTRA": RegionDefinition(
        region_id="MAHARASHTRA",
        name="Maharashtra State",
        region_type="ADMINISTRATIVE",
        bounds=RegionBounds(min_lat=15.6, max_lat=22.0, min_lon=72.6, max_lon=80.9),
        centroid_lat=19.7515,
        centroid_lon=75.7139,
        representative_stations=["Mumbai", "Pune", "Nagpur"],
        climate_classification="Coastal monsoon to rain-shadow interior",
    ),
}


class RegionService:
    """Service providing query and tiling operations across spatial units."""

    def __init__(self, regions: Optional[Dict[str, RegionDefinition]] = None):
        self._regions = regions or INDIA_REGIONS

    def list_regions(self, region_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all supported regions, optionally filtered by region_type."""
        out = []
        for r in self._regions.values():
            if region_type is None or r.region_type.upper() == region_type.upper():
                out.append(r.to_dict())
        return out

    def get_region(self, region_id: str) -> Optional[RegionDefinition]:
        """Retrieve region definition by ID (case-insensitive)."""
        clean_id = region_id.strip().upper()
        return self._regions.get(clean_id)

    def find_region_by_coordinates(self, latitude: float, longitude: float) -> Optional[RegionDefinition]:
        """Identify which primary meteorological zone contains the given coordinate pair."""
        # Prefer specific zones first
        for key in ["DELHI_NCR", "IN_NORTH", "IN_SOUTH", "IN_EAST", "IN_WEST", "IN_CENTRAL", "HIMALAYAN"]:
            r = self._regions.get(key)
            if r and r.bounds.contains(latitude, longitude):
                return r
        return None

    def generate_grid_patches(
        self,
        region_id: str,
        resolution_deg: float = 0.5,
    ) -> List[GridPatch]:
        """Partition a region bounding box into a regular grid of spatial patches."""
        reg = self.get_region(region_id)
        if not reg:
            return []

        patches: List[GridPatch] = []
        bounds = reg.bounds

        lat = bounds.min_lat
        while lat < bounds.max_lat:
            lon = bounds.min_lon
            while lon < bounds.max_lon:
                patch_max_lat = min(bounds.max_lat, lat + resolution_deg)
                patch_max_lon = min(bounds.max_lon, lon + resolution_deg)
                center_lat = (lat + patch_max_lat) / 2.0
                center_lon = (lon + patch_max_lon) / 2.0

                patch_id = f"{region_id}_{center_lat:.2f}N_{center_lon:.2f}E"
                # Approximate area: 1 deg lat ~ 111 km, 1 deg lon ~ 111 * cos(lat) km
                lat_km = (patch_max_lat - lat) * 111.0
                lon_km = (patch_max_lon - lon) * 111.0 * math.cos(math.radians(center_lat))
                area_sq_km = abs(lat_km * lon_km)

                patches.append(
                    GridPatch(
                        patch_id=patch_id,
                        center_latitude=center_lat,
                        center_longitude=center_lon,
                        bounds=RegionBounds(
                            min_lat=lat,
                            max_lat=patch_max_lat,
                            min_lon=lon,
                            max_lon=patch_max_lon,
                        ),
                        area_sq_km=area_sq_km,
                    )
                )
                lon += resolution_deg
            lat += resolution_deg

        return patches
