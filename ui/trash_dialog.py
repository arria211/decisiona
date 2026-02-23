from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                             QPushButton, QMessageBox)
from PySide6.QtCore import Signal

class TrashDialog(QDialog):
    restore_requested = Signal(str)   # mengirim trash_path
    empty_trash_requested = Signal()

    def __init__(self, undo_manager, parent=None):
        super().__init__(parent)
        self.undo_manager = undo_manager
        self.setWindowTitle("Trash")
        self.setMinimumSize(500, 300)
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.restore_btn = QPushButton("Restore Selected")
        self.restore_btn.clicked.connect(self.on_restore)
        self.empty_btn = QPushButton("Empty Trash")
        self.empty_btn.clicked.connect(self.on_empty)
        btn_layout.addWidget(self.restore_btn)
        btn_layout.addWidget(self.empty_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def refresh_list(self):
        self.list_widget.clear()
        files = self.undo_manager.list_trash()
        for f in files:
            # Tampilkan nama asli (path relatif)
            display = f"📄 {f['original_path']}"
            self.list_widget.addItem(display)
            item = self.list_widget.item(self.list_widget.count() - 1)
            item.setData(1, f['trash_path'])  # simpan trash_path

    def on_restore(self):
        current = self.list_widget.currentItem()
        if not current:
            QMessageBox.information(self, "Restore", "Pilih file yang akan direstore.")
            return
        trash_path = current.data(1)
        self.restore_requested.emit(trash_path)
        self.refresh_list()  # update setelah restore

    def on_empty(self):
        self.empty_trash_requested.emit()
        self.refresh_list()