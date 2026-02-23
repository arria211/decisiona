from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit,
                               QPushButton, QHBoxLayout, QLabel)
from PySide6.QtCore import Signal, Qt
from ai_integration import AIWorker

class ChatWidget(QWidget):
    send_message = Signal(str)
    ai_response_ready = Signal(str, str)  # (user_message, ai_response)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profiling_context = ""
        self.ai_worker = None
        self.last_user_input = None
        self.messages = []  # untuk memori percakapan
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        layout.addWidget(self.history)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ketik pesan...")
        self.input_field.returnPressed.connect(self.on_send)
        self.send_btn = QPushButton("📎")
        self.send_btn.clicked.connect(self.on_send)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

        self.suggestions = QLabel("Coba tanya: 'Tampilkan preview' atau 'Bersihkan data'")
        self.suggestions.setWordWrap(True)
        layout.addWidget(self.suggestions)

        self.setLayout(layout)

        # Initial AI greeting
        self.add_message("AI", "Halo! Saya DECISIONA AI, siap bantu analisis data Anda.")

    def add_message(self, sender, text):
        self.history.append(f"<b>{sender}:</b> {text}")
        role = "user" if sender == "Anda" else "assistant"
        self.messages.append({"role": role, "content": text})

    def on_send(self):
        msg = self.input_field.text().strip()
        if msg:
            self.add_message("Anda", msg)
            self.send_message.emit(msg)
            self.input_field.clear()
            self.send_to_ai(msg)

    def set_context(self, context):
        self.profiling_context = context

    def send_to_ai(self, user_input):
        # Pesan sistem dengan instruksi yang sangat ketat dan detail
        system_content = (
            "Anda adalah DECISIONA AI, asisten analisis data. Tugas Anda adalah menghasilkan kode Python yang akan dieksekusi untuk memenuhi permintaan pengguna.\n"
            "Berikut adalah hasil profiling data yang tersedia (mencakup file dari folder source dan processed):\n"
            f"{self.profiling_context}\n\n"
            "Semua file Excel dari folder source dan processed telah dimuat ke dalam DataFrame pandas dan tersedia dalam variabel berikut:\n"
            "- 'dataframes': dictionary dengan kunci = nama file TANPA EKSTENSI, dengan spasi dan tanda hubung diganti underscore, dan **semua huruf kecil (lowercase)**.\n"
            "  Contoh: file 'MRBH 31 JAN 2022-Copy.xlsx' → kunci 'mrbh_31_jan_2022_copy'.\n"
            "- 'save_dataframe(df, filename)': fungsi untuk menyimpan DataFrame ke file Excel di folder processed.\n"
            "- 'save_text(text, filename)': fungsi untuk menyimpan teks ke file .txt di folder ai_analysis.\n\n"
            "PENTING: \n"
            "1. JANGAN gunakan pd.read_csv(), pd.read_excel(), atau fungsi baca file lainnya. Data sudah tersedia.\n"
            "2. JANGAN gunakan path file apapun. HANYA gunakan variabel 'dataframes'.\n"
            "3. Nama variabel adalah 'dataframes' (dengan huruf 's' di akhir), bukan 'dataframe'.\n"
            "4. Gunakan kunci yang sudah ditransformasi (underscore) dan dalam huruf kecil sesuai contoh di atas.\n"
            "5. Untuk mengakses kolom, gunakan notasi string, misal: df['nama_kolom'], bukan df.nama_kolom (karena nama kolom bisa mengandung spasi atau karakter khusus).\n"
            "6. Jika pengguna meminta menampilkan baris dengan nilai tertentu di suatu kolom, gunakan method .isin() untuk beberapa nilai. Contoh: df[df['kolom'].isin([nilai1, nilai2])]\n"
            "7. Hindari menimpa dataframe asli. Gunakan variabel baru seperti 'hasil' atau 'filtered_df'.\n"
            "8. Jika pengguna meminta menyimpan hasil, gunakan variabel 'result' untuk DataFrame yang akan disimpan, lalu panggil save_dataframe(result, nama_file).\n"
            "9. Jika hanya ingin menampilkan hasil di console, gunakan print().\n\n"
            "INSTRUKSI KHUSUS:\n"
            "- Anda HARUS mengembalikan **hanya kode Python** dalam satu blok kode yang diapit oleh ```python dan ```.\n"
            "- Jangan sertakan teks penjelasan apa pun di luar blok kode.\n"
            "- Kode Anda harus lengkap dan dapat dieksekusi langsung.\n"
            "- Gunakan variabel 'result' untuk menyimpan DataFrame hasil jika akan disimpan.\n"
            "- Jika Anda perlu menampilkan sesuatu, gunakan print().\n\n"
            "Contoh format jawaban yang benar:\n"
            "```python\n"
            "df_sumber = dataframes['mrbh_31_jan_2022_copy']\n"
            "# Filter untuk nilai 2, 3, dan 4 di kolom KOLEKTIBILITY\n"
            "hasil = df_sumber[df_sumber['KOLEKTIBILITY'].isin([2, 3, 4])]\n"
            "save_dataframe(hasil, 'hasil_filter_kolektibilitas.xlsx')\n"
            "print('File berhasil disimpan')\n"
            "```\n\n"
            "Contoh lain: menampilkan preview 5 baris pertama:\n"
            "```python\n"
            "df = dataframes['mrbh_31_jan_2022_copy']\n"
            "print(df.head(5))\n"
            "```\n\n"
            "Jangan pernah memberikan penjelasan di luar blok kode. Hanya kode.\n"
            "Jika permintaan tidak memerlukan kode (misalnya hanya bertanya), Anda boleh menjawab dengan teks biasa, tetapi untuk permintaan yang memerlukan aksi, berikan kode.\n"
            "Sekarang, jawablah pertanyaan berikut dengan kode Python sesuai format di atas.\n"
        )

        # Bangun daftar pesan untuk AI
        messages_for_ai = [{"role": "system", "content": system_content}]
        # Sertakan hingga 10 pesan terakhir (agar tidak kelebihan token)
        messages_for_ai.extend(self.messages[-10:])

        # Hentikan worker sebelumnya jika masih berjalan
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.quit()
            self.ai_worker.wait()

        self.last_user_input = user_input
        # Buat worker dengan parent=self agar terikat siklus hidup widget
        self.ai_worker = AIWorker(messages=messages_for_ai, parent=self)
        self.ai_worker.response_ready.connect(self.on_ai_response)
        self.ai_worker.error_occurred.connect(self.on_ai_error)
        self.ai_worker.finished.connect(self.ai_worker.deleteLater)
        self.ai_worker.start()

    def on_ai_response(self, response):
        self.add_message("AI", response)
        if self.last_user_input is not None:
            self.ai_response_ready.emit(self.last_user_input, response)
            self.last_user_input = None
        self.ai_worker = None

    def on_ai_error(self, error):
        self.add_message("AI", f"Maaf, terjadi kesalahan: {error}")
        self.ai_worker = None

    def clear(self):
        self.history.clear()
        self.messages.clear()
        self.add_message("AI", "Halo! Saya DECISIONA AI, siap bantu analisis data Anda.")

    def closeEvent(self, event):
        """Hentikan worker saat widget ditutup."""
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.quit()
            self.ai_worker.wait()
        event.accept()