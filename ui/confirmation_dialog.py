from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLabel, QCheckBox, QMessageBox)
from PySide6.QtCore import Qt, Signal
import re

class ConfirmationDialog(QDialog):
    # Sinyal untuk memberi tahu hasil konfirmasi
    agreed = Signal(str)  # Mengirim kode atau teks yang disetujui
    modified = Signal()   # User ingin mengubah instruksi

    def __init__(self, user_message, ai_response, parent=None):
        super().__init__(parent)
        self.user_message = user_message
        self.ai_response = ai_response
        self.setWindowTitle("Konfirmasi Eksekusi")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.check_dangerous_operation()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Label petunjuk
        layout.addWidget(QLabel("Rekomendasi AI:"))

        # Tampilkan respons AI (bisa diedit jika perlu, tapi kita buat read-only)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.ai_response)
        layout.addWidget(self.text_edit)

        # Checkbox untuk konfirmasi operasi berbahaya (misal hapus data)
        self.danger_check = QCheckBox("Saya memahami bahwa operasi ini dapat menghapus data permanen.")
        self.danger_check.setVisible(False)  # Sembunyikan jika tidak berbahaya
        layout.addWidget(self.danger_check)

        # Tombol
        btn_layout = QHBoxLayout()
        self.jalankan_btn = QPushButton("Jalankan")
        self.jalankan_btn.clicked.connect(self.on_jalankan)
        self.ubah_btn = QPushButton("Ubah Instruksi")
        self.ubah_btn.clicked.connect(self.on_ubah)
        btn_layout.addWidget(self.jalankan_btn)
        btn_layout.addWidget(self.ubah_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def check_dangerous_operation(self):
        """Deteksi apakah respons mengandung operasi berbahaya (misal: drop, delete, hapus)."""
        # Sederhana: cek kata kunci
        dangerous_keywords = ['drop', 'delete', 'hapus', 'remove', 'truncate']
        text_lower = self.ai_response.lower()
        if any(keyword in text_lower for keyword in dangerous_keywords):
            self.danger_check.setVisible(True)
            self.jalankan_btn.setEnabled(False)
            self.danger_check.stateChanged.connect(self.toggle_jalankan)
        else:
            self.jalankan_btn.setEnabled(True)

    def toggle_jalankan(self):
        self.jalankan_btn.setEnabled(self.danger_check.isChecked())

    def on_jalankan(self):
        # Jika ada checkbox berbahaya dan belum dicentang, jangan lanjut
        if self.danger_check.isVisible() and not self.danger_check.isChecked():
            QMessageBox.warning(self, "Konfirmasi", "Anda harus menyetujui risiko sebelum menjalankan.")
            return
        # Ekstrak kode pandas jika ada (opsional, bisa juga langsung gunakan seluruh teks)
        # Kita bisa menyerahkan ekstraksi ke pemanggil (main_window)
        # Untuk fleksibilitas, kita emit seluruh respons
        self.agreed.emit(self.ai_response)
        self.accept()

    def on_ubah(self):
        self.modified.emit()
        self.reject()