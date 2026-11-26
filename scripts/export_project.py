import os
import zipfile

SOURCE_DIR = "/Users/kirtanpatel/JARVIS-REAL"
DEST_ZIP = "/Users/kirtanpatel/Desktop/JARVIS_MAYA_CODEBASE.zip"

EXCLUDE_DIRS = {
    "node_modules", ".next", "__pycache__", ".git", ".venv", 
    ".cache", "dist", "build", ".turbo"
}

EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".DS_Store"}

def make_zip():
    print(f"Creating ZIP archive at {DEST_ZIP}...")
    file_count = 0
    with zipfile.ZipFile(DEST_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(SOURCE_DIR):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.next')]
            
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in EXCLUDE_EXTS or f == ".DS_Store":
                    continue
                
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, SOURCE_DIR)
                zipf.write(full_path, arcname=os.path.join("JARVIS-REAL", rel_path))
                file_count += 1
                
    size_mb = os.path.getsize(DEST_ZIP) / (1024 * 1024)
    print(f"Successfully archived {file_count} files into {DEST_ZIP} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    make_zip()
