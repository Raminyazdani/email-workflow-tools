"""Opt-in browser wrapper using the existing browser_core implementation."""
def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Open a configured browser; no email transport.")
    parser.add_argument("--start", action="store_true", help="Launch Selenium using adjacent private step_9_browser_config.json")
    parser.add_argument("--dry-run", action="store_true", help="Describe only; no browser/config access")
    args = parser.parse_args(argv)
    if not args.start or args.dry_run:
        print("Dry run: --start reads your adjacent step_9_browser_config.json and launches a dedicated browser profile. No browser started.")
        return 0
    from browser_core import PipelineBrowser, load_step_setup
    setup = load_step_setup(__file__)
    browser = PipelineBrowser.from_setup(setup)
    if not setup.browser.start_url:
        browser.open("about:blank")
    input("Browser is running. Press Enter to return; manage its window manually.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
