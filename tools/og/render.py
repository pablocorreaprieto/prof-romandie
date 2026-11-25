#!/usr/bin/env python3
"""Render the share images (Open Graph) of the guide, one per language.

    python3 tools/og/render.py

Writes assets/img/og-<lang>.png, 1200 x 630, from content/<lang>/home.yml (h1)
and the "verified" line of build.py, with the site's own font. Needs Playwright
with Chromium (pip install playwright && playwright install chromium).
Run it again after changing a home page title or the verification date.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1].parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402  (reads content/ and the UI strings)
from playwright.sync_api import sync_playwright  # noqa: E402

TEMPLATE = (ROOT / "tools" / "og" / "template.html").resolve().as_uri()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 630})
    for lang in build.LANGS:
        page.goto(TEMPLATE)
        page.evaluate(
            """([h1, verified, lang]) => {
                document.documentElement.lang = lang;
                document.getElementById('h1').textContent = h1;
                document.getElementById('verified').textContent = verified;
            }""",
            [build.SITE[lang]["home"]["h1"], build.UI[lang]["verified"], lang],
        )
        page.evaluate("document.fonts.ready")
        out = ROOT / "assets" / "img" / f"og-{lang}.png"
        page.screenshot(path=str(out))
        print("wrote", out.relative_to(ROOT))
    browser.close()
