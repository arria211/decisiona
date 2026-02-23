from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QPushButton, QHBoxLayout, QStyle, QMessageBox, QLabel)
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon

class FileListWidget(QWidget):
    upload_requested = Signal()
    file_selected = Signal(str)          # filename dari source
    refresh_requested = Signal()          # untuk meminta profiling ulang
    delete_file_requested = Signal(str)   # untuk menghapus file source
    processed_file_selected = Signal(str) # filename dari processed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self.profiles = {}
        self.processed_files = []          # daftar file processed
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Tombol-tombol untuk source
        btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Files")
        self.upload_btn.clicked.connect(self.upload_requested.emit)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.on_delete)
        btn_layout.addWidget(self.upload_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        # Label untuk source files
        layout.addWidget(QLabel("Source Files:"))
        # Daftar file source
        self.source_list = QListWidget()
        self.source_list.itemClicked.connect(self.on_source_item_clicked)
        layout.addWidget(self.source_list)

        # Label untuk processed files
        layout.addWidget(QLabel("Processed Files:"))
        # Daftar file processed
        self.processed_list = QListWidget()
        self.processed_list.itemClicked.connect(self.on_processed_item_clicked)
        layout.addWidget(self.processed_list)

        self.setLayout(layout)

    def set_project(self, project):
        self.project = project

    def update_files(self, profiles):
        """Perbarui daftar file source dengan data profiling."""
        self.profiles = profiles
        self.source_list.clear()
        check_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton)
        for fname in profiles.keys():
            item = QListWidgetItem(fname)
            item.setIcon(check_icon)
            self.source_list.addItem(item)

    def update_processed_files(self, file_list):
        """Perbarui daftar file processed."""
        self.processed_files = file_list
        self.processed_list.clear()
        for fname in file_list:
            item = QListWidgetItem(fname)
            # Opsional: tambahkan ikon berbeda (misalnya file icon)
            self.processed_list.addItem(item)

    def on_source_item_clicked(self, item):
        fname = item.text()
        self.file_selected.emit(fname)

    def on_processed_item_clicked(self, item):
        fname = item.text()
        self.processed_file_selected.emit(fname)

    def on_delete(self):
        """Minta penghapusan file source yang dipilih."""
        current_item = self.source_list.currentItem()
        if current_item is None:
            QMessageBox.information(self, "Hapus File", "Pilih file source yang akan dihapus.")
            return
        fname = current_item.text()
        self.delete_file_requested.emit(fname)