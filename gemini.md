# GEMINI.md - WinFams AI Coding Rules & Architecture Guide

Dokumen ini adalah instruksi sistem wajib untuk AI Assistant dalam mengembangkan proyek **WinFams**. Anda WAJIB mematuhi seluruh aturan di bawah ini sebelum menulis atau memodifikasi kode apa pun.

## 1. Konteks Proyek & Urutan Eksekusi (Edge-First -> API -> Mobile)
* Baca `winfams_prd.md` untuk memahami spesifikasi fitur, skema tabel SQL, kontrak JSON, dan struktur direktori 3 pilar (`winfams-edge`, `winfams-api`, `winfams-mobile`).
* Baca `backlog.md` untuk melihat daftar tugas yang sedang dikerjakan.
* **ATURAN EMAS EKSEKUSI:** Kerjakan **HANYA 1 (satu) item backlog dalam satu waktu** sesuai urutan:
  1. **Epik 1 & 2 (`winfams-edge`):** Alat Raspberry Pi 4 + Pre-trained AI + Buzzer + GPS berjalan dulu secara lokal.
  2. **Epik 3 (`winfams-api`):** Backend FastAPI + Database SQL + WebSocket dibuat dan diuji.
  3. **Epik 4 (`winfams-edge` Sync):** Hubungkan Raspberry Pi 4 ke REST API disertai fitur Offline SQLite Queue.
  4. **Epik 5 & 6 (`winfams-mobile`):** Bangun aplikasi Flutter yang mengonsumsi REST API dan WebSocket dari Backend.
* Perbarui status tugas di `backlog.md` menjadi `[x]` hanya setelah kode selesai dibuat dan diuji.

## 2. Aturan Computer Vision (Pre-trained Model Only)
* **DILARANG** menulis rumus geometri manual yang rumit (seperti menghitung jarak Euclidean titik mata manual) di dalam kode utama.
* Gunakan **Pre-trained Model** resmi yang ringan untuk Raspberry Pi 4:
  * **Default:** `mediapipe.tasks.python.vision.FaceLandmarker` dengan `output_face_blendshapes=True`. Ambil skor langsung dari blendshape `eyeBlinkLeft`, `eyeBlinkRight`, dan `jawOpen`.
  * **Alternatif:** `ultralytics.YOLO` menggunakan model pre-trained deteksi kantuk yang diekspor ke format **NCNN** atau **TFLite**.
* Bungkus pemanggilan model di dalam `winfams-edge/core/detector.py` dengan *interface* yang bersih sehingga model bisa diganti kapan saja tanpa mengubah `state_machine.py` atau `main.py`.

## 3. Prinsip Anti-Spaghetti & Anti-AI Slop
1. **Batas Ukuran File:** Tidak boleh ada file yang melebihi **250 baris kode**. Jika lebih, pecah menjadi modul yang lebih kecil.
2. **Separation of Concerns (SoC):**
   * *Hardware I/O* (`camera_stream.py`, `gps_reader.py`, `buzzer_controller.py`) **DILARANG** mengimpor library HTTP/API atau melakukan query database.
   * *Core Logic* (`detector.py`, `state_machine.py`) harus berupa *pure logic* yang bisa diuji di laptop tanpa harus menyalakan Buzzer atau GPS fisik (wajib sediakan `MOCK_HARDWARE=True`).
   * *Backend API* (`winfams-api`) wajib memisahkan definisi tabel SQLAlchemy (`models/`), validasi input/output Pydantic (`schemas/`), dan rute HTTP (`api/`).
3. **Zero Blocking di Main Loop (Pi 4):**
   * Pembacaan frame kamera, pembacaan port serial GPS, bunyi Buzzer, dan pengiriman HTTP ke FastAPI **WAJIB** berjalan di *thread* atau *async queue* terpisah.
   * **DILARANG** menaruh `time.sleep()` atau `requests.post()` sinkron di dalam *loop* inferensi kamera OpenCV.
4. **Dilarang Menulis Kode Placeholder (No AI Slop):**
   * Jangan pernah menulis komentar seperti `# TODO: implement logic here` atau `// Add API call later`. Tulis implementasi lengkap dan fungsional untuk setiap modul yang diminta.
   * Jangan mengarang nama *method* atau *package* yang tidak ada (halusinasi API).

## 4. Standar Penulisan Kode (Code Style)
### Python (`winfams-edge` & `winfams-api`)
* Gunakan Python 3.10+ dengan **Explicit Type Hints** pada semua parameter fungsi dan *return value*.
* Gunakan `@dataclass` atau `pydantic.BaseModel` untuk semua objek transfer data.
* Gunakan `logging` bawaan Python (bukan `print()`) dengan format waktu dan level (`INFO`, `WARNING`, `ERROR`).
* **Fault Tolerance (Edge):** Jika modul GPS belum mendapatkan *lock* satelit (`lat/lng = None`) atau server API sedang tidak bisa dihubungi, deteksi kantuk dan buzzer **HARUS tetap berjalan normal** tanpa *crash*.

### Database SQL (`winfams-api`)
* Gunakan **SQLAlchemy 2.0 style** (`mapped_column`, `Mapped`, `select()`).
* Pastikan semua kolom *Foreign Key* dan kolom pencarian sering (`device_uid`, `family_id`, `recorded_at`) memiliki indeks (`index=True`).

### Flutter (`winfams-mobile`)
* Gunakan **Flutter 3.x** dan **Dart 3.x** dengan *strict null-safety*. Dilarang menggunakan tipe data `dynamic` tanpa *type casting* yang aman.
* Gunakan **Riverpod** (`ConsumerWidget`, `Notifier`, `AsyncNotifier`) untuk *state management*.
* **DILARANG** menaruh pemanggilan HTTP/Dio langsung di dalam method `build()`.

## 5. Protokol Eksekusi Vibe Coding
Setiap kali pengguna meminta pengerjaan fitur:
1. Sebutkan **ID Task** dari `backlog.md` yang sedang dikerjakan.
2. Tampilkan kode lengkap untuk file yang bersangkutan sesuai struktur folder di `winfams_prd.md`.
3. Berikan perintah terminal singkat untuk menguji file tersebut secara terisolasi.