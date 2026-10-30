# WinFams Development Backlog (Edge -> API/SQL -> Mobile)

Gunakan file ini untuk melacak progres pengembangan (*vibe coding*). Kerjakan secara berurutan dari Epik 1 hingga Epik 6.

**Keterangan Status:**
* `[ ]` Belum dikerjakan (To Do)
* `[~]` Sedang dikerjakan (In Progress)
* `[x]` Selesai & Teruji (Done)

---

## Epik 1: Pondasi Edge AI & Pre-trained CV (`winfams-edge`)
*Tujuan: Mendapatkan deteksi kantuk dan menguap secara real-time dari webcam menggunakan model pre-trained tanpa lag (bisa dites di laptop maupun Raspberry Pi 4).*

* `[x]` **EDGE-01: Inisialisasi Proyek Edge, Konfigurasi & Kontrak Data (`config/settings.py`, `schemas/payload.py`)**
  * Buat struktur folder `winfams-edge/` dan `requirements.txt`.
  * Definisikan konstanta threshold (`BLINK_THRESHOLD = 0.55`, `YAWN_THRESHOLD = 0.60`, `DROWSY_TIME_SEC = 1.5`), konfigurasi `MOCK_HARDWARE`, pin GPIO, URL API, serta `dataclasses` untuk `HeartbeatPayload` dan `IncidentPayload`.
* `[x]` **EDGE-02: Multithreaded Camera Stream (`core/camera_stream.py`)**
  * Buat class pembaca webcam menggunakan `cv2.VideoCapture` yang berjalan di *daemon thread* tersendiri agar selalu mengambil frame terbaru tanpa *buffer lag*.
* `[x]` **EDGE-03: Pre-trained Model Detector Wrapper (`core/detector.py`)**
  * Buat pengunduh otomatis file model resmi `face_landmarker.task` (MediaPipe) dengan `output_face_blendshapes=True` (serta opsi dukungan YOLO NCNN).
  * Ekstrak skor `drowsy_confidence` (rata-rata `eyeBlinkLeft` & `eyeBlinkRight`) dan `yawn_confidence` (`jawOpen`) pada setiap frame.
* `[x]` **EDGE-04: Fatigue State Machine (`core/state_machine.py`)**
  * Buat logika berbasis waktu (*timer*): memicu `CRITICAL_DROWSY` jika mata tertutup $\ge 1.5\text{ detik}$, dan `WARNING_FATIGUE` jika menguap $\ge 2.5\text{ detik}$ sebanyak 3 kali dalam 10 menit. Sediakan unit test di `tests/test_state_machine.py`.

---

## Epik 2: Integrasi Hardware Lokal - Buzzer & GPS (`winfams-edge`)
*Tujuan: Memberikan peringatan suara instan di mobil dan membaca koordinat lokasi tanpa memblokir proses kamera.*

* `[x]` **HW-01: Non-Blocking Buzzer Controller (`hardware/buzzer_controller.py`)**
  * Gunakan `gpiozero.Buzzer` untuk membuat fungsi peringatan suara pola cepat (*beep* darurat) dan pola lambat (*warning*).
  * Sediakan *mock mode* otomatis jika kode dijalankan di laptop/PC (bukan Raspberry Pi) untuk keperluan testing.
* `[x]` **HW-02: GPS Serial Reader Thread (`hardware/gps_reader.py`)**
  * Baca kalimat NMEA (`$GPGGA`, `$GPRMC`) dari port serial UART menggunakan `pyserial` dan `pynmea2` di thread terpisah.
  * Sediakan *fallback* koordinat *dummy/mock* jika modul GPS belum terhubung saat testing.
* `[x]` **HW-03: Edge Main Orchestrator Lokal (`main.py`)**
  * Hubungkan `camera_stream`, `detector`, `state_machine`, `buzzer_controller`, dan `gps_reader` dalam satu alur kerja yang bersih dengan overlay indikator FPS & status di layar.

---

## Epik 3: Backend REST API, Database SQL & WebSocket (`winfams-api`)
*Tujuan: Membangun server pusat dengan FastAPI dan Database SQL (PostgreSQL/MySQL) untuk menyimpan relasi keluarga, lokasi kendaraan, dan menyebarkan alert darurat.*

* `[x]` **API-01: Setup FastAPI, SQLAlchemy 2.0 & Tabel SQL (`app/core/`, `app/models/`)**
  * Buat struktur folder `winfams-api/`, koneksi database SQL, dan kelima model ORM: `User`, `Family`, `FamilyMember`, `Device`, dan `FatigueIncident`.
