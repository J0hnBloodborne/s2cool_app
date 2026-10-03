"""Exercise the demo through a real browser against an already running app."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8050")
    parser.add_argument("--channel", default="chrome")
    parser.add_argument("--auth-file", type=Path, help="Private JSON file with username and password")
    parser.add_argument("--timeout", type=int, default=60000)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--proxy", help="Optional browser proxy, e.g. socks5://127.0.0.1:1080")
    args = parser.parse_args()
    destination = args.report_dir or Path(__file__).resolve().parents[1] / "build"
    destination.mkdir(parents=True, exist_ok=True)
    errors, failures, downloads = [], [], []
    credentials = json.loads(args.auth_file.read_text(encoding="utf-8")) if args.auth_file else None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=args.channel, headless=True,
                                             proxy={"server": args.proxy} if args.proxy else None)
        context = browser.new_context(viewport={"width": 1440, "height": 1000},
                                      accept_downloads=True, http_credentials=credentials)
        page = context.new_page()
        page.set_default_timeout(args.timeout)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: failures.append(f"{response.status} {response.url}")
                if response.status >= 500 else None)
        page.goto(args.url, wait_until="networkidle")
        print("PASS browser login and dashboard", flush=True)
        page.screenshot(path=str(destination / "local-dashboard.png"), full_page=True)
        page.locator(".nav-strip").get_by_text("Data Analysis", exact=True).click()
        page.locator("#data-analysis-analyze-btn").click()
        expect(page.locator("#data-analysis-existing-controls")).to_be_visible(timeout=args.timeout)
        print("PASS dataset selection", flush=True)
        page.get_by_text("Dataset Builder", exact=True).click()
        page.locator("#data-analysis-generate-dataset-btn").click()
        expect(page.locator("#data-analysis-generate-dataset-status")).to_contain_text("Dataset generated", timeout=args.timeout)
        print("PASS dataset generation", flush=True)
        page.locator("#data-analysis-export-analysis-btn").click()
        expect(page.locator("#data-analysis-export-status")).to_contain_text("Dataset Ready", timeout=args.timeout)
        print("PASS dataset export", flush=True)
        with page.expect_download() as download:
            page.locator("#data-analysis-download-dataset-btn").click()
        downloads.append(download.value.suggested_filename)
        page.locator(".nav-strip").get_by_text("PV Forecasting", exact=True).click()
        page.locator("#pv-xgb-n-estimators").fill("30")
        page.locator("#pv-xgb-n-estimators").press("Tab")
        page.locator("#pv-train-model").click()
        expect(page.locator("#pv-run-status")).to_contain_text("training completed", timeout=args.timeout)
        print("PASS PV training", flush=True)
        with page.expect_download() as download:
            page.locator("#pv-save-model-btn").click()
        downloads.append(download.value.suggested_filename)
        page.locator("#pv-predict-forecast").click()
        expect(page.locator("#pv-run-status")).to_contain_text("predicted successfully", timeout=args.timeout)
        print("PASS PV prediction", flush=True)
        page.screenshot(path=str(destination / "local-pv.png"), full_page=True)
        page.locator(".nav-strip").get_by_text("Cooling Demand", exact=True).click()
        page.locator("#cooling-xgb-n-estimators").fill("30")
        page.locator("#cooling-xgb-n-estimators").press("Tab")
        page.locator("#cooling-run-backtest").click()
        expect(page.locator("#cooling-run-status")).to_contain_text("completed successfully", timeout=args.timeout)
        print("PASS cooling backtest", flush=True)
        with page.expect_download() as download:
            page.locator("#cooling-download-forecast-btn").click()
        downloads.append(download.value.suggested_filename)
        page.screenshot(path=str(destination / "local-cooling.png"), full_page=True)
        browser.close()
    report = {"status": "passed" if not errors and not failures else "failed",
              "url": args.url, "proxy_used": bool(args.proxy), "browser_errors": errors,
              "server_errors": failures, "downloads": downloads}
    (destination / "browser-smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    assert not errors and not failures, report
    print("PASS browser: dataset, export, PV training, model download, prediction, cooling backtest, CSV downloads")


if __name__ == "__main__":
    main()
