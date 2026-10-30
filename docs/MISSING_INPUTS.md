# Owner-supplied inputs

No original private input or configuration is included.

- Clipboard capture needs an interactive local desktop. The SQLite variant also needs an explicit new/private database path whose parent directory already exists.
- Offline conversion needs a reviewed prompt text file, a directory of local step-4 JSON objects with `items` lists, and a new output directory. No contact list, sample person, CV or original prompt is supplied. The synthetic reminder in `templates/prompt.example.txt` must be replaced locally.
- Prompt automation needs a private JSON configuration and prompt files named according to its configured pattern. `templates/automation_config.example` contains synthetic local paths only. Relative paths are interpreted from the current working directory. The retained packages do not implement a universal safety simulator.
- The Selenium wrapper needs an adjacent `by_steps/step_9_browser_config.json`, a compatible browser/driver, and a dedicated profile. `templates/browser_config.example` is a synthetic starting point, not a copied browser configuration.

Existing runtime outputs, schema/manifest files, personal configuration, browser state and accounts were deliberately excluded. Supplying these inputs does not authorize sending any email. The retained desktop automation can press Enter in the active application; the owner must choose and review the target before starting it.
