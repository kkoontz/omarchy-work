# Omarchy Quattro Arena

Merged work on [`basecamp/omarchy`](https://github.com/basecamp/omarchy): by area, by login, by what actually landed.

Live: https://kkoontz.github.io/omarchy-work/

Beta season: 2026-08-25 – 2026-12-31 (`data/seasons.json`).

## Run locally

```bash
python3 scripts/test_areas.py
python3 scripts/test_summarize.py
GITHUB_TOKEN=$(gh auth token) python3 scripts/collect.py
python3 scripts/build.py
python3 -m http.server -d site 8000
```

Open http://127.0.0.1:8000

## How we count

See the site’s [How we count](https://kkoontz.github.io/omarchy-work/methodology.html) page. Credit is merged PRs. People are ordered by share of a fixed achievement catalog (breadth across the tree), not by raw PR volume. GitHub Actions rebuilds nightly.
