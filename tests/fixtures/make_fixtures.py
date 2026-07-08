"""Generate synthetic screenshot fixtures. Run: python tests/fixtures/make_fixtures.py

All fixtures are drawn from scratch — no real accounts, no real screenshots.
FRAMES is the M2 acceptance set: 10 config contexts + 10 normal contexts.
"""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from PIL import Image, ImageDraw, ImageFont

FIXTURE_DIR = Path(__file__).parent

# Strings the M1 acceptance test asserts on. Keep in sync with test_ocr.py.
STRIPE_KEY_STRINGS = [
    "Webhooks",
    "Endpoint URL",
    "https://api.example.com/hooks/payments",
    "Signing secret",
    "API keys",
    "sk_live_51NxampleKey",
    "Delete endpoint",
]


class Frame(TypedDict):
    name: str
    kind: str  # "config" | "normal"
    app: str
    title: str
    theme: str  # "light" | "dark"
    header: str
    lines: list[str]


FRAMES: list[Frame] = [
    # ---- config contexts (should escalate) ----
    {
        "name": "stripe_settings",
        "kind": "config",
        "app": "Safari",
        "title": "AcmePay — Webhooks · dashboard.acmepay.com",
        "theme": "light",
        "header": "",  # special-cased rich rendering below
        "lines": [],
    },
    {
        "name": "dns_panel",
        "kind": "config",
        "app": "Safari",
        "title": "DNS Management — example.com",
        "theme": "light",
        "header": "DNS Records",
        "lines": [
            "Type    Name    Content                TTL",
            "A       @       203.0.113.7            Auto",
            "CNAME   www     example.com            Auto",
            "MX      @       mail.example.com       10",
            "Add record        Delete record",
        ],
    },
    {
        "name": "env_editor",
        "kind": "config",
        "app": "Code",
        "title": ".env — checkout-service",
        "theme": "dark",
        "header": ".env",
        "lines": [
            "# Production environment",
            "DATABASE_URL=postgres://prod-db.internal:5432/checkout",
            "STRIPE_SECRET_KEY=sk_live_51NxampleKey",
            "REDIS_URL=redis://cache.internal:6379",
            "DEBUG=false",
        ],
    },
    {
        "name": "prod_toggle",
        "kind": "config",
        "app": "Safari",
        "title": "Admin Console — Feature Flags",
        "theme": "light",
        "header": "Feature Flags — production",
        "lines": [
            "maintenance_mode          OFF",
            "new_checkout_flow         ON",
            "legacy_api_enabled        ON",
            "Danger Zone",
            "Disable all payments",
        ],
    },
    {
        "name": "billing_page",
        "kind": "config",
        "app": "Safari",
        "title": "Billing — Acme Cloud",
        "theme": "light",
        "header": "Billing & Subscription",
        "lines": [
            "Current plan: Team ($240/mo)",
            "Payment method: Visa ending 4242",
            "Next invoice: Aug 1, 2026",
            "Cancel subscription",
            "Downgrade plan",
        ],
    },
    {
        "name": "token_revoke",
        "kind": "config",
        "app": "Safari",
        "title": "Personal Access Tokens",
        "theme": "light",
        "header": "Personal access tokens",
        "lines": [
            "ci-deploy-token — last used 2 hours ago",
            "Expires: never",
            "Scopes: repo, workflow, admin:org",
            "Revoke token",
            "Regenerate token",
        ],
    },
    {
        "name": "deploy_yaml",
        "kind": "config",
        "app": "Code",
        "title": "deploy.yaml — checkout-service",
        "theme": "dark",
        "header": "deploy.yaml",
        "lines": [
            "apiVersion: apps/v1",
            "kind: Deployment",
            "spec:",
            "  replicas: 12",
            "  image: registry.acme.io/checkout:v2.4.1",
            "  cluster: prod-us-east",
        ],
    },
    {
        "name": "webhook_repo",
        "kind": "config",
        "app": "Safari",
        "title": "Repository Webhooks — Settings",
        "theme": "light",
        "header": "Webhooks",
        "lines": [
            "Payload URL",
            "http://localhost:8080/hooks",
            "Content type: application/json",
            "Secret: ********",
            "Update webhook      Delete webhook",
        ],
    },
    {
        "name": "db_console",
        "kind": "config",
        "app": "Safari",
        "title": "Database — Production Cluster",
        "theme": "light",
        "header": "Database settings",
        "lines": [
            "Host: prod-db-1.internal",
            "Connection pool: 200",
            "Backups: daily 03:00 UTC",
            "Reset primary credentials",
            "Delete database",
        ],
    },
    {
        "name": "iam_roles",
        "kind": "config",
        "app": "Safari",
        "title": "IAM — Roles & Permissions",
        "theme": "light",
        "header": "IAM Roles",
        "lines": [
            "role/deploy-bot — AdministratorAccess",
            "role/ci-runner — PowerUser",
            "role/readonly-analyst — Viewer",
            "Detach policy",
            "Delete role",
        ],
    },
    # ---- normal contexts (should NOT escalate) ----
    {
        "name": "news_article",
        "kind": "normal",
        "app": "Safari",
        "title": "Morning Herald — Marathon draws big crowd",
        "theme": "light",
        "header": "Local marathon draws its biggest crowd yet",
        "lines": [
            "Over nine thousand runners lined up at dawn on Saturday",
            "for the city's 40th annual marathon, cheered on by",
            "volunteers handing out water along the riverside route.",
            "Organizers said the finish-line festival will return",
            "next year with more food stalls and live music.",
        ],
    },
    {
        "name": "python_editor",
        "kind": "normal",
        "app": "Code",
        "title": "fibonacci.py — algorithms",
        "theme": "dark",
        "header": "fibonacci.py",
        "lines": [
            "def fibonacci(n: int) -> int:",
            '    """Return the nth Fibonacci number."""',
            "    if n < 2:",
            "        return n",
            "    return fibonacci(n - 1) + fibonacci(n - 2)",
        ],
    },
    {
        "name": "search_results",
        "kind": "normal",
        "app": "Safari",
        "title": "best hiking trails near Portland — Search",
        "theme": "light",
        "header": "best hiking trails near Portland",
        "lines": [
            "Top 10 hikes in the Columbia River Gorge",
            "Forest Park loop guide — maps and photos",
            "Angel's Rest: sunrise hike worth the climb",
            "Beginner-friendly waterfalls within an hour",
        ],
    },
    {
        "name": "docs_page",
        "kind": "normal",
        "app": "Safari",
        "title": "Python Tutorial — Lists and Tuples",
        "theme": "light",
        "header": "Lists and Tuples",
        "lines": [
            "Lists are mutable sequences, typically used to store",
            "collections of homogeneous items.",
            ">>> squares = [1, 4, 9, 16, 25]",
            ">>> squares.append(36)",
            "Tuples are immutable and often hold heterogeneous data.",
        ],
    },
    {
        "name": "video_site",
        "kind": "normal",
        "app": "Safari",
        "title": "Woodworking Basics — Episode 12",
        "theme": "light",
        "header": "How to cut a mortise and tenon joint",
        "lines": [
            "1.2M views · 3 weeks ago",
            "In this episode we lay out, cut, and fit a classic",
            "mortise and tenon joint using hand tools only.",
            "Up next: Sharpening chisels the easy way",
        ],
    },
    {
        "name": "forum_thread",
        "kind": "normal",
        "app": "Safari",
        "title": "r/cooking — What went wrong with my sourdough?",
        "theme": "light",
        "header": "What went wrong with my sourdough?",
        "lines": [
            "Posted by u/breadhopeful · 142 comments",
            "My loaf came out dense and gummy in the middle even",
            "though the crust looked perfect. Starter was bubbly.",
            "Top reply: sounds underproofed — try a longer bulk",
            "ferment and check your oven spring.",
        ],
    },
    {
        "name": "spreadsheet",
        "kind": "normal",
        "app": "Numbers",
        "title": "Marathon training plan",
        "theme": "light",
        "header": "Marathon training plan",
        "lines": [
            "Week   Mon    Tue     Wed     Sat",
            "1      Rest   5 km    8 km    12 km",
            "2      Rest   6 km    10 km   14 km",
            "3      Rest   6 km    10 km   16 km",
            "4      Rest   7 km    12 km   18 km",
        ],
    },
    {
        "name": "recipe_blog",
        "kind": "normal",
        "app": "Safari",
        "title": "Weeknight pasta — Smitten Cook",
        "theme": "light",
        "header": "Weeknight pasta with burst tomatoes",
        "lines": [
            "Serves 4 · 25 minutes",
            "Halve two pints of cherry tomatoes and cook in olive",
            "oil until they burst into a jammy sauce.",
            "Toss with rigatoni, basil, and plenty of parmesan.",
        ],
    },
    {
        "name": "terminal_ls",
        "kind": "normal",
        "app": "Terminal",
        "title": "zsh — ~/projects/algorithms",
        "theme": "dark",
        "header": "",
        "lines": [
            "$ ls",
            "fibonacci.py   sorting.py   README.md   tests",
            "$ python fibonacci.py",
            "55",
            "$",
        ],
    },
    {
        "name": "calendar_week",
        "kind": "normal",
        "app": "Calendar",
        "title": "July 2026 — Week view",
        "theme": "light",
        "header": "Week of July 6, 2026",
        "lines": [
            "Mon  9:00   Team standup",
            "Tue  12:00  Lunch with Sam",
            "Wed  16:00  Gym",
            "Thu  15:00  Dentist",
            "Fri  18:30  Movie night",
        ],
    },
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def _mono(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size)


def make_stripe_settings(dest: Path) -> Path:
    """A Stripe-like developers/webhooks settings page (rich M1 fixture)."""
    img = Image.new("RGB", (1200, 800), "#f6f8fa")
    d = ImageDraw.Draw(img)

    # Sidebar
    d.rectangle([0, 0, 240, 800], fill="#0a2540")
    d.text((24, 30), "AcmePay", font=_font(26), fill="white")
    for i, item in enumerate(["Home", "Payments", "Customers", "Developers", "Settings"]):
        d.text((24, 110 + i * 48), item, font=_font(20), fill="#c9d4e0")

    # Header
    d.text((280, 40), "Developers", font=_font(20), fill="#425466")
    d.text((280, 78), "Webhooks", font=_font(34), fill="#1a1f36")

    # Webhook endpoint card
    d.rounded_rectangle([280, 150, 1140, 400], radius=8, fill="white", outline="#e3e8ee")
    d.text((310, 175), "Endpoint URL", font=_font(20), fill="#425466")
    d.text((310, 210), "https://api.example.com/hooks/payments", font=_font(24), fill="#1a1f36")
    d.text((310, 265), "Signing secret", font=_font(20), fill="#425466")
    d.text((310, 300), "whsec_9f8e7d6c5b4a3210fedcba98", font=_font(24), fill="#1a1f36")
    d.rounded_rectangle([310, 340, 520, 382], radius=6, fill="#df1b41")
    d.text((335, 350), "Delete endpoint", font=_font(20), fill="white")

    # API keys card
    d.rounded_rectangle([280, 430, 1140, 640], radius=8, fill="white", outline="#e3e8ee")
    d.text((310, 455), "API keys", font=_font(28), fill="#1a1f36")
    d.text((310, 510), "Secret key", font=_font(20), fill="#425466")
    d.text((310, 545), "sk_live_51NxampleKey", font=_font(24), fill="#1a1f36")
    d.rounded_rectangle([310, 585, 470, 625], radius=6, outline="#635bff", width=2)
    d.text((335, 594), "Roll key", font=_font(20), fill="#635bff")

    img.save(dest)
    return dest


def make_page(frame: Frame, dest: Path) -> Path:
    """Generic page renderer: header + body lines in a light or dark theme."""
    dark = frame["theme"] == "dark"
    bg = "#1e1e1e" if dark else "#f6f8fa"
    fg = "#d4d4d4" if dark else "#1a1f36"
    dim = "#808080" if dark else "#425466"
    img = Image.new("RGB", (1200, 800), bg)
    d = ImageDraw.Draw(img)

    # Title bar
    d.rectangle([0, 0, 1200, 44], fill="#2d2d2d" if dark else "#e3e8ee")
    d.text((20, 10), frame["title"], font=_font(18), fill="#c0c0c0" if dark else "#425466")

    y = 90
    if frame["header"]:
        d.text((60, y), frame["header"], font=_font(32), fill=fg)
        y += 70
    body_font = _mono(22) if dark else _font(24)
    for line in frame["lines"]:
        d.text((60, y), line, font=body_font, fill=fg if not line.startswith("#") else dim)
        y += 46

    img.save(dest)
    return dest


def main() -> None:
    for frame in FRAMES:
        dest = FIXTURE_DIR / f"{frame['name']}.png"
        if frame["name"] == "stripe_settings":
            make_stripe_settings(dest)
        else:
            make_page(frame, dest)
        print(f"wrote {dest.name}")


if __name__ == "__main__":
    main()
