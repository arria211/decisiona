from PySide6.QtGui import QFontDatabase, QFont, QPalette, QColor
from PySide6.QtCore import Qt

def setup_theme(app, dark_mode=False):
    """Apply color scheme and font."""
    # Inter font
    QFontDatabase.addApplicationFont(":/fonts/Inter-Regular.ttf")  # you'd need to include the font file
    app.setFont(QFont("Inter", 10))
    
    if dark_mode:
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.black)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        app.setPalette(dark_palette)
    else:
        light_palette = app.style().standardPalette()
        light_palette.setColor(QPalette.ColorRole.Highlight, QColor(37, 99, 235))  # #2563EB
        light_palette.setColor(QPalette.ColorRole.Button, QColor(100, 116, 139))  # #64748B secondary
        app.setPalette(light_palette)