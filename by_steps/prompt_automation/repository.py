from __future__ import annotations

import datetime
import json
import os
import re
import time
from typing import Dict, List, Tuple

from .config import AutomationConfig
from .state import StateManager


class PromptRepository:
    def __init__(self, config: AutomationConfig):
        self.config = config

    def ensure_directories(self) -> None:
        os.makedirs(self.config.paths.prompts_folder_path, exist_ok=True)
        os.makedirs(self.config.paths.output_folder_path, exist_ok=True)

        prompt_url_map_output_path = getattr(
            self.config.paths,
            "prompt_url_map_output_path",
            "",
        )
        if prompt_url_map_output_path:
            parent = os.path.dirname(prompt_url_map_output_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

    def extract_index_from_prompt(self, filename: str):
        match = re.search(self.config.patterns.prompt_file_pattern, filename, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extract_index_from_output(self, filename: str):
        for pattern in self.config.patterns.output_file_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def get_prompt_files(self) -> List[Tuple[int, str]]:
        files = [
            f for f in os.listdir(self.config.paths.prompts_folder_path)
            if f.endswith(".txt")
        ]
        indexed = []
        for filename in files:
            idx = self.extract_index_from_prompt(filename)
            if idx is not None:
                indexed.append((idx, filename))
        indexed.sort(key=lambda x: x[0])
        return indexed

    def get_done_indices(self):
        done = set()
        if not os.path.exists(self.config.paths.output_folder_path):
            return done

        for out_file in os.listdir(self.config.paths.output_folder_path):
            if out_file.endswith(".json"):
                idx = self.extract_index_from_output(out_file)
                if idx is not None:
                    done.add(idx)
        return done

    def get_pending_prompt_files(self) -> List[Tuple[int, str]]:
        prompt_files = self.get_prompt_files()
        done_indices = self.get_done_indices()
        return [(idx, name) for idx, name in prompt_files if idx not in done_indices]

    def get_pending_prompt_names(self) -> List[str]:
        return [name for _, name in self.get_pending_prompt_files()]

    def reload_pending_into_state(self, state_manager: StateManager) -> List[str]:
        pending_names = self.get_pending_prompt_names()
        state_manager.replace_pending_queue(pending_names)
        return pending_names

    def read_prompt_file(self, file_name: str) -> str:
        file_path = os.path.join(self.config.paths.prompts_folder_path, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def disk_counts(self) -> Dict[str, int]:
        prompt_files = self.get_prompt_files()
        done_indices = self.get_done_indices()
        pending = self.get_pending_prompt_files()
        return {
            "total_prompt_files": len(prompt_files),
            "done_outputs": len(done_indices),
            "pending_files": len(pending),
        }

    def record_prompt_url(self, file_name: str, url: str) -> None:
        target_path = self.config.paths.prompt_url_map_output_path
        if not target_path:
            raise RuntimeError("prompt_url_map_output_path is not configured.")

        existing = {}
        if os.path.exists(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    existing = loaded
            except Exception:
                existing = {}

        existing[file_name] = {"url": url ,     "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}

        temp_path = target_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(temp_path, target_path)
