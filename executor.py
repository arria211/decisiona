import sys
import io
import traceback
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QThread, Signal

class PandasExecutor(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int, int)
    output_file = Signal(str)

    def __init__(self, project, code, operation_type='cleaning', files=None, parent=None):
        super().__init__(parent)
        self.project = project
        self.code = code
        self.operation_type = operation_type
        self.files = files or []
        self.undo_manager = None

    def set_undo_manager(self, undo_manager):
        self.undo_manager = undo_manager

    def run(self):
        try:
            if self.undo_manager and self.files:
                self.undo_manager.create_snapshot(self.files)
                self.progress.emit(1, 3)

            dataframes = {}
            folders = [
                ('source', self.project.folders['source']),
                ('processed', self.project.folders['processed'])
            ]
            for folder_name, folder_path in folders:
                if not folder_path.exists():
                    continue
                for ext in ['*.xlsx', '*.xls', '*.xlsm']:
                    for file_path in folder_path.glob(ext):
                        try:
                            df_file = pd.read_excel(file_path)
                            key = file_path.stem.replace(' ', '_').replace('-', '_').lower()
                            dataframes[key] = df_file
                        except Exception as e:
                            print(f"Gagal memuat {file_path}: {e}")

            if len(dataframes) == 1:
                df = list(dataframes.values())[0]
            else:
                df = None

            def custom_import(name, *args, **kwargs):
                allowed_modules = ['pandas', 'numpy']
                if name in allowed_modules:
                    return __import__(name, *args, **kwargs)
                else:
                    raise ImportError(f"Module '{name}' tidak diizinkan.")

            safe_globals = {
                'pd': pd,
                'np': np,
                'project': self.project,
                'files': self.files,
                'dataframes': dataframes,
                'df': df,
                'datetime': datetime,
                'Path': Path,
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'open': open,
                    '__import__': custom_import,
                }
            }

            def save_dataframe(df, filename=None):
                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"result_{timestamp}.xlsx"
                output_dir = self.project.folders['processed']
                output_path = output_dir / filename
                if isinstance(df, pd.DataFrame):
                    df.to_excel(output_path, index=False)
                else:
                    with open(output_path, 'w') as f:
                        f.write(str(df))
                return str(output_path)

            def save_text(text, filename=None):
                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"analysis_{timestamp}.txt"
                output_dir = self.project.folders['ai_analysis']
                output_path = output_dir / filename
                with open(output_path, 'w') as f:
                    f.write(text)
                return str(output_path)

            safe_globals['save_dataframe'] = save_dataframe
            safe_globals['save_text'] = save_text

            if 'pd.read_csv' in self.code or 'pd.read_excel' in self.code:
                raise Exception("Kode mengandung perintah membaca file yang tidak diizinkan.")

            original_cwd = os.getcwd()
            source_dir = self.project.folders['source']
            if source_dir.exists():
                os.chdir(source_dir)

            stdout_capture = io.StringIO()
            sys.stdout = stdout_capture

            try:
                exec(self.code, safe_globals)
            finally:
                os.chdir(original_cwd)
                sys.stdout = sys.__stdout__

            output_log = stdout_capture.getvalue()

            if 'result' in safe_globals and isinstance(safe_globals['result'], pd.DataFrame):
                path = save_dataframe(safe_globals['result'])
                self.output_file.emit(path)

            self.progress.emit(3, 3)
            self.finished.emit(f"Eksekusi selesai.\n{output_log}")

        except Exception as e:
            sys.stdout = sys.__stdout__
            error_msg = f"Error saat eksekusi: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)