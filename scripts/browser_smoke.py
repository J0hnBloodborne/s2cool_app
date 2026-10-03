"""Exercise the demo through a real browser against an already running app."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8050")
    parser.add_argument("--channel", default="chrome")
    args = parser.parse_args()
    destination = Path(__file__).resolve().parents[1] / "build"
    destination.mkdir(exist_ok=True)
    errors, failures, downloads = [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=args.channel, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: failures.append(f"{response.status} {response.url}")
                if response.status >= 500 else None)
        page.goto(args.url, wait_until="networkidle")
        page.screenshot(path=str(destination / "local-dashboard.png"), full_page=True)
        page.locator(".nav-strip").get_by_text("Data Analysis", exact=True).click()
        page.locator("#data-analysis-analyze-btn").click()
        page.get_by_text("Dataset Builder", exact=True).click()
        page.locator("#data-analysis-generate-dataset-btn").click()
        expect(page.locator("#data-analysis-generate-dataset-status")).to_contain_text("Dataset generated", timeout=60000)
        page.locator("#data-analysis-export-analysis-btn").click()
        expect(page.locator("#data-analysis-export-status")).to_contain_text("Dataset Ready", timeout=60000)
        with page.expect_download() as download:
            page.locator("#data-analysis-download-dataset-btn").click()
        downloads.append(download.value.suggested_filename)
        page.locator(".nav-strip").get_by_text("PV Forecasting", exact=True).click()
        page.locator("#pv-xgb-n-estimators").fill("30")
        page.locator("#pv-xgb-n-estimators").press("Tab")
        page.locator("#pv-train-model").click()
        expect(page.locator("#pv-run-status")).to_contain_text("training completed", timeout=60000)
        with page.expect_download() as download:
            page.locator("#pv-save-model-btn").click()
        downloads.append(download.value.suggested_filename)
        page.locator("#pv-predict-forecast").click()
        expect(page.locator("#pv-run-status")).to_contain_text("predicted successfully", timeout=60000)
        page.screenshot(path=str(destination / "local-pv.png"), full_page=True)
        page.locator(".nav-strip").get_by_text("Cooling Demand", exact=True).click()
        page.locator("#cooling-xgb-n-estimators").fill("30")
        page.locator("#cooling-xgb-n-estimators").press("Tab")
        page.locator("#cooling-run-backtest").click()
        expect(page.locator("#cooling-run-status")).to_contain_text("completed successfully", timeout=60000)
        with page.expect_download() as download:
            page.locator("#cooling-download-forecast-btn").click()
        downloads.append(download.value.suggested_filename)
        page.screenshot(path=str(destination / "local-cooling.png"), full_page=True)
        browser.close()
    report = {"status": "passed" if not errors and not failures else "failed",
              "url": args.url, "browser_errors": errors, "server_errors": failures, "downloads": downloads}
    (destination / "browser-smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    assert not errors and not failures, report
    print("PASS browser: dataset, export, PV training, model download, prediction, cooling backtest, CSV downloads")


if __name__ == "__main__":
    main()
