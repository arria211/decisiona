import shutil
from pathlib import Path
from PySide6.QtCore import QObject, QThread, Signal

class CopyWorker(QThread):
    progress = Signal(int, int)  # current, total
    file_copied = Signal(str)    # destination path
    finished = Signal(list)      # list of copied files
    error = Signal(str)

    def __init__(self, file_paths, target_dir, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.target_dir = Path(target_dir)
        self._is_running = True

    def run(self):
        copied = []
        total = len(self.file_paths)
        for i, src in enumerate(self.file_paths):
            if not self._is_running:
                break
            src = Path(src)
            if not self._validate_file(src):
                self.error.emit(f"Invalid file: {src.name}")
                continue
            # Create destination name: original-Copy.ext
            dest_name = src.stem + "-Copy" + src.suffix
            dest = self.target_dir / dest_name
            # If exists, add number
            counter = 1
            while dest.exists():
                dest_name = f"{src.stem}-Copy{counter}{src.suffix}"
                dest = self.target_dir / dest_name
                counter += 1
            try:
                shutil.copy2(src, dest)
                copied.append(str(dest))
                self.file_copied.emit(str(dest))
            except Exception as e:
                self.error.emit(f"Failed to copy {src.name}: {e}")
            self.progress.emit(i + 1, total)
        self.finished.emit(copied)

    def stop(self):
        self._is_running = False
        self.quit()
        self.wait()

    def _validate_file(self, filepath):
        ext = filepath.suffix.lower()
        return ext in ['.xlsx', '.xls', '.xlsm']


class FileManager(QObject):
    progress = Signal(int, int)  # current, total
    finished = Signal(list)      # list of copied files
    error = Signal(str)

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.worker = None

    def copy_files_to_source(self, file_paths):
        """Start copying files in a separate thread."""
        if self.worker is not None and self.worker.isRunning():
            self.error.emit("Copy operation already in progress.")
            return

        target_dir = self.project.folders['source']
        self.worker = CopyWorker(file_paths, target_dir, parent=self)
        self.worker.progress.connect(self.progress)
        self.worker.finished.connect(self.finished)
        self.worker.error.connect(self.error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.start()

    def stop(self):
        """Hentikan worker jika sedang berjalan."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker = None