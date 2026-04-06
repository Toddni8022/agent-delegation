"""Build a Windows executable for the transcript fact-check GUI.

Usage:
    python examples/build_gui_exe.py
    python examples/build_gui_exe.py --name TrumpFactChecker --icon path/to/icon.ico
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def build_pyinstaller_command(
    script_path: Path,
    app_name: str,
    onefile: bool = True,
    windowed: bool = True,
    icon_path: Optional[Path] = None,
    search_path: Optional[Path] = None,
    hidden_imports: Optional[List[str]] = None,
) -> List[str]:
    """Create the pyinstaller command for building the GUI executable."""
    command = ["pyinstaller"]
    if onefile:
        command.append("--onefile")
    if windowed:
        command.append("--windowed")
    if search_path:
        command.extend(["--paths", str(search_path)])
    for module_name in hidden_imports or []:
        command.extend(["--hidden-import", module_name])
    command.extend(["--name", app_name, str(script_path)])
    if icon_path:
        command.extend(["--icon", str(icon_path)])
    return command


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a Windows .exe for examples/fact_check_gui.py."
    )
    parser.add_argument(
        "--name",
        default="TrumpFactCheckerGUI",
        help="Executable name in dist/ (default: TrumpFactCheckerGUI).",
    )
    parser.add_argument(
        "--icon",
        default=None,
        help="Optional .ico file path for the executable icon.",
    )
    parser.add_argument(
        "--no-onefile",
        action="store_true",
        help="Disable onefile packaging (faster build, folder output).",
    )
    args = parser.parse_args()

    if shutil.which("pyinstaller") is None:
        raise SystemExit(
            "PyInstaller is not installed. Run: python -m pip install pyinstaller"
        )

    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "examples" / "fact_check_gui.py"
    if not script_path.exists():
        raise FileNotFoundError(f"GUI script not found: {script_path}")

    icon_path = Path(args.icon).resolve() if args.icon else None
    if icon_path and not icon_path.exists():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")

    command = build_pyinstaller_command(
        script_path=script_path,
        app_name=args.name,
        onefile=not args.no_onefile,
        windowed=True,
        icon_path=icon_path,
        search_path=repo_root,
        hidden_imports=[
            "agent_delegation",
            "agent_delegation.agents",
            "agent_delegation.core",
        ],
    )

    print("Running build command:")
    print(" ".join(command))
    subprocess.run(command, cwd=repo_root, check=True)

    if args.no_onefile:
        output = repo_root / "dist" / args.name
    else:
        output = repo_root / "dist" / f"{args.name}.exe"
    print(f"Build complete. Output should be at: {output}")


if __name__ == "__main__":
    main()
