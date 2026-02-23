from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtCore import Qt

class ActivationDialog(QDialog):
    def __init__(self, activation_manager, parent=None):
        super().__init__(parent)
        self.activation = activation_manager
        self.setWindowTitle("DECISIONA Activation")
        self.setFixedSize(400, 250)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        label = QLabel("🔐 Masukkan Kode Aktivasi")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Kode aktivasi")
        layout.addWidget(self.code_input)
        
        btn_layout = QHBoxLayout()
        self.activate_btn = QPushButton("Aktifkan")
        self.activate_btn.clicked.connect(self.activate_commercial)
        self.trial_btn = QPushButton("Mulai Trial 14H")
        self.trial_btn.clicked.connect(self.activate_trial)
        btn_layout.addWidget(self.activate_btn)
        btn_layout.addWidget(self.trial_btn)
        layout.addLayout(btn_layout)
        
        self.status_label = QLabel("Status: Belum Aktif")
        layout.addWidget(self.status_label)
        
        info_label = QLabel("Info: Trial 14 hari full feature")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def activate_trial(self):
        ok, msg = self.activation.activate_trial()
        if ok:
            QMessageBox.information(self, "Sukses", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Gagal", msg)
    
    def activate_commercial(self):
        code = self.code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "Input", "Masukkan kode aktivasi.")
            return
        ok, msg = self.activation.activate_commercial(code)
        if ok:
            QMessageBox.information(self, "Sukses", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Gagal", msg)