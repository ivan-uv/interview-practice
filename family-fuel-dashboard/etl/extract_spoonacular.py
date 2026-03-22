"""
Extract recipes from the Spoonacular API.

Free tier: 50 points/day (points-based, not a flat request count).
Strategy:
  - Use complexSearch with addRecipeNutrition=true + addRecipeInformation=true
    to get full detail in one call (costs more points but fewer total calls).
  - Fetch 15 recipes per run to stay comfortably within the daily quota.
  - Skip recipe_ids already in DuckDB (cache-aware).
"""
import os
import time
import logging

import requests

BASE_URL = "https://api.spoonacular.com"
log = logging.getLogger(__name__)

# Rotate through search queries to build a varied recipe library over time
SEARCH_QUERIES = [
    {"query": "kid friendly dinner", "maxReadyTime": 45, "diet": ""},
    {"query": "quick family breakfast", "maxReadyTime": 20, "diet": ""},
    {"query": "easy weeknight pasta", "maxReadyTime": 30, "diet": ""},
    {"query": "chicken vegetable", "maxReadyTime": 40, "diet": ""},
    {"query": "healthy lunch", "maxReadyTime": 30, "diet": ""},
    {"query": "vegetarian family dinner", "maxReadyTime": 45, "diet": "vegetarian"},
    {"query": "salmon easy", "maxReadyTime": 30, "diet": ""},
    {"query": "soup stew", "maxReadyTime": 60, "diet": ""},
]


def _get_api_key() -> str:
    key = os.getenv("SPOONACULAR_KEY", "")
    if not key:
        raise EnvironmentError(
            "SPOONACULAR_KEY not set. Sign up at https://spoonacular.com/food-api "
            "and add the key to your .env file."
        )
    return key


def fetch_recipes(
    exclude_ids: set[int] | None = None,
    max_new: int = 15,
) -> list[dict]:
    """
    Fetch up to max_new new recipes from Spoonacular.

    Args:
        exclude_ids: Set of recipe_id integers already stored in DuckDB.
        max_new: Maximum number of new recipes to return.

    Returns:
        List of raw recipe dicts (Spoonacular API format).
    """
    api_key = _get_api_key()
    exclude_ids = exclude_ids or set()
    results: list[dict] = []

    for search in SEARCH_QUERIES:
        if len(results) >= max_new:
            break

        params = {
            "apiKey": api_key,
            "query": search["query"],
            "maxReadyTime": search["maxReadyTime"],
            "number": 10,
            "addRecipeInformation": True,
            "addRecipeNutrition": True,
            "fillIngredients": True,
            "instructionsRequired": True,
        }
        if search.get("diet"):
            params["diet"] = search["diet"]

        try:
            resp = requests.get(
                f"{BASE_URL}/recipes/complexSearch",
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            for recipe in data.get("results", []):
                rid = recipe.get("id")
                if rid and rid not in exclude_ids:
                    results.append(recipe)
                    exclude_ids.add(rid)
                    if len(results) >= max_new:
                        break

            log.debug(f"Spoonacular search '{search['query']}': got {len(data.get('results', []))} results")
            # Be polite — one request per second
            time.sleep(1)

        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 402:
                log.warning("Spoonacular daily quota reached — stopping early")
                break
            log.error(f"Spoonacular HTTP error for query '{search['query']}': {exc}")
        except requests.RequestException as exc:
            log.error(f"Spoonacular request failed for query '{search['query']}': {exc}")

    log.info(f"Spoonacular: fetched {len(results)} new recipes")
    return results
