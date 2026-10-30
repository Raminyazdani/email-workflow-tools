# Email workflow tools — reviewed publication subset

Local Python helpers preserved from the `email_steps` project and the related `copy_append_keyboard` variant. This is a code-only subset: clipboard capture, offline prompt preparation, and desktop/browser automation components. It does **not** include the original SMTP sender, API batch wrapper, personal prompts, contact records, CVs, browser profiles or generated results. No email is sent automatically by the included entry points.

The original MIT license is retained unchanged. See [PROVENANCE.md](PROVENANCE.md) for the relationship between the two copies and the publication changes. The variants remain separate; their histories have not been invented or merged.

## Setup

Use Python 3.10 or newer in a dedicated environment. `requirements.txt` lists imports needed by this subset: `keyboard`, `pyperclip`, `pynput`, `rich` and `selenium`. All five direct dependencies are pinned to the audited resolution. `requirements-lock.txt` records all 25 packages resolved for Windows/Python 3.13; other platforms may need different marker dependencies. Runtime desktop dependencies have not been exercised. Clipboard/hotkey tools need an interactive desktop and platform permissions; the original workflow targets Windows. Selenium also needs a compatible browser/driver; its normal driver management may use the network when you explicitly launch it.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the commands below from this repository root. They describe supported entry points; preparation verified syntax and static import resolution. Isolated tests additionally exercised the safe modes with device/network mocks, not real desktop automation.

## Clipboard tools

```powershell
python main.py --dry-run
python main.py --start
python variants/clipboard/main.py --dry-run
python variants/clipboard/sqlite_history.py --dry-run
python variants/clipboard/sqlite_history.py --start --database .\private\clipboard_store.db
```

The shared monitor and the separate clipboard variant append clipboard changes in memory, replace the clipboard with the accumulated text, clear on **Ctrl+Y**, and exit on **Esc**. The variant is retained as a separate publication copy of its source, not a different algorithm. Captured text is omitted from console logs.

The SQLite variant persists captures only after `--start --database PATH`. Create the private parent directory yourself. **F8** pastes all saved entries into the active application; **F9** deletes its stored entries; **Esc** exits. Keep the database outside the repository or in an ignored private directory. Do not run clipboard capture while copying passwords or other private material.

Default/dry-run modes do not start capture or create a database. They still import the two clipboard libraries, so those dependencies are required. These modes are descriptive, not an end-to-end simulation.

## Offline prompt preparation

```powershell
python by_steps/step_6_api_ready_prompts.py --input-dir .\private\step4 --prompt-file .\private\prompt.txt --output-dir .\private\new-step6 --dry-run
python by_steps/step_6_api_ready_prompts.py --input-dir .\private\step4 --prompt-file .\private\prompt.txt --output-dir .\private\new-step6 --write
```

Supply your own reviewed prompt and a directory of JSON objects containing an `items` list of objects. Those inputs are intentionally absent. A synthetic prompt reminder is in `templates/prompt.example.txt`; it is not the original outreach prompt. Dry-run checks that paths exist and that the output path is new; it does not read or validate input contents. `--write` reads the local inputs and creates prompt text, payload JSON and a small manifest in a **new** output directory. It makes no API request and sends no message. Existing outputs are never cleared by this entry point. Generated files contain the supplied data and must stay private.

## Desktop prompt automation and browser helper

```powershell
python by_steps/step_8_parse_prompt_find_data.py --dry-run
python by_steps/step_8_parse_prompt_find_data.py --start --config .\private\automation.config.json
python by_steps/step_9_browser.py --dry-run
python by_steps/step_9_browser.py --start
```

Copy `templates/automation_config.example` to your private configuration path and review every setting. Paths are resolved relative to the working directory. Provide your own prompt text files, such as `prompt_1.txt`, in the configured private prompt directory. The wrapper loads no configuration and registers no hotkeys until `--start`.

After startup, the default **Ctrl+Alt+Shift+F5** hotkey starts the actual workflow; **F6** reloads pending files, **F8** terminates the process, and **F10** records mouse positions (all with the same Ctrl+Alt+Shift modifiers). The retained automation can focus controls, paste text, press Enter, duplicate/close tabs, capture URLs, and write state/output files. Verify focus and shortcuts in an isolated test application before supplying private prompts. This is real desktop automation, not a dry-run backend. It can submit text to the active application when started; no SMTP transport is included.

For the browser helper, copy `templates/browser_config.example` to the ignored `by_steps/step_9_browser_config.json`. This filename is required by the existing `browser_core` interface. The template uses `about:blank` and a separate private profile. Launching it creates browser/profile/download directories. The wrapper returns after Enter and leaves browser-window management to you. Do not point it at an existing personal browser profile.

## Scope and validation

Private inputs, runtime JSON/JSONL, databases, clipboard stores, logs, browser profiles, outputs and original schema/manifest files were not copied. The original environment freeze was replaced with minimal imports. The original `.gitignore` contained private mail configuration; this copy has a newly written ignore file with no inherited content. Ignore rules do not protect data that has already been tracked.

Large send/API scripts, early ad hoc file-mutating pipeline stages, personal email-generation prompts and unrelated scraping macros remain excluded and require a separate review. This subset does not recreate the complete historic email workflow. Syntax compilation, AST parsing, static local-import resolution and a pinned Gitleaks scan were performed during preparation. Four isolated tests exercise five safe-mode entry points and offline conversion with fictional records and temporary directories. No real clipboard, browser, mailbox or network API was used. The resolved dependency audit found no known vulnerabilities at audit time. Full interactive runtime behavior and dependency compatibility remain unverified.

## Isolated validation

Run `python -I -S -B -m unittest discover -s tests`. The tests replace clipboard/keyboard modules with failing mocks, block database/network access for safe modes, validate offline conversion using fictional records, and verify existing outputs remain intact. They do not exercise real desktop automation.
