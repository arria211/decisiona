import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from activation import ActivationManager

def global_exception_hook(exctype, value, tb):
    """Handler untuk exception yang tidak tertangani."""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    QMessageBox.critical(None, "Unhandled Exception",
                         f"Terjadi error yang tidak tertangani:\n\n{error_msg}")
    # Panggil hook bawaan (opsional)
    sys.__excepthook__(exctype, value, tb)

# Pasang global exception hook
sys.excepthook = global_exception_hook

def main():
    app = QApplication(sys.argv)
    
    # Check activation before showing main window
    activation = ActivationManager()
    if not activation.is_activated():
        from ui.activation_dialog import ActivationDialog
        dlg = ActivationDialog(activation)
        if dlg.exec() != ActivationDialog.DialogCode.Accepted:
            sys.exit(0)  # User closed without activating
    
    window = MainWindow(activation)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()