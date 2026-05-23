# tools/search.py
import requests

API_URL = "https://api.duckduckgo.com/"


def search(query: str) -> str:
    """
    Search financial information via DuckDuckGo.
    Returns top 3 results as formatted string.
    No API key needed.
    """
    if not query or not query.strip():
        return "No query provided."

    try:
        response = requests.get(
            API_URL,
            params={
                "q": query,
                "format": "json",
                "no_redirect": 1,
                "no_html": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = []

        if data.get("AbstractText"):
            results.append(data["AbstractText"])

        for item in data.get("RelatedTopics", []):
            if isinstance(item, dict):
                text = item.get("Text")
                if text:
                    results.append(text)
            if len(results) >= 3:
                break

        if not results:
            return f"No results found for: {query}"

        return "\n\n".join(
            f"{i+1}. {r}" for i, r in enumerate(results[:3])
        )

    except Exception as e:
        print(f"[Search] failed: {e}")
        return "Search unavailable right now."


# ── quick test ──────────────────────────────────────────
if __name__ == "__main__":
    result = search("SIP mutual fund india")
    print(result)