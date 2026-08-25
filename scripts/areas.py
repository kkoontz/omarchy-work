"""Map changed file paths to work areas on basecamp/omarchy."""

# First matching prefix wins per path. A PR that touches several
# prefixes is counted in each of those areas (once each).
RULES = (
    ("agent-skill", ("default/agents/", "agents/")),
    ("hyprland", ("default/hypr/", "config/hypr/")),
    ("systemd", ("default/systemd/",)),
    ("themes", ("themes/", "default/themed/")),
    ("shell", ("shell/",)),
    ("commands", ("bin/",)),
    ("install", ("install/",)),
    ("migrations", ("migrations/",)),
    ("manual", ("manual/",)),
    ("config", ("config/",)),
    ("tests", ("test/",)),
    ("docs", ("docs/",)),
    ("applications", ("applications/",)),
)

OTHER = "other"

AREA_LABELS = {
    "shell": "Shell",
    "commands": "Commands",
    "agent-skill": "Agent skill",
    "hyprland": "Hyprland",
    "install": "Install",
    "migrations": "Migrations",
    "manual": "Manual",
    "themes": "Themes",
    "systemd": "Systemd",
    "config": "Config",
    "tests": "Tests",
    "docs": "Docs",
    "applications": "Applications",
    "other": "Other",
}

# Homepage order. Starved layers stay visible; do not hide zeros.
AREA_ORDER = (
    "shell",
    "commands",
    "agent-skill",
    "hyprland",
    "install",
    "migrations",
    "manual",
    "themes",
    "systemd",
    "config",
    "tests",
    "docs",
    "applications",
    "other",
)


def area_for_path(path):
    for area, prefixes in RULES:
        for prefix in prefixes:
            if path == prefix.rstrip("/") or path.startswith(prefix):
                return area
    return OTHER


def areas_for_paths(paths):
    found = []
    seen = set()
    for path in paths:
        area = area_for_path(path)
        if area not in seen:
            seen.add(area)
            found.append(area)
    if not found:
        found.append(OTHER)
    return found
