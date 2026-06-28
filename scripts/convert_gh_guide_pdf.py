#!/usr/bin/env python3
"""تحويل دليل GitHub + VPS من HTML إلى PDF"""
import asyncio
from playwright.async_api import async_playwright

HTML_PATH = "/home/z/my-project/download/github-vps-guide/index.html"
PDF_PATH = "/home/z/my-project/download/github-vps-guide/GitHub-VPS-Guide-Arabic.pdf"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(f"file://{HTML_PATH}", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        await page.pdf(
            path=PDF_PATH,
            format="A4",
            print_background=True,
            margin={"top": "15mm", "bottom": "15mm", "left": "10mm", "right": "10mm"},
        )
        await browser.close()
        print(f"✅ PDF saved: {PDF_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
