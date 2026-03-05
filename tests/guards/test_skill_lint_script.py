from pathlib import Path
import subprocess


def test_skill_lint_script_runs_cleanly() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["python3", "scripts/lint_skills.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "errors/warnings/info: 0/0/0" in result.stdout
