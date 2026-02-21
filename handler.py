"""
SearXNG Search Tool Handler — Search the web for current information via SearXNG.

Returns titles, snippets, URLs, and source engines from SearXNG (privacy-focused metasearch).
Config injected via runner.py; defaults fall back to os.getenv().
"""

import logging
import os
import requests
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def execute(topic: str, params: dict, config: dict = None, telemetry: dict = None) -> dict:
    """
    Execute a web search query via SearXNG.

    Args:
        topic: Conversation topic (passed by framework)
        params: {
            "query": str (required),
            "limit": int (optional, default 5, max 20),
            "categories": str (optional, comma-separated),
            "time_range": str (optional, e.g. "day", "week", "month", "year")
        }
        config: {"SEARXNG_URL"}

    Returns:
        {"results": [{"title", "snippet", "url", "engine"}], "count": int}
    """
    config = config or {}

    searxng_url = config.get("SEARXNG_URL") or os.getenv("SEARXNG_URL", "http://localhost:8080")
    timeout = int(config.get("SEARXNG_TIMEOUT") or os.getenv("SEARXNG_TIMEOUT", "10"))

    query = params.get("query", "").strip()
    limit = params.get("limit", 5)
    limit = max(1, min(20, limit))
    categories = params.get("categories", "").strip()
    time_range = params.get("time_range", "").strip()

    if not query:
        return {"results": [], "count": 0}

    try:
        results = _search_searxng(searxng_url, query, limit, categories, time_range, timeout)
    except Exception as e:
        logger.error(f"[SEARXNG SEARCH] Search failed: {e}")
        return {"results": [], "count": 0, "error": str(e)[:200]}

    formatted = []
    for r in results:
        snippet = r.get("snippet", "")
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."
        formatted.append({
            "title": r.get("title", ""),
            "snippet": snippet,
            "url": r.get("url", ""),
            "engine": r.get("engine", "unknown")
        })

    return {
        "results": formatted,
        "count": len(formatted),
    }


# ── Search backend ────────────────────────────────────────────────

def _search_searxng(searxng_url: str, query: str, limit: int, categories: str, time_range: str, timeout: int) -> List[Dict[str, Any]]:
    """Query SearXNG API and return deduplicated results."""
    results = []
    seen_urls = set()

    try:
        # Construct request payload
        data = {
            "q": query,
            "format": "json",
            "pageno": 1,
        }

        if categories:
            data["categories"] = categories
        if time_range:
            data["time_range"] = time_range

        # Make POST request to SearXNG
        response = requests.post(
            f"{searxng_url}/search",
            data=data,
            timeout=timeout
        )
        response.raise_for_status()

        resp_json = response.json()
        search_results = resp_json.get("results", [])

        # Deduplicate by URL and collect results
        for item in search_results:
            url = item.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": url,
                    "engine": ", ".join(item.get("engines", ["unknown"]))
                })
                if len(results) >= limit:
                    break

    except requests.exceptions.RequestException as e:
        logger.error(f"[SEARXNG] Request error: {e}")
        raise

    return results
