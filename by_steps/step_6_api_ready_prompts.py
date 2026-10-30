
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List


INPUT_FILES_PATH = "./outputs/step_4"
SOURCE_PROMPT_FILE = "../prompts/step_3_find_email_info"
WHERE_GENERATE_PARENT = "./steps"
WHERE_GENERATE = os.path.join(WHERE_GENERATE_PARENT, "step_6")

PROMPT_TXT_PATTERN = "prompt_{index}.txt"
PAYLOAD_JSON_PATTERN = "prompt_{index}.payload.json"
MANIFEST_FILE_NAME = "manifest_step_6.json"

CLEAR_OLD_GENERATED_FILES = True
INPUT_ENCODING = "utf-8"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode(INPUT_ENCODING)).hexdigest()


def safe_int_sort_key(name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)", name)
    if match:
        return (int(match.group(1)), name)
    return (10**12, name)


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding=INPUT_ENCODING) as file:
        return json.load(file)


def load_source_prompt(path: str | Path) -> str:
    with open(path, "r", encoding=INPUT_ENCODING) as file:
        return file.read().strip()


def collect_step4_items(input_dir: str | Path) -> List[Dict[str, Any]]:
    datas: List[Dict[str, Any]] = []

    for filename in sorted(os.listdir(input_dir), key=safe_int_sort_key):
        if not filename.endswith(".json"):
            continue

        full_path = os.path.join(input_dir, filename)
        try:
            temp = load_json(full_path)
        except Exception as exc:
            print(f"[WARN] Could not load JSON file: {filename} | {exc}")
            continue

        if isinstance(temp, dict) and isinstance(temp.get("items"), list):
            for item in temp["items"]:
                if isinstance(item, dict):
                    datas.append(item)
        else:
            print(f"[WARN] Missing or invalid 'items' in file: {filename}")

    return datas





def build_user_input_text(data: Dict[str, Any]) -> str:
    return "This is the input:\n" + json.dumps(data, ensure_ascii=False, indent=2)


def build_full_prompt(source_prompt: str, data: Dict[str, Any]) -> str:
    return source_prompt + "\n\n" + build_user_input_text(data)


def build_payload_record(
    idx: int,
    data: Dict[str, Any],
    source_prompt: str,
    source_prompt_file: str | Path,
) -> Dict[str, Any]:
    source_prompt_sha256 = sha256_text(source_prompt)
    user_input_text = build_user_input_text(data)
    full_prompt_text = source_prompt + "\n\n" + user_input_text
    full_prompt_sha256 = sha256_text(full_prompt_text)

    return {
        "prompt_index": idx,
        "source_prompt_file": str(source_prompt_file),
        "source_prompt_sha256": source_prompt_sha256,
        "full_prompt_sha256": full_prompt_sha256,
        "local_output_file_name": f"output_step_6_{idx}.json",
        "developer_prompt": source_prompt,
        "user_input_text": user_input_text,
        "input_object": data,
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Prepare prompt text/payloads offline. Default: no writes.")
    parser.add_argument("--input-dir", required=True, help="Owner-supplied step-4 JSON directory")
    parser.add_argument("--prompt-file", required=True, help="Owner-supplied reviewed prompt text")
    parser.add_argument("--output-dir", required=True, help="New empty local output directory")
    parser.add_argument("--write", action="store_true", help="Create local outputs; never makes network requests")
    parser.add_argument("--dry-run", action="store_true", help="Validate paths only; no data read and no output writes")
    args = parser.parse_args(argv)
    input_dir, prompt_file, output = Path(args.input_dir), Path(args.prompt_file), Path(args.output_dir)
    if not input_dir.is_dir() or not prompt_file.is_file():
        parser.error("Supply an existing input directory and prompt file; private inputs are intentionally excluded")
    if output.exists():
        parser.error("Output directory must be new; this publication copy never clears previous outputs")
    if not args.write or args.dry_run:
        print("Dry run: input paths exist; no prompt/data read, outputs written or network requests made.")
        return 0
    source_prompt = load_source_prompt(prompt_file)
    datas = collect_step4_items(input_dir)
    output.mkdir(parents=True, exist_ok=False)
    manifest = {"prompt_count": len(datas), "items": []}
    for idx, data in enumerate(datas, start=1):
        prompt_name = PROMPT_TXT_PATTERN.format(index=idx)
        payload_name = PAYLOAD_JSON_PATTERN.format(index=idx)
        (output / prompt_name).write_text(build_full_prompt(source_prompt, data), encoding=INPUT_ENCODING)
        payload = build_payload_record(idx, data, source_prompt, prompt_file)
        (output / payload_name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding=INPUT_ENCODING)
        manifest["items"].append({"prompt_index": idx, "prompt_file": prompt_name, "payload_file": payload_name})
    (output / MANIFEST_FILE_NAME).write_text(json.dumps(manifest, indent=2), encoding=INPUT_ENCODING)
    print(f"Prepared {len(datas)} local prompt payloads. Nothing was sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
