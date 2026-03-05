#!/usr/bin/env python3
"""Compile Python scripts under a skill path and write JSON evidence."""

from __future__ import annotations

import argparse
import json
import py_compile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-path", required=True, help="Path to target skill directory")
    parser.add_argument("--output", required=True, help="Path to JSON output file")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    scripts_dir = skill_path / "scripts"
    py_files = sorted(scripts_dir.glob("*.py")) if scripts_dir.is_dir() else []

    compiled = []
    failed = []
    for py in py_files:
        try:
            py_compile.compile(str(py), doraise=True)
            compiled.append(str(py))
        except Exception as exc:  # noqa: BLE001
            failed.append({"file": str(py), "error": str(exc)})

    payload = {
        "skill_path": str(skill_path),
        "scripts_found": len(py_files),
        "compiled": compiled,
        "failed": failed,
        "status": "pass" if not failed else "fail",
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
