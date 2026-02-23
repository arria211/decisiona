import shutil
import time
import json
from pathlib import Path

class UndoManager:
    def __init__(self, project):
        self.project = project
        self.backup_dir = project.folders['backups']
        self.trash_dir = project.folders['trash']
        self.history = []  # list of snapshot timestamps
        self._load_history()

    def _load_history(self):
        """Load existing snapshots from backup directory."""
        if self.backup_dir.exists():
            self.history = sorted([d.name for d in self.backup_dir.iterdir() if d.is_dir()])

    def _get_relative_path(self, absolute_path):
        """Convert absolute path to relative path from project root."""
        try:
            return Path(absolute_path).relative_to(self.project.root_path)
        except ValueError:
            # If file is outside project root (should not happen), return just name
            return Path(absolute_path).name

    def create_snapshot(self, file_paths):
        """
        Create a backup of given files.
        Stores files in a subfolder named with timestamp, preserving relative paths.
        Also saves a manifest.json with original relative paths.
        """
        timestamp = str(int(time.time()))
        snapshot_dir = self.backup_dir / timestamp
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        manifest = []
        for fp in file_paths:
            src = Path(fp)
            if not src.exists():
                continue
            # Compute relative path
            rel_path = self._get_relative_path(src)
            dest = snapshot_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            manifest.append(str(rel_path))

        # Save manifest
        with open(snapshot_dir / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)

        self.history.append(timestamp)
        return timestamp

    def snapshot_source_folder(self):
        """
        Create a snapshot of the entire source_files folder.
        This captures the complete state of all source files before an operation.
        Returns the timestamp of the snapshot.
        """
        source_dir = self.project.folders['source']
        if not source_dir.exists():
            return None
        # Get all files in source_files recursively
        files = [str(p) for p in source_dir.rglob('*') if p.is_file()]
        if not files:
            return None
        return self.create_snapshot(files)

    def restore_snapshot(self, timestamp):
        """Restore files from a snapshot."""
        snapshot_dir = self.backup_dir / timestamp
        if not snapshot_dir.exists():
            return False

        # Load manifest
        manifest_file = snapshot_dir / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
        else:
            # Fallback for old snapshots: assume all files directly in snapshot dir
            manifest = [f.name for f in snapshot_dir.iterdir() if f.is_file() and f.name != "manifest.json"]

        for rel_path in manifest:
            backup_file = snapshot_dir / rel_path
            if not backup_file.exists():
                continue
            original = self.project.root_path / rel_path
            original.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_file, original)

        return True

    def move_to_trash(self, file_path):
        """Move file to trash, preserving relative path structure."""
        src = Path(file_path)
        if not src.exists():
            return False

        rel_path = self._get_relative_path(src)
        dest = self.trash_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Avoid overwrite in trash
        counter = 1
        original_dest = dest
        while dest.exists():
            stem = original_dest.stem
            suffix = original_dest.suffix
            dest = original_dest.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        shutil.move(str(src), str(dest))
        return str(dest)

    def restore_from_trash(self, trash_path):
        """Restore file from trash to original location."""
        trash_file = Path(trash_path)
        if not trash_file.exists():
            return False

        # Compute relative path from trash dir
        try:
            rel_path = trash_file.relative_to(self.trash_dir)
        except ValueError:
            return False

        original = self.project.root_path / rel_path
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(trash_file), str(original))
        return True

    def list_trash(self):
        """Return list of files in trash with their relative paths."""
        if not self.trash_dir.exists():
            return []
        files = []
        for p in self.trash_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(self.trash_dir)
                files.append({
                    'trash_path': str(p),
                    'original_path': str(self.project.root_path / rel)
                })
        return files

    def empty_trash(self):
        """Permanently delete trash contents."""
        shutil.rmtree(self.trash_dir)
        self.trash_dir.mkdir(parents=True, exist_ok=True)