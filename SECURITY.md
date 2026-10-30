# Security and privacy

The repository contains a reviewed code-only subset and fictional templates.
Original contact/CV records, clipboard captures, browser profiles, credentials,
mail settings, runtime JSON/JSONL and generated outputs are excluded.

Safe modes are the default. Actual desktop actions require explicit --start;
review the README before enabling them. Do not capture passwords or private
material. The SQLite variant can clear its own stored entries when F9 is used.

The import used Gitleaks with an external clean configuration, a resolved Python
dependency audit, static import checks and isolated synthetic tests. These checks
are bounded evidence, not a guarantee. Historical omitted scripts remain private
and are not represented as audited or published by this subset.
