"""Generate synthetic screenshot fixtures. Run: python tests/fixtures/make_fixtures.py

All fixtures are drawn from scratch — no real accounts, no real screenshots.
"""

from __future__ import annotations

from pathlib import Path

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


def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def make_stripe_settings(dest: Path) -> Path:
    """A Stripe-like developers/webhooks settings page."""
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


def main() -> None:
    path = make_stripe_settings(FIXTURE_DIR / "stripe_settings.png")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
