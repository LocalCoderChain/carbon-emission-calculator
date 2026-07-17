"""
utils/distance.py — Automatic distance calculation
====================================================
Uses OpenRouteService (ORS) — free tier: 2,000 requests/day, no credit card required.

Sign-up: https://openrouteservice.org/dev/#/signup
After signing up, copy your API key into config/settings.py → ORS_API_KEY

Geocoding:  ORS Geocoding Search API  (place name → lat/lon)
Routing:    ORS Directions API        (lat/lon pair → road distance in km)

Both calls use the same API key. No other dependency needed beyond `requests`
(already available in most Python envs; add to requirements.txt if missing).
"""

from __future__ import annotations
import requests

# ── Constants ────────────────────────────────────────────────────────────────
_GEOCODE_URL   = "https://api.openrouteservice.org/geocode/search"
_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv"  # HGV = heavy goods vehicle (trucks)
_TIMEOUT       = 10   # seconds


# ── Public helpers ────────────────────────────────────────────────────────────

def geocode(place: str, api_key: str) -> tuple[float, float] | None:
    """
    Convert a place name / city / address to (longitude, latitude).
    Returns None on failure so callers can fall back gracefully.
    """
    coords, _ = _geocode_detailed(place, api_key)
    return coords


def _geocode_detailed(place: str, api_key: str) -> tuple[tuple[float, float] | None, str | None]:
    """
    Same as geocode(), but also returns a reason string on failure so callers
    can tell "place doesn't exist" apart from a transient API/network problem
    instead of reporting every failure as if the place were unrecognized.
    """
    if not api_key:
        return None, "no_api_key"
    if not place.strip():
        return None, "empty"
    try:
        resp = requests.get(
            _GEOCODE_URL,
            params={"api_key": api_key, "text": place.strip(), "size": 1},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        features = resp.json().get("features", [])
        if not features:
            return None, "not_found"
        coords = features[0]["geometry"]["coordinates"]   # [lon, lat]
        return (float(coords[0]), float(coords[1])), None  # (lon, lat)
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        return None, f"api_error:{status}"
    except requests.exceptions.RequestException:
        return None, "network_error"
    except Exception:
        return None, "unknown_error"


def _geocode_failure_message(place: str, reason: str | None) -> str:
    if reason == "not_found":
        return f"Could not find '{place}' — check spelling or enter distance manually."
    if reason == "timeout":
        return f"Lookup for '{place}' timed out. Please try again."
    if reason and reason.startswith("api_error:"):
        return f"Location service error looking up '{place}' ({reason.split(':', 1)[1]}). Please try again."
    if reason == "network_error":
        return f"Network error looking up '{place}'. Check your connection and try again."
    return f"Could not locate '{place}'. Check spelling or enter distance manually."


def road_distance_km(
    origin: str,
    destination: str,
    api_key: str,
) -> tuple[float | None, str]:
    """
    Calculate road distance in km between two place names.

    Returns
    -------
    (distance_km, message)
        distance_km  — float if successful, None on failure
        message      — human-readable status / error string
    """
    if not api_key:
        return None, "No API key configured. Enter distance manually."

    origin_coords, origin_err = _geocode_detailed(origin, api_key)
    if origin_coords is None:
        return None, _geocode_failure_message(origin, origin_err)

    dest_coords, dest_err = _geocode_detailed(destination, api_key)
    if dest_coords is None:
        return None, _geocode_failure_message(destination, dest_err)

    try:
        resp = requests.post(
            _DIRECTIONS_URL,
            headers={"Authorization": api_key, "Content-Type": "application/json"},
            json={"coordinates": [list(origin_coords), list(dest_coords)]},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data    = resp.json()
        metres  = data["routes"][0]["summary"]["distance"]
        km      = round(metres / 1000, 1)
        return km, f"Route found: {origin} → {destination} = {km:,.0f} km"
    except requests.exceptions.HTTPError as e:
        # ORS returns 404 when no route exists (e.g. island with no roads)
        if e.response is not None and e.response.status_code == 404:
            return None, "No drivable route found between these locations."
        return None, f"Routing API error: {e}"
    except Exception as e:
        return None, f"Distance calculation failed: {e}"


def air_distance_km(origin: str, destination: str, api_key: str) -> tuple[float | None, str]:
    """
    Straight-line (great-circle) distance in km — used as fallback when
    transport type is Air or Sea and road routing doesn't make sense.
    Uses the Haversine formula; no extra API call needed once coords are known.
    """
    import math

    origin_coords, origin_err = _geocode_detailed(origin, api_key)
    if origin_coords is None:
        return None, _geocode_failure_message(origin, origin_err)

    dest_coords, dest_err = _geocode_detailed(destination, api_key)
    if dest_coords is None:
        return None, _geocode_failure_message(destination, dest_err)

    lon1, lat1 = map(math.radians, origin_coords)
    lon2, lat2 = map(math.radians, dest_coords)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    km = round(2 * 6371 * math.asin(math.sqrt(a)), 1)
    return km, f"Straight-line distance: {origin} → {destination} = {km:,.0f} km"


def get_distance(
    origin: str,
    destination: str,
    transport_type: str,
    api_key: str,
) -> tuple[float | None, str]:
    """
    Main entry point. Chooses road or air/sea distance based on transport type.
    Road:   Road, Rail
    Linear: Air, Sea (Ocean)  ← great-circle; road routing is meaningless for these
    """
    road_modes = {"Road", "Rail"}
    if transport_type in road_modes:
        return road_distance_km(origin, destination, api_key)
    else:
        return air_distance_km(origin, destination, api_key)
