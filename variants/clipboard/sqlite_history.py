import pyperclip
import keyboard
import time
import sqlite3

DB = None

last_clip = None
ignore_next = None


def get_conn():
    return sqlite3.connect(DB)


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.commit()


def save_item(text):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO clipboard_items (text, created_at) VALUES (?, ?)",
            (text, time.time())
        )
        conn.commit()


def load_items():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT text FROM clipboard_items ORDER BY id ASC"
        ).fetchall()
    return [row[0] for row in rows]


def load_all():
    return "\n".join(load_items())


def clear_all():
    global last_clip, ignore_next
    with get_conn() as conn:
        conn.execute("DELETE FROM clipboard_items")
        conn.commit()
    last_clip = pyperclip.paste()
    ignore_next = None
    print("[Cleared]")


def paste_all():
    global ignore_next, last_clip

    text = load_all()
    if not text.strip():
        print("[Empty]")
        return

    ignore_next = text
    pyperclip.copy(text)
    last_clip = text
    time.sleep(0.05)
    keyboard.send("ctrl+v")
    print("[Pasted]")



def main(argv=None):
    global DB, last_clip, ignore_next
    import argparse
    parser = argparse.ArgumentParser(description="Local SQLite clipboard history; no email sending.")
    parser.add_argument("--start", action="store_true", help="Begin persistent clipboard capture")
    parser.add_argument("--dry-run", action="store_true", help="Describe behavior without capture (default)")
    parser.add_argument("--database", help="Explicit private local database path; never commit this file")
    args = parser.parse_args(argv)
    if not args.start or args.dry_run:
        print("Dry run: --start --database PATH enables persistent capture; F8 pastes, F9 deletes stored items, Esc exits.")
        return 0
    if not args.database:
        parser.error("--database is required with --start")
    DB = args.database
    last_clip = pyperclip.paste()
    init_db()

    keyboard.add_hotkey("f8", paste_all, suppress=True)
    keyboard.add_hotkey("f9", clear_all, suppress=True)

    print("Running...")
    print("F8 = paste all")
    print("F9 = clear")
    print("Esc = exit")

    while True:
        cur = pyperclip.paste()

        if cur != last_clip:
            if ignore_next is not None and cur == ignore_next:
                ignore_next = None
                last_clip = cur
            else:
                text = (cur or "").rstrip("\r\n")
                if text.strip():
                    save_item(text)
                    print("[Saved] Clipboard item captured; contents omitted.")
                last_clip = cur

        if keyboard.is_pressed("esc"):
            break

        time.sleep(0.2)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
