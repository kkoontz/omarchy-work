# Omarchy work map

Unofficial record of **merged** pull requests on [`basecamp/omarchy`](https://github.com/basecamp/omarchy).

Not a leaderboard. Not Omacom. Not a grant formula. A picture of where labor landed, so the work is visible. Whether that is useful is for other people to decide.

The [Omacom Foundation](https://omarchy.org/news/2026/08/omacom-foundation-launches-with-8-million) funds infrastructure and the open-source projects Omarchy depends on. This map only shows merges **inside** the distro repo.

## Run locally

```bash
python3 scripts/test_areas.py
GITHUB_TOKEN=$(gh auth token) python3 scripts/collect.py
python3 scripts/build.py
python3 -m http.server -d site 8000
```

Open http://127.0.0.1:8000

## What we count

Merged PRs, attributed to the GitHub login on the PR. File paths bucket the PR into areas (shell, commands, agent skill, …). See `site/methodology.html` after a build.

## Hosting

GitHub Pages, rebuilt nightly by Actions.
