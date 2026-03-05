#!/usr/bin/env python3
"""Lint skill quality and test coverage for this repository."""

from __future__ import annotations

import argparse
import glob
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


REQUIRED_FRONTMATTER_FIELDS = ("name", "description")
RECOMMENDED_SECTIONS = (
    "## Validation",
    "## Output And Evidence",
    "## Prerequisites",
    "## Workflow",
)
TEMPLATED_DESC_SUFFIX = (
    "Use for listing resources, creating or updating configurations, querying status, "
    "and troubleshooting workflows for this product."
)


@dataclass
class SkillIssue:
    path: str
    severity: str
    rule: str
    detail: str


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    block = match.group(1)
    result: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def skill_name_from_test_dir(name: str) -> str:
    return name[:-5] if name.endswith("-test") else name


def collect_issues(max_lines: int) -> tuple[List[SkillIssue], dict[str, object]]:
    issues: List[SkillIssue] = []
    skill_files = sorted(glob.glob("skills/**/SKILL.md", recursive=True))

    skill_names: set[str] = set()
    for p in skill_files:
        path = Path(p)
        skill_names.add(path.parent.name)
        text = path.read_text(encoding="utf-8")

        frontmatter = parse_frontmatter(text)
        if not frontmatter:
            issues.append(SkillIssue(p, "error", "frontmatter.missing", "Missing or invalid YAML frontmatter"))
            continue

        for field in REQUIRED_FRONTMATTER_FIELDS:
            if not frontmatter.get(field):
                issues.append(SkillIssue(p, "error", f"frontmatter.{field}", f"Missing required field: {field}"))

        description = frontmatter.get("description", "")
        if TEMPLATED_DESC_SUFFIX in description:
            issues.append(
                SkillIssue(
                    p,
                    "warn",
                    "description.templated",
                    "Description contains a highly templated suffix; add concrete trigger language.",
                )
            )

        line_count = text.count("\n") + 1
        if line_count > max_lines:
            issues.append(
                SkillIssue(
                    p,
                    "warn",
                    "content.too_long",
                    f"SKILL.md has {line_count} lines (max recommended: {max_lines}).",
                )
            )

        for section in RECOMMENDED_SECTIONS:
            if section not in text:
                issues.append(
                    SkillIssue(
                        p,
                        "info",
                        "section.missing",
                        f"Recommended section missing: {section}",
                    )
                )

    test_files = sorted(glob.glob("tests/**/SKILL.md", recursive=True))
    tested_skills = set()
    for t in test_files:
        tested_skills.add(skill_name_from_test_dir(Path(t).parent.name))

    missing_tests = sorted(skill_names - tested_skills)
    for skill in missing_tests:
        issues.append(
            SkillIssue(
                f"skills/**/{skill}/SKILL.md",
                "warn",
                "tests.missing",
                f"No corresponding tests/**/{skill}-test/SKILL.md found.",
            )
        )

    summary = {
        "total_skills": len(skill_names),
        "total_tests": len(test_files),
        "tested_skills": len(skill_names & tested_skills),
        "coverage_percent": round(100 * len(skill_names & tested_skills) / len(skill_names), 1) if skill_names else 0,
        "issues": len(issues),
        "errors": sum(1 for i in issues if i.severity == "error"),
        "warnings": sum(1 for i in issues if i.severity == "warn"),
        "info": sum(1 for i in issues if i.severity == "info"),
    }
    return issues, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint skills and smoke test coverage.")
    parser.add_argument("--max-lines", type=int, default=500, help="Recommended max lines for each SKILL.md")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--output", type=Path, help="Optional output file path")
    args = parser.parse_args()

    issues, summary = collect_issues(max_lines=args.max_lines)
    payload = {
        "summary": summary,
        "issues": [asdict(i) for i in issues],
    }

    if args.json:
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        lines = [
            "Skill lint summary:",
            f"- total_skills: {summary['total_skills']}",
            f"- total_tests: {summary['total_tests']}",
            f"- tested_skills: {summary['tested_skills']}",
            f"- coverage_percent: {summary['coverage_percent']}",
            f"- errors/warnings/info: {summary['errors']}/{summary['warnings']}/{summary['info']}",
            "",
        ]
        for issue in issues:
            lines.append(f"[{issue.severity}] {issue.rule} {issue.path} :: {issue.detail}")
        rendered = "\n".join(lines)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
