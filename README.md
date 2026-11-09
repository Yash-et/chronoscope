# ChronoScope — Discover the Day

A responsive Flask web app that explores historical events associated with any calendar date. It retrieves event summaries from Wikipedia's On-this-day feed and discovers related images through Wikimedia Commons.

## Features

- Detects today's date automatically.
- Explore any date using the date picker.
- Shows historical events, births, deaths and holidays.
- Displays up to three related images when the source data provides them.
- Includes source links and image attribution/license metadata where available.
- Responsive editorial-style layout.

## Requirements

- Python 3.10+
- Internet connection

## Run on Windows (PowerShell)

```powershell
cd path\to\chronoscope
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

You can also double-click `run.bat` to create the virtual environment, install dependencies and launch the app.

## API route

`GET /api/day?date=YYYY-MM-DD`

Example: `http://127.0.0.1:5000/api/day?date=2026-11-08`

## Data and image sourcing

- Historical events: Wikimedia/Wikipedia On-this-day feed.
- Image discovery: Wikimedia Commons MediaWiki API.
- The app prefers article thumbnails included with event records, then searches Commons for additional images.
- Image pages and available author/license metadata are included in the API response. Always retain attribution and verify the specific file's license before reusing images outside this app.

This uses Wikimedia's structured public APIs rather than scraping arbitrary websites' HTML. That is more stable and makes image source/attribution information easier to preserve. Wikimedia's On-this-day feed may change or be retired; keep the data-fetching functions in `app.py` isolated so the source can be replaced later.

## Important note about dates

The On-this-day feed is keyed by month and day. Selecting a different year changes the displayed calendar date, but the feed still returns events historically associated with that month/day; it does not reconstruct what happened only in the selected year.
