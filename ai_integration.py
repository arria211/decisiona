import requests
from PySide6.QtCore import QThread, Signal

class AIWorker(QThread):
    response_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, messages, model='mistral:7b', parent=None):
        super().__init__(parent)
        self.model = model
        self.messages = messages
        self._is_running = True
        self.ollama_host = "http://127.0.0.1:11434"  # gunakan IP loopback

    def run(self):
        try:
            # Cek koneksi ke server Ollama
            if not self._check_ollama_server():
                self.error_occurred.emit(
                    "Tidak dapat terhubung ke Ollama server.\n"
                    "Pastikan Ollama sudah berjalan (jalankan 'ollama serve' di PowerShell)."
                )
                return

            # Cek apakah model tersedia
            if not self._check_model_available():
                self.error_occurred.emit(
                    f"Model {self.model} tidak ditemukan.\n"
                    f"Silakan download dengan perintah: `ollama pull {self.model}`"
                )
                return

            if not self._is_running:
                return

            # Kirim permintaan chat ke API Ollama
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.model,
                    "messages": self.messages,
                    "stream": False
                },
                timeout=120
            )

            if response.status_code == 200:
                answer = response.json()['message']['content']
                self.response_ready.emit(answer)
            else:
                self.error_occurred.emit(f"Error HTTP {response.status_code}: {response.text}")

        except requests.exceptions.ConnectionError:
            self.error_occurred.emit(
                "Gagal terhubung ke Ollama. Pastikan server berjalan di 127.0.0.1:11434"
            )
        except Exception as e:
            self.error_occurred.emit(f"Terjadi kesalahan: {str(e)}")

    def stop(self):
        self._is_running = False
        self.quit()
        self.wait()

    def _check_ollama_server(self):
        """Cek apakah server Ollama merespons."""
        try:
            r = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return r.status_code == 200
        except:
            return False

    def _check_model_available(self):
        """Cek apakah model terdaftar di server."""
        try:
            r = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if r.status_code == 200:
                models = r.json().get('models', [])
                return any(self.model in m.get('name', '') for m in models)
            return False
        except:
            return False