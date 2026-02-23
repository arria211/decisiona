import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations
from PySide6.QtCore import QThread, Signal

class ExcelProfiler:
    def __init__(self, project):
        self.project = project
        self.source_dir = project.folders['source']
        self.processed_dir = project.folders['processed']
        self.profiles = {}          # gabungan source + processed
        self.relationships = []

    def profile_all(self):
        """Profile all Excel files in source and processed folders."""
        self._profile_folder(self.source_dir)
        self._profile_folder(self.processed_dir)
        self._detect_relationships()
        return self.profiles

    def _profile_folder(self, folder):
        """Profile all Excel files in a given folder."""
        files = list(folder.glob("*.xlsx")) + list(folder.glob("*.xls")) + list(folder.glob("*.xlsm"))
        for file in files:
            try:
                profile = self._profile_file(file)
                self.profiles[file.name] = profile
            except Exception as e:
                print(f"Error profiling {file.name}: {e}")

    def _profile_file(self, filepath):
        df = pd.read_excel(filepath, nrows=100)
        sample_data = df.head(100).to_dict(orient='list')
        profile = {
            'filename': filepath.name,
            'columns': list(df.columns),
            'dtypes': df.dtypes.astype(str).to_dict(),
            'sample_rows': df.head(10).to_dict(orient='records'),
            'shape': df.shape,
            'missing_values': df.isnull().sum().to_dict(),
            'numeric_columns': df.select_dtypes(include=[np.number]).columns.tolist(),
            'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
            'datetime_columns': df.select_dtypes(include=['datetime64']).columns.tolist(),
            'sample_data': sample_data,
            'unique_values': {col: df[col].nunique() for col in df.columns}
        }
        return profile

    def _detect_relationships(self):
        """Detect relationships between files (based on sample data)."""
        self.relationships = []
        file_names = list(self.profiles.keys())
        for f1, f2 in combinations(file_names, 2):
            prof1 = self.profiles[f1]
            prof2 = self.profiles[f2]
            for col1 in prof1['columns']:
                for col2 in prof2['columns']:
                    if col1 == col2 and prof1['dtypes'][col1] == prof2['dtypes'][col2]:
                        values1 = set(prof1['sample_data'].get(col1, []))
                        values2 = set(prof2['sample_data'].get(col2, []))
                        values1 = {v for v in values1 if pd.notna(v)}
                        values2 = {v for v in values2 if pd.notna(v)}
                        if values1 and values2:
                            overlap = values1.intersection(values2)
                            if overlap:
                                percent1 = len(overlap) / len(values1) * 100 if values1 else 0
                                percent2 = len(overlap) / len(values2) * 100 if values2 else 0
                                if percent1 > 50 or percent2 > 50:
                                    rel = {
                                        'file1': f1,
                                        'file2': f2,
                                        'column1': col1,
                                        'column2': col2,
                                        'overlap_count': len(overlap),
                                        'overlap_percent1': round(percent1, 1),
                                        'overlap_percent2': round(percent2, 1),
                                        'type': 'possible_foreign_key'
                                    }
                                    self.relationships.append(rel)
                    elif prof1['dtypes'][col1] == prof2['dtypes'][col2]:
                        values1 = set(prof1['sample_data'].get(col1, []))
                        values2 = set(prof2['sample_data'].get(col2, []))
                        values1 = {v for v in values1 if pd.notna(v)}
                        values2 = {v for v in values2 if pd.notna(v)}
                        if values1 and values2:
                            overlap = values1.intersection(values2)
                            if overlap:
                                percent1 = len(overlap) / len(values1) * 100 if values1 else 0
                                percent2 = len(overlap) / len(values2) * 100 if values2 else 0
                                if percent1 > 50 or percent2 > 50:
                                    rel = {
                                        'file1': f1,
                                        'file2': f2,
                                        'column1': col1,
                                        'column2': col2,
                                        'overlap_count': len(overlap),
                                        'overlap_percent1': round(percent1, 1),
                                        'overlap_percent2': round(percent2, 1),
                                        'type': 'possible_relationship'
                                    }
                                    self.relationships.append(rel)

        # Tambahkan informasi relasi ke masing-masing profil
        for prof in self.profiles.values():
            prof['relationships'] = []
        for rel in self.relationships:
            self.profiles[rel['file1']]['relationships'].append({
                'with_file': rel['file2'],
                'column': rel['column1'],
                'related_column': rel['column2'],
                'overlap': f"{rel['overlap_percent1']}% of values match"
            })
            self.profiles[rel['file2']]['relationships'].append({
                'with_file': rel['file1'],
                'column': rel['column2'],
                'related_column': rel['column1'],
                'overlap': f"{rel['overlap_percent2']}% of values match"
            })

    def get_context_for_ai(self):
        """Buat konteks untuk AI dengan informasi detail per file."""
        context = "DATA PROFILING RESULTS:\n"
        context += "=" * 50 + "\n"
        for fname, prof in self.profiles.items():
            # Buat key untuk dataframe (sesuai transformasi di executor) dalam huruf kecil
            key = Path(fname).stem.replace(' ', '_').replace('-', '_').lower()
            context += f"\nFile: {fname}\n"
            context += f"Dataframe key: {key}\n"
            context += f"Shape: {prof['shape']}\n"
            context += "Columns and types:\n"
            for col, dtype in prof['dtypes'].items():
                context += f"  - {col} ({dtype})"
                # Tambahkan contoh nilai jika ada di sample_rows
                if prof['sample_rows'] and col in prof['sample_rows'][0]:
                    sample_val = prof['sample_rows'][0][col]
                    context += f"  contoh: {sample_val}"
                context += "\n"
            context += f"Sample rows (first 2):\n"
            for row in prof['sample_rows'][:2]:
                context += f"  {row}\n"
            if prof['relationships']:
                context += "Relationships:\n"
                for rel in prof['relationships']:
                    context += f"  - {rel['column']} di file ini terkait dengan {rel['related_column']} di {rel['with_file']} (overlap {rel['overlap']})\n"
        return context


class ProfilingWorker(QThread):
    finished = Signal(object)  # mengirim hasil profiling (dict)
    error = Signal(str)

    def __init__(self, profiler, parent=None):
        super().__init__(parent)
        self.profiler = profiler

    def run(self):
        try:
            profiles = self.profiler.profile_all()
            self.finished.emit(profiles)
        except Exception as e:
            self.error.emit(str(e))