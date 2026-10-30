"""Opt-in wrapper around the preserved desktop prompt automation package."""
from pathlib import Path
def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Desktop prompt automation; sends text to the active application.")
    parser.add_argument("--config", type=Path, help="Owner-created private JSON configuration")
    parser.add_argument("--start", action="store_true", help="Register live desktop hotkeys")
    parser.add_argument("--dry-run", action="store_true", help="Describe only; no config read or UI activity")
    args = parser.parse_args(argv)
    if not args.start or args.dry_run:
        print("Dry run: --start --config PATH registers desktop hotkeys; the start hotkey can paste/send prompts and close browser tabs. No UI activity started.")
        return 0
    if not args.config or not args.config.is_file():
        parser.error("Supply your reviewed --config file; no private configuration is distributed")
    from prompt_automation.runner import run_dashboard_launcher
    run_dashboard_launcher(args.config, strategy_name="capture_url_close")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
