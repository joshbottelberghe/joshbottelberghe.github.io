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

PAGE_PX = 11 * 96  # US-Letter height in CSS px at 96dpi

with sync_playwright() as p:
    browser = p.chromium.launch()
    # Measure at true Letter width (8.5in = 816px) so height reflects the print layout.
    page = browser.new_page(viewport={"width": 816, "height": 1056})
    page.set_content(doc, wait_until="networkidle")
    # Scale the whole sheet down just enough to fit one page.
    height = page.evaluate("document.querySelector('.sheet').scrollHeight")
    scale = min(1.0, (PAGE_PX / height) * 0.99)
    page.pdf(path=str(ROOT / "resume.pdf"), format="Letter",
             print_background=True, prefer_css_page_size=True, scale=round(scale, 3))
    browser.close()

print(f"wrote {ROOT / 'resume.pdf'}  (content {height}px, scale {round(scale,3)})")
