from datetime import date, datetime
from functools import lru_cache
from urllib.parse import quote
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

WIKIPEDIA_FEED = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month}/{day}"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {
    "User-Agent": "ChronoScope/1.0 (educational history explorer; contact: add-your-email@example.com)"
}
TIMEOUT = 18


def get_json(url, params=None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def clean_event(item, category="events"):
    pages = item.get("pages") or []
    page = pages[0] if pages else {}
    title = page.get("normalizedtitle") or page.get("title") or ""
    return {
        "year": item.get("year"),
        "text": item.get("text", ""),
        "category": category,
        "title": title,
        "url": page.get("content_urls", {}).get("desktop", {}).get("page")
                or (f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}" if title else ""),
        "extract": page.get("extract", ""),
        "thumbnail": page.get("thumbnail", {}).get("source"),
    }


def fetch_events(month, day):
    # The Wikimedia On-this-day feed is indexed by month/day, not by year.
    payload = get_json(WIKIPEDIA_FEED.format(month=f"{month:02d}", day=f"{day:02d}"))
    results = []
    for category in ("events", "births", "deaths", "holidays"):
        for item in payload.get(category, []):
            results.append(clean_event(item, category))
    results.sort(key=lambda event: (event["year"] is None, -(event["year"] or 0)))
    return results


def commons_images(query, limit=3):
    """Discover reusable image files through Wikimedia Commons' public API."""
    if not query:
        return []
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f'{query} filetype:bitmap',
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 1200,
        "format": "json",
        "origin": "*",
    }
    data = get_json(COMMONS_API, params)
    pages = (data.get("query") or {}).get("pages") or {}
    images = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        images.append({
            "title": page.get("title", "").replace("File:", ""),
            "image": info.get("thumburl") or info.get("url"),
            "page": info.get("descriptionurl") or "https://commons.wikimedia.org/",
            "artist": meta.get("Artist", {}).get("value", "Unknown"),
            "license": meta.get("LicenseShortName", {}).get("value", "See source page"),
        })
    return images


def make_gallery(events):
    gallery, seen = [], set()

    # Prefer event-linked Wikipedia thumbnails when available.
    for event in events:
        src = event.get("thumbnail")
        if src and src not in seen:
            seen.add(src)
            gallery.append({
                "title": event.get("title") or "Historical photograph",
                "image": src,
                "page": event.get("url") or "https://en.wikipedia.org/",
                "artist": "See source article",
                "license": "Check source article",
            })
        if len(gallery) == 3:
            return gallery

    # If the feed has few thumbnails, search Commons using the most relevant event titles.
    for event in events:
        query = event.get("title") or event.get("text", "")[:90]
        try:
            for image in commons_images(query, limit=2):
                if image["image"] and image["image"] not in seen:
                    seen.add(image["image"])
                    gallery.append(image)
                if len(gallery) == 3:
                    return gallery
        except requests.RequestException:
            continue
    return gallery


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/day")
def day_data():
    raw_date = request.args.get("date")
    try:
        selected = date.fromisoformat(raw_date) if raw_date else date.today()
    except ValueError:
        return jsonify({"error": "Please provide a valid date in YYYY-MM-DD format."}), 400

    try:
        events = fetch_events(selected.month, selected.day)
        gallery = make_gallery(events)
        return jsonify({
            "date": selected.isoformat(),
            "display_date": selected.strftime("%A, %B %d, %Y"),
            "events": events[:30],
            "gallery": gallery,
            "source": "Wikipedia On-this-day feed and Wikimedia Commons",
            "note": "Historical entries are indexed by month and day; changing the selected year does not change the historical event list.",
        })
    except requests.Timeout:
        return jsonify({"error": "The history service took too long to respond. Please try again."}), 504
    except requests.RequestException as exc:
        app.logger.warning("Upstream Wikimedia request failed: %s", exc)
        return jsonify({"error": "Could not reach Wikimedia right now. Please try again in a moment."}), 502


if __name__ == "__main__":
    app.run(debug=True, port=5000)
