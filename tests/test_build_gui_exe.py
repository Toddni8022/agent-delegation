"""Tests for Windows GUI build command helper."""

from pathlib import Path

from examples.build_gui_exe import build_pyinstaller_command


def test_build_command_defaults():
    """Default build command should include onefile + windowed flags."""
    cmd = build_pyinstaller_command(
        script_path=Path("examples/fact_check_gui.py"),
        app_name="TrumpFactCheckerGUI",
    )
    assert cmd[0] == "pyinstaller"
    assert "--onefile" in cmd
    assert "--windowed" in cmd
    assert "--name" in cmd
    assert "TrumpFactCheckerGUI" in cmd


def test_build_command_with_icon():
    """Icon option should be appended when provided."""
    cmd = build_pyinstaller_command(
        script_path=Path("examples/fact_check_gui.py"),
        app_name="MyApp",
        icon_path=Path("icon.ico"),
    )
    assert "--icon" in cmd
    assert "icon.ico" in cmd
