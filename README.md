# Omarchy Quattro Arena

Merged work on [`basecamp/omarchy`](https://github.com/basecamp/omarchy): by area, by login, by what actually landed.

Live: https://kkoontz.github.io/omarchy-work/

Beta season: 2026-08-10 – 2026-12-31 (`data/seasons.json`). Public beta and “shipping this week,” not ship day.

## Run locally

```bash
python3 scripts/test_areas.py
python3 scripts/test_summarize.py
python3 scripts/test_seasons.py
python3 scripts/test_scoring.py
python3 scripts/test_ranks.py
python3 scripts/test_classes.py
GITHUB_TOKEN=$(gh auth token) python3 scripts/collect.py
python3 scripts/build.py
python3 -m http.server -d site 8000
```

Open http://127.0.0.1:8000

## How we count

See the site’s [How we count](https://kkoontz.github.io/omarchy-work/methodology.html) page. Credit is merged PRs. Points use area, size, and a weekly diminishing multiplier (never zero). Beta season (2026-08-10 – 2026-12-31) has its own score with idle decay toward a floor. The home page is the Beta ladder. Lifetime is a second board. Class is on the person page. Category ladders cover class and area this season. GitHub Actions rebuilds nightly.
