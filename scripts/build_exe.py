import os
import subprocess
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    os.chdir(root)
    
    # We need to make sure the locales folder is included in the build
    # pyinstaller format: --add-data "src/ufc/locales;ufc/locales" (on Windows, semicolons are used)
    # Actually, a more robust way is using os.pathsep
    sep = os.pathsep
    
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--windowed",
        "--name", "UniversalFileConverter",
        "--add-data", f"src/ufc/locales{sep}ufc/locales",
        "src/ufc/app.py"
    ]
    
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("Build complete. Check the 'dist' folder.")

if __name__ == "__main__":
    main()
