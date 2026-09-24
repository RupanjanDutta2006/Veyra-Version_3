"""Feature flag governance configuration for Veyra Round 2.

Ensures experimental modules and uncertified specialists cannot enter the production path.
"""
import os
from typing import Dict

# Default feature flags - experimental specialists are disabled by default in production
DEFAULT_FEATURE_FLAGS: Dict[str, bool] = {
    "ENABLE_PRECIPITATION_SPECIALIST": False,
    "ENABLE_CYCLONE_SPECIALIST": False,
    "ENABLE_MONSOON_SPECIALIST": False,
    "ENABLE_WESTERN_DISTURBANCE_SPECIALIST": False,
    "ENABLE_HEATWAVE_SPECIALIST": False,
    "ENABLE_SPATIAL_ENGINE": False,
    "ENABLE_COMPOUND_HAZARD": False,
    "ENABLE_COMMON_MODE": False,
    "ENABLE_CROSS_SYSTEM": False,
    "ENABLE_EXPERIMENTAL_SPECIALISTS": False,
}

def is_feature_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled via environment variable or default.
    
    Default is strictly False for all experimental specialists.
    """
    env_val = os.getenv(flag_name)
    if env_val is not None:
        return env_val.strip().lower() in ("true", "1", "yes", "on")
    
    # Check parent master switch if applicable
    if flag_name != "ENABLE_EXPERIMENTAL_SPECIALISTS":
        master_val = os.getenv("ENABLE_EXPERIMENTAL_SPECIALISTS")
        if master_val is not None and master_val.strip().lower() in ("true", "1", "yes", "on"):
            return True
            
    return DEFAULT_FEATURE_FLAGS.get(flag_name, False)

def get_all_flags() -> Dict[str, bool]:
    """Return current status of all feature flags."""
    return {flag: is_feature_enabled(flag) for flag in DEFAULT_FEATURE_FLAGS}
