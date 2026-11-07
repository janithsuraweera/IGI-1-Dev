"""
Project IGI 1 - Restore Original Files Utility
Restores all modified files from _backup_original
"""

import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "_backup_original"

def restore_files():
    if not BACKUP_DIR.exists():
        print("No backup directory found!")
        return

    count = 0
    for backup_file in BACKUP_DIR.rglob("*"):
        if backup_file.is_file():
            rel_path = backup_file.relative_to(BACKUP_DIR)
            dest = BASE_DIR / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_file, dest)
            print(f"Restored: {rel_path}")
            count += 1

    print(f"\nRestored {count} original files successfully.")

if __name__ == "__main__":
    restore_files()

