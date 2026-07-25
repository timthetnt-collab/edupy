"""Small GitHub Actions coding agent for EduPy.

The agent sends a compact repository snapshot and a task to OpenAI, then writes
full-file replacements returned by the model. It never deletes files.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


ROOT = Path.cwd()
MAX_FILE_BYTES = 20_000
MAX_TOTAL_BYTES = 160_000
ALLOWED_SUFFIXES = {
    ".bat",
    ".cfg",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {
    ".git",
    ".github",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "backups",
    "dist",
    "build",
}
IGNORED_NAMES = {
    ".agent-task.txt",
    "edupy.db",
    "save_backup.json",
    "save_data.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-file", required=True)
    return parser.parse_args()


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in IGNORED_PARTS for part in relative.parts):
        return False
    if path.name in IGNORED_NAMES:
        return False
    return path.suffix.lower() in ALLOWED_SUFFIXES


def collect_context() -> str:
    chunks: list[str] = []
    total = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not should_include(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        encoded_size = len(content.encode("utf-8"))
        if encoded_size > MAX_FILE_BYTES:
            content = content[:MAX_FILE_BYTES] + "\n\n[TRUNCATED]\n"
            encoded_size = len(content.encode("utf-8"))
        if total + encoded_size > MAX_TOTAL_BYTES:
            break
        relative = path.relative_to(ROOT).as_posix()
        chunks.append(f"--- FILE: {relative} ---\n{content}")
        total += encoded_size
    return "\n\n".join(chunks)


def extract_text(response: dict) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    parts: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)


def strip_json_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    return match.group(1) if match else text


def call_openai(task: str, context: str) -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY repository secret.")

    model = os.environ.get("OPENAI_MODEL", "gpt-5")
    payload = {
        "model": model,
        "instructions": (
            "You are a careful coding agent working on a Python education game. "
            "Return only JSON. The JSON shape must be: "
            "{\"summary\":\"short summary\",\"files\":[{\"path\":\"relative/path.py\",\"content\":\"complete file contents\"}]}. "
            "Only include files that need to be created or fully replaced. "
            "Do not delete files. Keep changes small, correct, and consistent with the existing project."
        ),
        "input": f"Task:\n{task}\n\nRepository context:\n{context}",
        "max_output_tokens": 12000,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {error.code}: {details}") from error

    text = extract_text(data)
    if not text.strip():
        raise RuntimeError("OpenAI response did not contain text output.")
    return json.loads(strip_json_fence(text))


def validate_path(path: str) -> Path:
    target = (ROOT / path).resolve()
    root = ROOT.resolve()
    if root != target and root not in target.parents:
        raise ValueError(f"Refusing to write outside repository: {path}")
    return target


def write_files(result: dict) -> None:
    files = result.get("files")
    if not isinstance(files, list):
        raise ValueError("Agent result must contain a files list.")

    for file_change in files:
        path = file_change.get("path")
        content = file_change.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError("Each file change must have string path and content.")
        target = validate_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")

    print(result.get("summary", "Agent changes written."))


def main() -> int:
    args = parse_args()
    task = Path(args.task_file).read_text(encoding="utf-8").strip()
    if not task:
        raise RuntimeError("Agent task is empty.")

    context = collect_context()
    result = call_openai(task, context)
    write_files(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())