* `[x]` **API-02: Autentikasi JWT & Manajemen Grup Keluarga (`app/api/auth.py`, `app/api/families.py`)**
  * Buat endpoint Register, Login, Update FCM Token, Buat Grup Keluarga (`invite_code` unik), Join Keluarga, dan Pairing Device Raspberry Pi ke Keluarga.
* `[x]` **API-03: Endpoint Ingesti IoT Edge & Riwayat Insiden (`app/api/edge.py`)**
  * Buat endpoint `POST /api/v1/edge/heartbeat` (update posisi & status terakhir di tabel `devices`) dan `POST /api/v1/edge/incidents` (simpan log kantuk ke tabel `fatigue_incidents`) dengan autentikasi `X-Device-API-Key`.
* `[x]` **API-04: Real-time WebSocket Broadcaster & FCM Notifier (`app/api/ws.py`, `app/services/fcm_notifier.py`)**
  * Buat channel WebSocket `/ws/families/{family_id}` yang langsung meneruskan update lokasi & status kantuk ke aplikasi Flutter secara *real-time*, ditambah pengiriman Push Notification FCM saat `CRITICAL_DROWSY`.

---

## Epik 4: Sinkronisasi Edge ke API & Offline Resilience (`winfams-edge`)
*Tujuan: Memastikan data lokasi dan insiden kantuk dari Raspberry Pi selalu sampai ke server SQL meskipun sinyal internet di jalan tidak stabil.*

* `[x]` **SYNC-01: Local SQLite Offline Queue (`services/local_cache.py`)**
  * Buat penyimpanan SQLite lokal di Raspberry Pi untuk menampung antrean `IncidentPayload` saat tidak ada koneksi internet.
* `[x]` **SYNC-02: Async API Client & Background Sync Worker (`services/api_client.py`)**
  * Buat worker thread di Raspberry Pi yang mengirimkan `HeartbeatPayload` setiap 10 detik dan `IncidentPayload` seketika saat terjadi insiden ke FastAPI Backend, serta otomatis menguras (*flush*) isi SQLite saat internet kembali tersambung.

---

## Epik 5: Aplikasi Mobile Flutter - Auth & Live Family Monitoring (`winfams-mobile`)
*Tujuan: Membangun aplikasi mobile WinFams untuk memantau posisi dan kondisi pengemudi secara langsung.*

* `[x]` **MOB-01: Inisialisasi Proyek Flutter, Tema & Arsitektur Riverpod**
  * Setup folder `lib/core/` dan `lib/features/`, konfigurasi Dio HTTP Client, tema warna keselamatan, dan model data Dart (`DeviceStatus`, `FatigueIncident`, `FamilyOverview`).
* `[x]` **MOB-02: Autentikasi, Grup Keluarga & Pairing Alat (`features/auth/`)**
  * Buat halaman Login, Register, Buat/Gabung Grup Keluarga dengan `invite_code`, dan input `device_uid` Raspberry Pi 4.
* `[x]` **MOB-03: Live Family Map Dashboard via WebSocket (`features/live_map/`)**
  * Integrasikan peta (`flutter_map` / OpenStreetMap) yang terhubung ke WebSocket `/ws/families/{family_id}`.
  * Tampilkan pin mobil yang bergerak *real-time*, kecepatan ($km/h$), indikator status (`DRIVING`, `WARNING_FATIGUE`, `CRITICAL_DROWSY`), dan kartu info anggota keluarga.

---

## Epik 6: Notifikasi Darurat & Fitur Keselamatan Keluarga (`winfams-mobile`)
*Tujuan: Memberikan peringatan darurat instan dan rekomendasi tempat istirahat bagi keluarga.*

* `[x]` **MOB-04: High-Priority Push Notification & Emergency Alert Screen (`features/alerts/`)**
  * Integrasikan penerima notifikasi darurat ketika pengemudi mengalami `CRITICAL_DROWSY`, lengkap dengan alarm di HP keluarga dan tombol cepat **"Hubungi Pengemudi"**.
* `[x]` **MOB-05: Riwayat Perjalanan & Titik Insiden (`features/alerts/`)**
  * Buat halaman daftar riwayat insiden kantuk dari database SQL beserta tampilan titik lokasinya di peta.
* `[x]` **MOB-06: Smart Rest-Stop Finder (`features/family_hub/`)**
  * Buat fitur rekomendasi *Rest Area* / SPBU terdekat dari titik koordinat pengemudi saat status `WARNING_FATIGUE` aktif untuk dibagikan ke pengemudi.
