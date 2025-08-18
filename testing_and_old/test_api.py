# SITE: https://rapidapi.com/letscrape-6bRBa3QguO5/api/local-business-data

import http.client
import json
from urllib.parse import urlencode

RAPIDAPI_HOST = "local-business-data.p.rapidapi.com"
# Put your real key here or load from env
RAPIDAPI_KEY = "f6399adba0msh224e79049a0e091p12a748jsn1c335c39626e"

# Minimal mapping; add more as you need
CITY_COORDS = {
    "brisbane": (-27.4698, 153.0251),
    "brisbane cbd": (-27.4679, 153.0281),
}

def search_businesses_in_area(business_type: str,
                              area: str = "Brisbane",
                              *,
                              limit: int = 20,
                              language: str = "en",
                              region: str = "au",
                              zoom: int = 13,
                              extract_emails_and_contacts: bool = False,
                              lat: float | None = None,
                              lng: float | None = None) -> dict:
    """
    Query Local Business Data (RapidAPI) 'search-in-area' for a business type within a metro area.

    You can pass a known area name (mapped in CITY_COORDS) OR explicit lat/lng.
    """
    # Resolve coordinates
    if lat is None or lng is None:
        key = area.strip().lower()
        if key not in CITY_COORDS:
            raise ValueError(
                f"Unknown area '{area}'. Provide lat/lng or add it to CITY_COORDS."
            )
        lat, lng = CITY_COORDS[key]

    params = {
        "query": business_type,
        "lat": f"{lat:.6f}",
        "lng": f"{lng:.6f}",
        "zoom": str(zoom),
        "limit": str(limit),
        "language": language,
        "region": region,
        "extract_emails_and_contacts": str(extract_emails_and_contacts).lower(),
    }

    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY,
    }

    conn = http.client.HTTPSConnection(RAPIDAPI_HOST, timeout=30)
    try:
        path = f"/search-in-area?{urlencode(params)}"
        conn.request("GET", path, headers=headers)
        res = conn.getresponse()
        body = res.read()
        if res.status != 200:
            raise RuntimeError(f"HTTP {res.status}: {body.decode('utf-8', 'ignore')}")
        return json.loads(body)
    finally:
        conn.close()

if __name__ == "__main__":
    data = search_businesses_in_area("PC SHOP", "Brisbane", limit=20)
    print(json.dumps(data.get("data", data)[:3], indent=2, ensure_ascii=False))
