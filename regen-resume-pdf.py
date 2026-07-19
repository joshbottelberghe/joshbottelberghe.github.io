#!/usr/bin/env python3
"""Regenerate resume.pdf from resume.html.

The résumé page renders its content as a light one-page ".sheet" that is meant to
match the downloadable PDF word for word. This script extracts that sheet plus its
inline styles and prints it to a one-page US-Letter PDF via Playwright's Chromium,
so the PDF is always derived from the HTML (single source of truth).

Usage:  python3 regen-resume-pdf.py
Deps:   playwright (already installed system-wide) + its chromium browser.
"""
import re
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
html = (ROOT / "resume.html").read_text()

# Pull the inline <style> block (holds the .sheet rules) and the .sheet element.
style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
sheet = re.search(r'(<div class="sheet">.*?</div>)\s*</main>', html, re.S).group(1)

# Standalone print document: white page, no shadow/radius, sheet padding = page margin.
doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<style>
  @page {{ size: Letter; margin: 0; }}
  html, body {{ margin: 0; padding: 0; background: #fff; }}
  {style}
  .sheet {{ box-shadow: none; border-radius: 0; margin: 0; max-width: none; }}
</style></head><body>{sheet}</body></html>"""

import subprocess, tempfile

OUT = ROOT / "resume.pdf"


def pages_at(page, scale, path):
    """Render at the given scale and return the resulting page count."""
    page.pdf(path=path, format="Letter", print_background=True,
             prefer_css_page_size=True, scale=round(scale, 3))
    info = subprocess.run(["pdfinfo", path], capture_output=True, text=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 816, "height": 1056})
    page.set_content(doc, wait_until="networkidle")

    # Find the LARGEST scale that still fits one page (fills the page, no big white
    # bar, text as large as possible). Page count is monotonic in scale.
    tmp = tempfile.mktemp(suffix=".pdf")
    lo, hi = 0.5, 1.0
    if pages_at(page, hi, tmp) <= 1:
        lo = hi
    else:
        for _ in range(7):
            mid = (lo + hi) / 2
            if pages_at(page, mid, tmp) <= 1:
                lo = mid
            else:
                hi = mid
    scale = round(lo, 3)
    pages_at(page, scale, str(OUT))
    browser.close()

print(f"wrote {OUT}  (scale {scale})")
