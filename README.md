DECISIONA


1.Pendahuluan

DECISIONA adalah aplikasi desktop berbasis AI yang dirancang untuk membantu pengguna bisnis, analis data, dan profesional lainnya dalam melakukan eksplorasi, pembersihan, dan analisis data Excel secara alami menggunakan bahasa sehari-hari (Indonesia/Inggris) tanpa perlu menulis kode. Aplikasi ini beroperasi sepenuhnya secara lokal (private AI), sehingga data pengguna tetap aman dan tidak keluar dari lingkungan mereka.


2.Fitur Utama

2.1Manajemen Proyek

Pembuatan Proyek: Pengguna dapat membuat proyek baru dengan nama unik. Setiap proyek memiliki struktur folder otomatis:

source_files : tempat file Excel asli disalin.

processed_files : tempat hasil analisis/cleaning disimpan.

Satu Proyek Aktif: Hanya satu proyek yang aktif dalam satu waktu, memudahkan fokus pekerjaan.


2.2 Unggah dan Pengelolaan File Excel

Unggah File: Pengguna dapat memilih satu atau beberapa file Excel (.xlsx, .xls, .xlsm) dari komputer. File akan disalin ke folder source_files proyek aktif dengan penamaan otomatis (misal: nama-Copy.xlsx).

Validasi Format: Hanya file Excel yang diperbolehkan.

Indikator Progress: Menampilkan progress saat menyalin file besar.

Daftar File: Menampilkan file sumber dan file hasil olahan (processed) dalam dua daftar terpisah.


2.3Profiling Data Otomatis

Pemindaian Struktur: Setiap file Excel dibaca untuk mendapatkan informasi:

Nama kolom, tipe data, jumlah baris, nilai unik, nilai hilang.

Sampel data (10 baris pertama).

Kolom numerik, kategorikal, dan tanggal.

Deteksi Relasi: Menganalisis kemungkinan hubungan antar file berdasarkan kesamaan nama kolom dan nilai (misal: foreign key). Informasi ini digunakan untuk memberikan konteks yang lebih kaya kepada AI.

Status Profiling: Hasil profiling ditampilkan di UI dan digunakan sebagai konteks bagi AI.


2.4 Antarmuka Percakapan dengan AI

Chat Interaktif: Area chat yang menampilkan riwayat percakapan antara pengguna dan AI.

Input Alami: Pengguna dapat mengetik pertanyaan atau perintah dalam bahasa Indonesia atau Inggris, misalnya:

"Tampilkan preview data"

"Bersihkan data dari nilai kosong"

"Buatkan analisis penjualan per bulan"

Saran Pertanyaan: Menampilkan contoh pertanyaan untuk memudahkan pengguna baru.

Respons AI: AI akan merespons dengan kode Python (yang akan dieksekusi) atau teks penjelasan, tergantung permintaan.

2.5 Penggunaan Model AI Lokal

Model AI: Decisiona menggunakan Model AI yang berjalan sepenuhnya di lokal.

Keamanan: Tidak ada data yang dikirim ke internet; semua proses inference terjadi di mesin pengguna.

2.6 Eksekusi Kode dengan Aman

Ekstraksi Kode: AI menghasilkan kode Python dalam blok kode (python ...). Aplikasi mengekstrak kode tersebut.

Lingkungan Terbatas: Kode dieksekusi dalam lingkungan yang aman dengan hanya modul pandas dan numpy yang diizinkan. Modul lain seperti os, subprocess dilarang.

Data Tersedia: Semua file Excel yang sudah diprofil tersedia dalam dictionary dataframes dengan kunci berupa nama file (tanpa ekstensi, lowercase, underscore). Fungsi save_dataframe dan save_text disediakan untuk menyimpan hasil.

Hasil Eksekusi: Output kode (misalnya DataFrame baru) disimpan di folder processed_files dengan nama otomatis atau sesuai instruksi. Log eksekusi ditampilkan di chat.

2.7 Konfirmasi Sebelum Eksekusi
Dialog Konfirmasi: Sebelum menjalankan kode yang dihasilkan AI, aplikasi menampilkan dialog yang berisi rekomendasi AI. Pengguna dapat menyetujui (Jalankan) atau memodifikasi instruksi (Ubah Instruksi).

Pencegahan Kesalahan: Konfirmasi untuk operasi berbahaya (misal: penghapusan file) ditampilkan.

2.8 Preview File dan Atribut AI
Preview Excel: Saat pengguna memilih file di daftar, tampilan preview menunjukkan isi file (10 baris pertama) dan informasi tambahan seperti kualitas data, insight, anomali, dan saran dari AI.
Atribut AI: Menampilkan ringkasan hasil profiling dalam bentuk metrik (misal: persentase data lengkap, tipe kolom, dll).


2.9 Manajemen Thread dan Kestabilan
Semua operasi berat (profiling, eksekusi, copy file, komunikasi AI) dijalankan dalam thread terpisah (QThread) agar antarmuka tetap responsif.
Mekanisme penghentian thread yang aman saat aplikasi ditutup atau berganti proyek, menghindari kebocoran memori dan crash.


2.10 Versi Development

Saat ini Decisiona masih Versi Development dan akan terus di perbaharui sesuai kebutuhan pengguna



						                                                         Padang 22 Februari 2026
                                                                                          Ttd

                                                                                         ARRIA
                                                                                        Founder
