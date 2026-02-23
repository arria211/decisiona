from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QPushButton, QInputDialog, QMessageBox, QMenu)
from PySide6.QtCore import Signal, Qt, QPoint

class ProjectListWidget(QWidget):
    project_selected = Signal(object)  # Project
    project_created = Signal(object)
    project_deleted = Signal(object)   # Project yang dihapus

    def __init__(self, project_manager, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.setup_ui()
        self.refresh_list()
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_context_menu)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.list = QListWidget()
        self.list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list)

        self.new_btn = QPushButton("+ New Project")
        self.new_btn.clicked.connect(self.create_new_project)
        layout.addWidget(self.new_btn)

        self.setLayout(layout)

    def refresh_list(self):
        self.list.clear()
        projects = self.project_manager.get_project_list()
        for proj in projects:
            item = QListWidgetItem(f"{proj.name}\n{proj.id}")
            item.setData(32, proj)
            self.list.addItem(item)

    def on_item_clicked(self, item):
        proj = item.data(32)
        if proj:
            self.project_manager.set_active_project(proj.id)
            self.project_selected.emit(proj)

    def create_new_project(self):
        name, ok = QInputDialog.getText(self, "New Project", "Project name:")
        if ok and name:
            try:
                proj = self.project_manager.create_project(name)
                self.refresh_list()
                self.project_created.emit(proj)
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def show_context_menu(self, pos: QPoint):
        item = self.list.itemAt(pos)
        if not item:
            return
        proj = item.data(32)
        if not proj:
            return
        menu = QMenu()
        delete_action = menu.addAction("Delete Project")
        action = menu.exec(self.list.mapToGlobal(pos))
        if action == delete_action:
            self.delete_project(proj)

    def delete_project(self, proj):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete project '{proj.name}'?\nAll files will be permanently deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.project_manager.delete_project(proj.id):
                self.refresh_list()
                self.project_deleted.emit(proj)
            else:
                QMessageBox.warning(self, "Error", "Failed to delete project.")