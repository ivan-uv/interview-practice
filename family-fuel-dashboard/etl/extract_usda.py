"""
Extract nutrient data from the USDA FoodData Central API.

Free tier: 1,000 requests/hour (generous — no real constraint for this project).
Strategy:
  - POST /fdc/v1/foods/search for each ingredient name.
  - Return the top match (Foundation or SR Legacy preferred over Branded).
  - Batch in groups of 20 to be efficient.
"""
import os
import time
import logging

import requests

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
log = logging.getLogger(__name__)

# Prefer Foundation > SR Legacy > Survey > Branded (most authoritative first)
DATA_TYPE_PREFERENCE = ["Foundation", "SR Legacy", "Survey (FNDDS)", "Branded"]


def _get_api_key() -> str:
    key = os.getenv("USDA_KEY", "DEMO_KEY")
    if key == "DEMO_KEY":
        log.warning("Using USDA DEMO_KEY — rate limited. Set USDA_KEY in .env for production use.")
    return key


def _best_match(results: list[dict]) -> dict | None:
    """Return the most authoritative food match from a search result list."""
    for preferred_type in DATA_TYPE_PREFERENCE:
        for food in results:
            if food.get("dataType") == preferred_type:
                return food
    return results[0] if results else None


def fetch_usda_nutrients(ingredient_names: list[str]) -> list[dict]:
    """
    Search USDA FDC for each ingredient name and return the best match.

    Args:
        ingredient_names: List of ingredient name strings to look up.

    Returns:
        List of USDA food dicts (each has fdcId, description, foodNutrients, etc.)
    """
    api_key = _get_api_key()
    results: list[dict] = []

    for name in ingredient_names:
        params = {"api_key": api_key}
        payload = {
            "query": name,
            "pageSize": 5,
            "dataType": DATA_TYPE_PREFERENCE,
        }

        try:
            resp = requests.post(
                f"{BASE_URL}/foods/search",
                params=params,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            foods = data.get("foods", [])

            match = _best_match(foods)
            if match:
                results.append(match)
                log.debug(f"USDA: '{name}' → '{match.get('description')}' (fdcId={match.get('fdcId')})")
            else:
                log.debug(f"USDA: no match found for '{name}'")

            # USDA allows 1,000 req/hr — 0.5s sleep keeps us well under
            time.sleep(0.5)

        except requests.RequestException as exc:
            log.error(f"USDA request failed for '{name}': {exc}")

    log.info(f"USDA: fetched {len(results)} nutrient records for {len(ingredient_names)} ingredients")
    return results
