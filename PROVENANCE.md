# Provenance and publication changes

The root code is from `email_steps`; `variants/clipboard` is retained separately from `copy_append_keyboard`. These are local publication copies, not a fabricated merge of Git histories. The original `email_steps` MIT license is preserved unchanged. Identical source files have not been claimed as independently developed implementations.

## Source file evidence

| Family | Original relative path | Publication path | Original SHA-256 |
|---|---|---|---|
| email_steps | `LICENSE` | `LICENSE` | `6b4f80a44024f483d883db14ff71ed247b8628110871b69e6f88805c79e9b1c2` |
| email_steps | `main.py` | `main.py` | `eaa9caf59fad1bea5a0d424766930376ae85d89403d907826c84b0448816018c` |
| clipboard | `main.py` | `variants/clipboard/main.py` | `eaa9caf59fad1bea5a0d424766930376ae85d89403d907826c84b0448816018c` |
| clipboard | `new_man.py` | `variants/clipboard/sqlite_history.py` | `9d75132efc120d269c5c55e69b7173e1bcee5e765665bb9e2eb7afce037a5d52` |
| email_steps | `by_steps/prompt_automation/__init__.py` | `by_steps/prompt_automation/__init__.py` | `1cb69a5067e621a15232e8f781b6bd1c2899bb633ba34f39758c067331262f0e` |
| email_steps | `by_steps/prompt_automation/config.py` | `by_steps/prompt_automation/config.py` | `a1a242c0d8d4736153d4c0368ee90bac487a6fbdeea07cd34de206a72d6ce152` |
| email_steps | `by_steps/prompt_automation/dashboard.py` | `by_steps/prompt_automation/dashboard.py` | `30f31f84a5dc8135fe34aaea1ef1432c119fe65daa696999049126d035ac465c` |
| email_steps | `by_steps/prompt_automation/input_actions.py` | `by_steps/prompt_automation/input_actions.py` | `6bc6c4d3b7f6250abf3adf33784a5d77408dd23d034be44dba685f2bff1dd275` |
| email_steps | `by_steps/prompt_automation/pipeline.py` | `by_steps/prompt_automation/pipeline.py` | `fba7f05ef5c5118aec6b57a2ea7c3c15bc0094acbe835bb450c4a294ef293a44` |
| email_steps | `by_steps/prompt_automation/repository.py` | `by_steps/prompt_automation/repository.py` | `65feb5332a886abf48afd644e3aea3243b59e3a7b8356eebbc3b94bfb3b518f8` |
| email_steps | `by_steps/prompt_automation/runner.py` | `by_steps/prompt_automation/runner.py` | `e3e863a444ae16a3c7a989dd17404dcf9099f6234bc742aed84d460a71b5f6f0` |
| email_steps | `by_steps/prompt_automation/simulator.py` | `by_steps/prompt_automation/simulator.py` | `ff5d5bdf10a85e049c3c5211a68c30e29f607a35452f6b78c1ab2a60ba4ef7c3` |
| email_steps | `by_steps/prompt_automation/state.py` | `by_steps/prompt_automation/state.py` | `51ac6b86e4c3026c100bf1f0e29729df9dc6b3cb0922300d115450825bbff537` |
| email_steps | `by_steps/prompt_automation/timing.py` | `by_steps/prompt_automation/timing.py` | `8460e2bdfefac6040c657cf6c8b65da803f30072479ae13c0083a66afdceea3a` |
| email_steps | `by_steps/browser_core/__init__.py` | `by_steps/browser_core/__init__.py` | `d4022e4c6282e39db82fbcdade576ede3de9093e78cdd4e45d3bbd62a52a8bf0` |
| email_steps | `by_steps/browser_core/config.py` | `by_steps/browser_core/config.py` | `8cf4b3050326f845017a42f775435f8b3d3900dd1d0bd8a42e77ade4f0d1f207` |
| email_steps | `by_steps/browser_core/driver.py` | `by_steps/browser_core/driver.py` | `02be50adc8fde8dc19a7614276f32fa06f76729bc327663ed64a4e1000ef88da` |
| email_steps | `by_steps/browser_core/pipeline.py` | `by_steps/browser_core/pipeline.py` | `2c6b16fe884b7dc447b05c34466ef65e17dd276129373e9f473e1f558a983a1d` |
| email_steps | `by_steps/browser_core/utils.py` | `by_steps/browser_core/utils.py` | `8ed8d97da847e3d03b64116c42cd3112074f7b972573973f343f2872e914d631` |
| email_steps | `by_steps/browser_core/waiters.py` | `by_steps/browser_core/waiters.py` | `d98ac824231711e5e796a9d9870ca22b0f932c1cecb8d5c7ac1c66656bb3eb45` |
| email_steps | `by_steps/step_6_api_ready_prompts.py` | `by_steps/step_6_api_ready_prompts.py` | `cac283f18baaf86a1d017592a541bcd7123667a711ec321b6bf7b33089199ff4` |
| email_steps | `by_steps/step_8_parse_prompt_find_data.py` | `by_steps/step_8_parse_prompt_find_data.py` | `28e94e5768fb7a884f308a9269cdc926a93177eec07450cbc2e53ef56d5e6f32` |
| email_steps | `by_steps/step_9_browser.py` | `by_steps/step_9_browser.py` | `8f26d64912461658eede35e158a341c2a5a873a8ae7601e871f1fb2998ac8c84` |

## Publication-only changes

- `main.py`: Guard startup behind main and explicit --start; default dry-run; omit captured clipboard values from logs.
- `variants/clipboard/main.py`: Guard startup behind main and explicit --start; default dry-run; omit captured clipboard values from logs.
- `variants/clipboard/sqlite_history.py`: Explicit --start and --database; no module-level clipboard/DB access; default dry-run; no content logs; F9 behavior retained and documented.
- `by_steps/step_6_api_ready_prompts.py`: Explicit input/prompt/output CLI, path-only default dry-run, --write opt-in, new output directory only; old cleanup removed; conversion helpers retained.
- `by_steps/step_8_parse_prompt_find_data.py`: Explicit opt-in wrapper; no config reads/UI hooks before --start; preserved package retains real desktop actions.
- `by_steps/step_9_browser.py`: Explicit --start, default dry-run, removed hardcoded remote fallback; adjacent private config still required.

A new minimal dependency file, clean ignore rules, synthetic templates and documentation were added. Original stages were left unchanged. The complete private historical workflow is not reproduced. No original runtime JSON/JSONL, private prompt, contact list, CV, database, browser profile, log, output or schema/manifest was included. The large SMTP/API wrappers and unrelated ad hoc stages remain outside this subset.
