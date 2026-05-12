"""Build a self-contained desktop release with PyInstaller."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


APP_NAME = "HypertensionRiskTool"
ROOT = Path(__file__).resolve().parent


def main() -> None:
    if not shutil.which("pyinstaller"):
        print("PyInstaller is not installed.")
        print("Install it for the build machine with: python -m pip install pyinstaller")
        raise SystemExit(1)

    separator = ";" if sys.platform.startswith("win") else ":"
    command = [
        "pyinstaller",
        "--clean",
        "--onefile",
        "--name",
        APP_NAME,
        "--add-data",
        f"{ROOT / 'index.html'}{separator}.",
        "--add-data",
        f"{ROOT / 'index-frontend-poc.html'}{separator}.",
        "--add-data",
        f"{ROOT / 'backend' / 'data' / 'test_patients.csv'}{separator}backend/data",
        "--add-data",
        f"{ROOT / 'backend' / 'models' / 'model-v1.json'}{separator}backend/models",
        str(ROOT / "release_entry.py"),
    ]

    subprocess.run(command, cwd=ROOT, check=True)
    executable = ROOT / "dist" / executable_name()
    print(f"Built release executable: {executable}")


def executable_name() -> str:
    return f"{APP_NAME}.exe" if sys.platform.startswith("win") else APP_NAME


if __name__ == "__main__":
    main()
