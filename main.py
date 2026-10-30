import pyperclip
import time
import threading
import keyboard
from threading import Lock

history = []
lock = Lock()

# Instead of a boolean, store what WE wrote
internal_value = None

def set_clipboard(text: str):
    global internal_value
    internal_value = text
    pyperclip.copy(text)

def history_text() -> str:
    return "\n".join(history) + ("\n" if history else "")

def flush_clipboard():
    with lock:
        history.clear()
        set_clipboard("")
    print("[Flushed] History + clipboard cleared.")

def monitor_clipboard():
    global internal_value
    last_seen = None

    while True:
        try:
            cur = pyperclip.paste()

            if cur == last_seen:
                time.sleep(0.02)
                continue

            # If clipboard now equals exactly what we wrote, ignore it
            if internal_value is not None and cur == internal_value:
                last_seen = cur
                internal_value = None
                time.sleep(0.02)
                continue

            # Stabilize: some apps update clipboard in 1–2 steps
            time.sleep(0.05)
            cur2 = pyperclip.paste()

            item = (cur2 or "").rstrip("\r\n")
            if not item.strip():
                last_seen = cur2
                time.sleep(0.02)
                continue

            with lock:
                # ignore ONLY consecutive duplicates
                if history and item == history[-1]:
                    set_clipboard(history_text())
                    last_seen = internal_value
                    print("[Skipped] Consecutive duplicate; history preserved.")
                    time.sleep(0.02)
                    continue

                history.append(item)
                set_clipboard(history_text())
                last_seen = internal_value

                print(f"[Appended] items={len(history)}")
                    # Clipboard contents are deliberately omitted from console logs.

        except Exception as e:
            print(f"[Monitor Error] {e}")

        time.sleep(0.02)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Clipboard append monitor; no email sending.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--start", action="store_true", help="Start clipboard capture and register hotkeys")
    mode.add_argument("--dry-run", action="store_true", help="Describe behavior without starting capture (default)")
    args = parser.parse_args(argv)
    if not args.start:
        print("Dry run: --start captures clipboard changes in memory; Ctrl+Y clears; Esc exits. No clipboard access started.")
        return 0
    threading.Thread(target=monitor_clipboard, daemon=True).start()

    keyboard.add_hotkey("ctrl+y", flush_clipboard)

    print("📋 Running (auto-append on clipboard change)")
    print("→ Copies are captured automatically")
    print("→ Ctrl+Y: flush")
    print("→ Esc: exit")
    keyboard.wait("esc")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
