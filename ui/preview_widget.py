import os
import pandas as pd
import traceback
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QGroupBox, QFormLayout, QTableView, QPushButton,
                               QProgressBar, QComboBox, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal, QThread
from PySide6.QtGui import QFont

class PandasModel(QAbstractTableModel):
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data

    def rowCount(self, parent=QModelIndex()) -> int:
        return self._data.shape[0] if self._data is not None else 0

    def columnCount(self, parent=QModelIndex()) -> int:
        return self._data.shape[1] if self._data is not None else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._data is None:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            text = str(value)
            if len(text) > 100:
                text = text[:97] + "..."
            return text
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if self._data is None:
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            else:
                return str(self._data.index[section])
        return None

class LoadExcelThread(QThread):
    data_loaded = Signal(object, list)
    error_occurred = Signal(str)

    def __init__(self, filepath, sheet_name=None, nrows=None):
        super().__init__()
        self.filepath = filepath
        self.sheet_name = sheet_name
        self.nrows = nrows

    def run(self):
        try:
            if self.sheet_name is None:
                xl = pd.ExcelFile(self.filepath)
                sheet_names = xl.sheet_names
                df = pd.read_excel(self.filepath, sheet_name=sheet_names[0], nrows=self.nrows)
            else:
                df = pd.read_excel(self.filepath, sheet_name=self.sheet_name, nrows=self.nrows)
                sheet_names = [self.sheet_name]
            self.data_loaded.emit(df, sheet_names)
        except Exception as e:
            self.error_occurred.emit(str(e) + "\n" + traceback.format_exc())

class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filepath = None
        self.full_data = None
        self.current_model = None
        self.thread = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        self.ai_group = QGroupBox("AI Atribut")
        ai_layout = QFormLayout()
        self.quality_label = QLabel("-")
        self.insight_label = QLabel("-")
        self.anomaly_label = QLabel("-")
        self.saran_label = QLabel("-")
        ai_layout.addRow("Kualitas Data:", self.quality_label)
        ai_layout.addRow("Insight:", self.insight_label)
        ai_layout.addRow("Anomali:", self.anomaly_label)
        ai_layout.addRow("Saran:", self.saran_label)
        self.ai_group.setLayout(ai_layout)
        layout.addWidget(self.ai_group)

        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 5, 0, 5)

        self.sheet_combo = QComboBox()
        self.sheet_combo.setEnabled(False)
        self.sheet_combo.currentTextChanged.connect(self.on_sheet_changed)
        control_layout.addWidget(QLabel("Sheet:"))
        control_layout.addWidget(self.sheet_combo)

        self.load_full_btn = QPushButton("Load Full Data")
        self.load_full_btn.clicked.connect(self.load_full_data)
        self.load_full_btn.setEnabled(False)
        control_layout.addWidget(self.load_full_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        self.table_view = QTableView()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table_view.setFont(QFont("Courier", 9))
        layout.addWidget(self.table_view)

        self.setLayout(layout)

    def show_preview(self, filepath, profile):
        self.current_filepath = filepath
        self.full_data = None
        self.sheet_combo.setEnabled(False)
        self.sheet_combo.clear()
        self.load_full_btn.setEnabled(True)
        self._update_ai_attributes(profile)
        self._load_preview_from_file(filepath, nrows=100)

    def show_processed_preview(self, filepath):
        self.current_filepath = filepath
        self.full_data = None
        self.sheet_combo.setEnabled(False)
        self.sheet_combo.clear()
        self.load_full_btn.setEnabled(True)
        # Kosongkan label AI
        self.quality_label.setText("-")
        self.insight_label.setText("-")
        self.anomaly_label.setText("-")
        self.saran_label.setText("-")
        self._load_preview_from_file(filepath, nrows=100)

    def _load_preview_from_file(self, filepath, nrows=100):
        try:
            if not os.path.exists(filepath):
                QMessageBox.warning(self, "File Tidak Ditemukan", f"File tidak ditemukan:\n{filepath}")
                self.table_view.setModel(None)
                return
            try:
                df_sample = pd.read_excel(filepath, nrows=nrows, engine='openpyxl')
            except:
                df_sample = pd.read_excel(filepath, nrows=nrows, engine='xlrd')
            print(f"[Preview] Berhasil membaca {nrows} baris dari file: {df_sample.shape}")
            self._set_table_model(df_sample)
        except Exception as e:
            print(f"[Preview] Gagal membaca file: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Error Preview", f"Gagal membaca file:\n{str(e)}")
            self.table_view.setModel(None)

    def _update_ai_attributes(self, profile):
        shape = profile.get('shape', (0, 0))
        total_rows, total_cols = shape
        missing = sum(profile.get('missing_values', {}).values())
        if total_rows * total_cols > 0:
            quality = int(100 * (1 - missing / (total_rows * total_cols)))
        else:
            quality = 100
        self.quality_label.setText(f"{quality}%")

        numeric_cols = profile.get('numeric_columns', [])
        if numeric_cols:
            insight = f"Numeric: {', '.join(numeric_cols[:3])}"
            if len(numeric_cols) > 3:
                insight += "..."
        else:
            insight = "No numeric data"
        self.insight_label.setText(insight)
        self.anomaly_label.setText("None detected")
        self.saran_label.setText("Group by date for trend")

    def _set_table_model(self, df):
        model = PandasModel(df)
        self.table_view.setModel(model)
        self.current_model = model

    def load_full_data(self):
        if not self.current_filepath:
            return
        try:
            file_size = os.path.getsize(self.current_filepath)
            if file_size > 100 * 1024 * 1024:
                reply = QMessageBox.warning(
                    self,
                    "File Besar",
                    "File ini berukuran lebih dari 100 MB. Memuat seluruh data mungkin memakan memori besar dan memperlambat aplikasi.\n\nTetap muat?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return
        except:
            pass

        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()

        self.progress.setVisible(True)
        self.load_full_btn.setEnabled(False)
        self.sheet_combo.setEnabled(False)

        self.thread = LoadExcelThread(self.current_filepath, nrows=None)
        self.thread.data_loaded.connect(self.on_full_data_loaded)
        self.thread.error_occurred.connect(self.on_load_error)
        self.thread.finished.connect(self.on_thread_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_full_data_loaded(self, df, sheet_names):
        self.full_data = df
        self._set_table_model(df)
        self.sheet_combo.clear()
        self.sheet_combo.addItems(sheet_names)
        self.sheet_combo.setEnabled(True)
        self.progress.setVisible(False)

    def on_load_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Gagal memuat file:\n{error_msg}")
        self.progress.setVisible(False)
        self.load_full_btn.setEnabled(True)

    def on_thread_finished(self):
        self.thread = None

    def on_sheet_changed(self, sheet_name):
        if not self.current_filepath or not sheet_name:
            return
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.progress.setVisible(True)
        self.sheet_combo.setEnabled(False)
        self.load_full_btn.setEnabled(False)
        self.thread = LoadExcelThread(self.current_filepath, sheet_name=sheet_name, nrows=100)
        self.thread.data_loaded.connect(self.on_full_data_loaded)
        self.thread.error_occurred.connect(self.on_load_error)
        self.thread.finished.connect(self.on_thread_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def clear(self):
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.current_filepath = None
        self.full_data = None
        self.quality_label.setText("-")
        self.insight_label.setText("-")
        self.anomaly_label.setText("-")
        self.saran_label.setText("-")
        self.sheet_combo.clear()
        self.sheet_combo.setEnabled(False)
        self.load_full_btn.setEnabled(False)
        self.table_view.setModel(None)
        self.progress.setVisible(False)