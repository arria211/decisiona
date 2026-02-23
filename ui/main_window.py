from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QSplitter, QMessageBox, QFileDialog, QApplication,
                               QToolBar)
from PySide6.QtCore import Qt, QTimer
from ui.project_list import ProjectListWidget
from ui.file_list import FileListWidget
from ui.chat_widget import ChatWidget
from ui.preview_widget import PreviewWidget
from project import ProjectManager
from file_manager import FileManager
from profiler import ExcelProfiler, ProfilingWorker
from undo_manager import UndoManager
from ui.confirmation_dialog import ConfirmationDialog
from executor import PandasExecutor
from ui.trash_dialog import TrashDialog
import re

class MainWindow(QMainWindow):
    def __init__(self, activation):
        super().__init__()
        self.activation = activation
        self.project_manager = ProjectManager()
        self.current_project = None
        self.file_manager = None
        self.undo_manager = None
        self.profiler = None
        self.profiling_worker = None
        self.executor = None

        # Timer aktivasi dengan parent (QTimer akan otomatis berhenti saat window ditutup)
        self.activation_timer = QTimer(self)
        self.activation_timer.timeout.connect(self.check_activation_timer)
        self.activation_timer.start(60000)  # cek setiap 60 detik

        self.setWindowTitle("DECISIONA")
        self.setMinimumSize(1280, 720)
        self.setup_ui()
        self.create_toolbar()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Project list
        self.project_list = ProjectListWidget(self.project_manager)
        self.project_list.project_selected.connect(self.on_project_selected)
        self.project_list.project_created.connect(self.on_project_created)
        self.project_list.project_deleted.connect(self.on_project_deleted)
        splitter.addWidget(self.project_list)

        # Right side vertical splitter
        right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Top right: File list + upload
        self.file_list = FileListWidget()
        self.file_list.upload_requested.connect(self.on_upload_files)
        self.file_list.file_selected.connect(self.on_file_selected)
        self.file_list.refresh_requested.connect(self.profile_current_project)
        self.file_list.delete_file_requested.connect(self.on_delete_file)
        self.file_list.processed_file_selected.connect(self.on_processed_file_selected)
        right_splitter.addWidget(self.file_list)

        # Bottom right: Chat and preview
        chat_preview_splitter = QSplitter(Qt.Orientation.Vertical)
        self.chat_widget = ChatWidget()
        self.chat_widget.send_message.connect(self.on_chat_message)
        self.chat_widget.ai_response_ready.connect(self.on_ai_response_ready)
        chat_preview_splitter.addWidget(self.chat_widget)

        self.preview_widget = PreviewWidget()
        chat_preview_splitter.addWidget(self.preview_widget)

        right_splitter.addWidget(chat_preview_splitter)

        splitter.addWidget(right_splitter)
        splitter.setSizes([250, 900])

        main_layout.addWidget(splitter)

        self.create_menus()

    def create_toolbar(self):
        toolbar = QToolBar("Undo & Trash")
        self.addToolBar(toolbar)

        undo_action = toolbar.addAction("↩ Undo")
        undo_action.triggered.connect(self.on_undo)

        trash_action = toolbar.addAction("🗑 Trash")
        trash_action.triggered.connect(self.show_trash_dialog)

    def create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        new_action = file_menu.addAction("New Project")
        new_action.triggered.connect(self.project_list.create_new_project)
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        help_menu = menubar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def show_about(self):
        QMessageBox.about(self, "About DECISIONA", "DECISIONA AI Data Assistant\nVersion 1.0")

    def check_activation_timer(self):
        if not self.activation.is_activated():
            QMessageBox.critical(self, "License Expired", "Your license has expired. Application will close.")
            QApplication.quit()
        # Timer akan terus berjalan karena sudah di-start di __init__

    def on_project_selected(self, project):
        # Hentikan semua thread dari proyek sebelumnya
        self.stop_all_threads()

        self.current_project = project
        # FileManager adalah QObject, beri parent=self agar terikat siklus hidup
        self.file_manager = FileManager(project, parent=self)
        # UndoManager bukan QObject, jadi tidak perlu parent
        self.undo_manager = UndoManager(project)
        self.profiler = ExcelProfiler(project)
        self.file_list.set_project(project)
        self.preview_widget.clear()
        self.chat_widget.clear()
        self.profile_current_project()
        self.load_processed_files()

    def on_project_created(self, project):
        self.on_project_selected(project)

    def on_project_deleted(self, project):
        if self.current_project and self.current_project.id == project.id:
            self.current_project = None
            self.file_manager = None
            self.undo_manager = None
            self.profiler = None
            self.file_list.set_project(None)
            self.preview_widget.clear()
            self.chat_widget.clear()
            self.statusBar().showMessage("Project deleted.", 3000)

    def profile_current_project(self):
        if self.profiler is None:
            self.statusBar().showMessage("No active project.", 3000)
            return
        if self.profiling_worker and self.profiling_worker.isRunning():
            self.profiling_worker.quit()
            self.profiling_worker.wait()
        self.statusBar().showMessage("Profiling data...")
        # ProfilingWorker adalah QThread, beri parent=self
        self.profiling_worker = ProfilingWorker(self.profiler, parent=self)
        self.profiling_worker.finished.connect(self.on_profiling_finished)
        self.profiling_worker.error.connect(self.on_profiling_error)
        self.profiling_worker.finished.connect(self.profiling_worker.deleteLater)
        self.profiling_worker.start()

    def on_profiling_finished(self, profiles):
        self.profiler.profiles = profiles  # Simpan semua profil (source + processed)

        # Pisahkan profil source dan processed berdasarkan lokasi file
        source_profiles = {}
        processed_profiles = {}
        for fname, prof in profiles.items():
            # Cek apakah file ada di folder source
            source_path = self.current_project.folders['source'] / fname
            if source_path.exists():
                source_profiles[fname] = prof
            else:
                # Cek di folder processed
                processed_path = self.current_project.folders['processed'] / fname
                if processed_path.exists():
                    processed_profiles[fname] = prof
                else:
                    # Jika tidak ditemukan di kedua folder (mungkin file sudah dihapus), abaikan
                    pass

        # Perbarui UI
        self.file_list.update_files(source_profiles)  # Daftar source
        self.file_list.update_processed_files(list(processed_profiles.keys()))  # Daftar processed

        # Berikan konteks ke AI (semua file)
        context = self.profiler.get_context_for_ai()
        self.chat_widget.set_context(context)
        self.statusBar().showMessage("Profiling completed.", 3000)

        # Putuskan sinyal sebelum deleteLater
        try:
            self.profiling_worker.finished.disconnect()
            self.profiling_worker.error.disconnect()
        except TypeError:
            pass
        self.profiling_worker.deleteLater()
        self.profiling_worker = None

    def on_profiling_error(self, error_msg):
        QMessageBox.warning(self, "Profiling Error", error_msg)
        self.statusBar().showMessage("Profiling failed.", 3000)
        self.profiling_worker = None

    def on_upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Pilih File Excel", "", "Excel Files (*.xlsx *.xls *.xlsm)"
        )
        if files and self.file_manager:
            self.file_manager.progress.connect(self.on_copy_progress)
            self.file_manager.finished.connect(self.on_copy_finished)
            self.file_manager.error.connect(self.on_copy_error)
            self.file_manager.copy_files_to_source(files)

    def on_copy_progress(self, current, total):
        self.statusBar().showMessage(f"Copying {current}/{total}...")

    def on_copy_finished(self, copied):
        self.statusBar().showMessage(f"Copied {len(copied)} files.", 3000)
        self.profile_current_project()

    def on_copy_error(self, msg):
        QMessageBox.warning(self, "Copy Error", msg)

    def on_file_selected(self, filename):
        if self.profiler and filename in self.profiler.profiles:
            profile = self.profiler.profiles[filename]
            filepath = self.current_project.folders['source'] / filename
            self.preview_widget.show_preview(filepath, profile)

    def on_processed_file_selected(self, filename):
        """Tampilkan preview file dari folder processed."""
        if not self.current_project:
            return
        filepath = self.current_project.folders['processed'] / filename
        if filepath.exists():
            self.preview_widget.show_processed_preview(filepath)
        else:
            QMessageBox.warning(self, "File Tidak Ditemukan", f"File {filename} tidak ditemukan.")

    def on_chat_message(self, message):
        if not self.profiler or not self.profiler.profiles:
            self.chat_widget.add_message("AI", "Belum ada data yang diprofil. Silakan upload file Excel terlebih dahulu.")
            return
        # Konteks sudah diset via set_context, cukup kirim pesan
        self.chat_widget.send_to_ai(message)

    # ========== ALUR VII: Konfirmasi ==========
    def on_ai_response_ready(self, user_msg, ai_response):
        dialog = ConfirmationDialog(user_msg, ai_response, self)
        dialog.agreed.connect(lambda code: self.execute_action(code))
        dialog.modified.connect(self.on_modify_instruction)
        dialog.exec()

    def on_modify_instruction(self):
        self.chat_widget.input_field.clear()
        self.chat_widget.input_field.setFocus()

    def extract_pandas_code(self, text):
        pattern = r"```(?:\w*)\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return "\n".join(matches).strip()
        else:
            return text.strip()

    def execute_action(self, ai_response):
        code = self.extract_pandas_code(ai_response)
        if not code:
            QMessageBox.warning(self, "Kode Kosong", "Tidak ada kode yang dapat dieksekusi.")
            return

        # Daftar file source untuk snapshot undo (hanya source yang diubah)
        if self.profiler and self.profiler.profiles:
            files = list(self.profiler.profiles.keys())
            source_files = [f for f in files if (self.current_project.folders['source'] / f).exists()]
            file_paths = [str(self.current_project.folders['source'] / f) for f in source_files]
        else:
            file_paths = []

        if self.executor and self.executor.isRunning():
            self.executor.quit()
            self.executor.wait()

        # PandasExecutor adalah QThread, beri parent=self
        self.executor = PandasExecutor(self.current_project, code, files=file_paths, parent=self)
        self.executor.set_undo_manager(self.undo_manager)
        self.executor.finished.connect(self.on_execution_finished)
        self.executor.error.connect(self.on_execution_error)
        self.executor.progress.connect(self.on_execution_progress)
        self.executor.output_file.connect(self.on_execution_output)
        self.executor.finished.connect(self.executor.deleteLater)
        self.executor.start()
        self.statusBar().showMessage("Menjalankan operasi...")

    def on_execution_finished(self, message):
        self.statusBar().showMessage("Eksekusi selesai.", 3000)
        self.chat_widget.add_message("Sistem", message)
        self.profile_current_project()  # Profiling ulang termasuk processed
        self.load_processed_files()     # Refresh daftar processed

        # Putuskan sinyal dan bersihkan
        try:
            self.executor.finished.disconnect()
            self.executor.error.disconnect()
            self.executor.progress.disconnect()
            self.executor.output_file.disconnect()
        except TypeError:
            pass
        self.executor.deleteLater()
        self.executor = None

    def on_execution_error(self, error_msg):
        QMessageBox.critical(self, "Eksekusi Gagal", error_msg)
        self.statusBar().showMessage("Eksekusi gagal.", 3000)
        self.executor = None

    def on_execution_progress(self, current, total):
        self.statusBar().showMessage(f"Progress: {current}/{total}")

    def on_execution_output(self, filepath):
        self.chat_widget.add_message("Sistem", f"File hasil disimpan: {filepath}")

    # ========== ALUR VIII: Undo System ==========
    def on_undo(self):
        if not self.undo_manager:
            QMessageBox.information(self, "Undo", "Tidak ada proyek aktif.")
            return
        if not self.undo_manager.history:
            QMessageBox.information(self, "Undo", "Tidak ada riwayat yang dapat di-undo.")
            return
        last_snapshot = self.undo_manager.history[-1]
        success = self.undo_manager.restore_snapshot(last_snapshot)
        if success:
            self.undo_manager.history.pop()
            self.statusBar().showMessage("Undo berhasil.", 3000)
            self.profile_current_project()
        else:
            QMessageBox.warning(self, "Undo", "Gagal mengembalikan snapshot.")

    def show_trash_dialog(self):
        if not self.undo_manager:
            QMessageBox.information(self, "Trash", "Tidak ada proyek aktif.")
            return
        dialog = TrashDialog(self.undo_manager, self)
        dialog.restore_requested.connect(self.on_restore_from_trash)
        dialog.empty_trash_requested.connect(self.on_empty_trash)
        dialog.exec()

    def on_restore_from_trash(self, trash_path):
        success = self.undo_manager.restore_from_trash(trash_path)
        if success:
            self.statusBar().showMessage("File dipulihkan.", 3000)
            self.profile_current_project()
        else:
            QMessageBox.warning(self, "Restore", "Gagal memulihkan file.")

    def on_empty_trash(self):
        reply = QMessageBox.question(self, "Kosongkan Trash",
                                     "Hapus permanen semua file di trash?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.undo_manager.empty_trash()
            self.statusBar().showMessage("Trash dikosongkan.", 3000)

    def on_delete_file(self, filename):
        if not self.undo_manager or not self.current_project:
            return
        filepath = self.current_project.folders['source'] / filename
        if filepath.exists():
            trash_path = self.undo_manager.move_to_trash(str(filepath))
            if trash_path:
                self.statusBar().showMessage(f"File dipindahkan ke trash: {filename}", 3000)
                if self.profiler and filename in self.profiler.profiles:
                    del self.profiler.profiles[filename]
                # Perbarui daftar source
                source_profiles = {k: v for k, v in self.profiler.profiles.items() if (self.current_project.folders['source'] / k).exists()}
                self.file_list.update_files(source_profiles)
            else:
                QMessageBox.warning(self, "Hapus", "Gagal memindahkan file ke trash.")

    # ========== Method untuk processed files ==========
    def load_processed_files(self):
        """Muat daftar file dari folder processed dan kirim ke file_list."""
        if not self.current_project:
            return
        processed_dir = self.current_project.folders['processed']
        if processed_dir.exists():
            files = [f.name for f in processed_dir.glob("*") if f.is_file() and f.suffix.lower() in ['.xlsx', '.xls', '.xlsm', '.txt']]
            self.file_list.update_processed_files(files)

    # ========== Method untuk membersihkan thread ==========
    def stop_all_threads(self):
        """Hentikan semua thread yang sedang berjalan."""
        # Profiling worker
        if self.profiling_worker and self.profiling_worker.isRunning():
            self.profiling_worker.quit()
            self.profiling_worker.wait(3000)
        # Executor
        if self.executor and self.executor.isRunning():
            self.executor.quit()
            self.executor.wait(3000)
        # FileManager worker
        if self.file_manager and hasattr(self.file_manager, 'stop'):
            self.file_manager.stop()
        # Chat widget worker (sudah ditangani oleh closeEvent widget sendiri)

    def closeEvent(self, event):
        """Hentikan semua thread dan timer sebelum window ditutup."""
        self.activation_timer.stop()
        self.stop_all_threads()
        event.accept()