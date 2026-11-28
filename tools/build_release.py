"""
Build a Windows release of LittleCat: a single LittleCat.exe (no Python needed).

Usage:
    pip install -r requirements-build.txt
    python tools/build_release.py            # -> dist/LittleCat-dev-windows.exe
    python tools/build_release.py v1.0.0     # -> dist/LittleCat-v1.0.0-windows.exe

The GitHub workflow .github/workflows/release.yml runs this on every v* tag
and attaches the .exe to the GitHub Release.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "dev"
    dist = os.path.join(ROOT, "dist")
    build = os.path.join(ROOT, "build")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "LittleCat",
        "--paths", os.path.join(ROOT, "src"),
        # screen agent game profiles (JSON) travel inside the exe
        "--add-data", f"{os.path.join(ROOT, 'src', 'screen_agent', 'profiles')}{os.pathsep}screen_agent/profiles",
        "--distpath", dist,
        "--workpath", build,
        "--specpath", build,
        # Dev-only modules the game never needs at runtime
        "--exclude-module", "sklearn",
        "--exclude-module", "cv2",
        "--exclude-module", "matplotlib",
        "--exclude-module", "tkinter",
        os.path.join(ROOT, "src", "game.py"),
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)

    exe = os.path.join(dist, "LittleCat.exe")
    target = os.path.join(dist, f"LittleCat-{version}-windows.exe")
    shutil.copyfile(exe, target)
    size_mb = os.path.getsize(target) / 1_048_576
    print(f"\nBuilt {target} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
