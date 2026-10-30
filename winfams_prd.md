# Product Requirements Document (PRD): WinFams

**Sistem Deteksi Kelelahan Pengemudi (IoT Edge) & Pemantauan Keselamatan Keluarga Terintegrasi**

## 1. Ringkasan Eksekutif & Visi Produk

* **Nama Produk:** WinFams (Winners Family Safety / Window to Family Safety)
* **Visi:** Menurunkan risiko kecelakaan lalu lintas akibat *microsleep* atau kelelahan melalui pemantauan *real-time* di dalam kabin kendaraan (Edge AI), sekaligus memberikan ketenangan pikiran bagi anggota keluarga di rumah melalui pemantauan lokasi dan notifikasi darurat instan.
* **Tujuan Dokumen:** Menjadi *Single Source of Truth* (SSOT) yang terhubung dengan `GEMINI.md` dan `backlog.md` untuk proses *vibe coding* agar menghasilkan kode berstandar produksi, modular, bersih (*clean architecture*), tanpa *AI slop* dan *spaghetti code*.

---

## 2. Arsitektur Sistem & Tech Stack (3-Pillar Architecture)

### A. Edge Device (`winfams-edge` - Raspberry Pi 4)
* **Hardware:** Raspberry Pi 4 (RAM minimal 4GB), USB Webcam (720p @ 30fps, disarankan Night Vision/IR), Modul GPS (U-blox NEO-6M/8M via UART/Serial), Active Buzzer 5V (via GPIO).
* **OS & Runtime:** Raspberry Pi OS Lite (64-bit), Python 3.10+.
* **Pre-trained Computer Vision Model (Tanpa Buat Rumus Geometri Manual):**
  1. **Opsi A (Default - Paling Ringan):** `MediaPipe Face Landmarker` (`face_landmarker.task`) dengan fitur **`output_face_blendshapes=True`**. Mengambil skor bawaan ($0.0 - 1.0$) untuk `eyeBlinkLeft`, `eyeBlinkRight` ($> 0.55$ = Mata tertutup) dan `jawOpen` ($> 0.60$ = Menguap).
  2. **Opsi B (Object Detection):** Model **YOLOv8n / YOLOv11n Drowsiness Detection** dalam format **NCNN** atau **TFLite (INT8)**.
* **Supporting Libraries:** `opencv-python`, `mediapipe` / `ultralytics`, `gpiozero`, `pyserial`, `pynmea2`, `httpx` (async HTTP client), `sqlite3` (offline buffer).

### B. Backend REST API & Database (`winfams-api` - Server/VPS)
* **Framework:** **FastAPI (Python 3.10+)** — Satu ekosistem bahasa dengan Edge AI, mendukung *asynchronous I/O*, WebSocket bawaan, dan dokumentasi OpenAPI/Swagger otomatis.
* **Database Utama (SQL):** **PostgreSQL** atau **MySQL** menggunakan **SQLAlchemy 2.0 (ORM)** + **Alembic** (Database Migration) + **Pydantic v2** (Validasi Schema).
* **Real-Time & Push Notification:**
  * **FastAPI WebSockets:** Memancarkan (*broadcast*) koordinat GPS dan status kantuk langsung ke aplikasi Flutter anggota keluarga secara *real-time*.
  * **Firebase Cloud Messaging (FCM):** Hanya digunakan sebagai layanan pengirim *Push Notification* prioritas tinggi saat insiden `CRITICAL_DROWSY` masuk ke API.

### C. Aplikasi Mobile (`winfams-mobile` - Smartphone Keluarga)
* **Framework:** Flutter (Dart 3.x).
* **State Management:** `Flutter Riverpod` (`Notifier` / `AsyncNotifier`).
* **Networking:** `dio` (REST API client) & `web_socket_channel` (Live Map Stream).
* **Peta & Geospasial:** `flutter_map` (OpenStreetMap - Gratis tanpa perlu kartu kredit) atau `google_maps_flutter`.

---

## 3. Desain Database Relasional (SQL Schema / ERD)

Database terdiri dari **5 tabel inti** dengan relasi *Foreign Key* yang ketat:

### 1. Tabel `users`
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `UUID / BIGINT` (PK) | Primary Key |
| `name` | `VARCHAR(100)` | Nama lengkap pengguna |
| `email` | `VARCHAR(120)` (UNIQUE) | Email untuk login |
| `password_hash` | `VARCHAR(255)` | Password terenkripsi (Bcrypt) |
| `phone_number` | `VARCHAR(20)` | Nomor telepon darurat |
| `fcm_token` | `VARCHAR(255)` (NULLABLE) | Token perangkat untuk Push Notification darurat |
| `created_at` | `TIMESTAMP` | Waktu pembuatan akun |

### 2. Tabel `families`
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `UUID / BIGINT` (PK) | Primary Key |
| `name` | `VARCHAR(100)` | Nama grup keluarga (misal: "Keluarga Budi") |
| `invite_code` | `VARCHAR(12)` (UNIQUE) | Kode unik 6-8 karakter untuk bergabung ke keluarga |
| `created_by` | `FK -> users.id` | Pembuat grup keluarga |
| `created_at` | `TIMESTAMP` | Waktu pembuatan grup |

### 3. Tabel `family_members` (Pivot Table)
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `BIGINT` (PK) | Primary Key |
| `family_id` | `FK -> families.id` | Relasi ke grup keluarga |
| `user_id` | `FK -> users.id` | Relasi ke pengguna |
| `role` | `ENUM('DRIVER', 'MONITOR', 'ADMIN')` | Peran di dalam keluarga |
| `joined_at` | `TIMESTAMP` | Waktu bergabung |

### 4. Tabel `devices` (State Terakhir Kendaraan / Raspberry Pi 4)
*Catatan Arsitektur: Menyimpan koordinat terakhir langsung di tabel ini membuat query Live Map sangat cepat tanpa perlu melakukan scan tabel log.*
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `BIGINT` (PK) | Primary Key |
| `device_uid` | `VARCHAR(64)` (UNIQUE) | Serial ID unik Raspberry Pi (misal: `pi4_car_01`) |
| `api_key_hash` | `VARCHAR(255)` | Token otorisasi khusus perangkat IoT |
| `family_id` | `FK -> families.id` | Grup keluarga pemilik alat |
| `active_driver_id` | `FK -> users.id` (NULLABLE) | Pengemudi yang sedang aktif membawa mobil |
| `vehicle_name` | `VARCHAR(100)` | Nama kendaraan (misal: "Innova Hitam - B 1234 XYZ") |
| `is_online` | `BOOLEAN` | Status koneksi alat |
| `current_state` | `ENUM('IDLE', 'DRIVING', 'WARNING_FATIGUE', 'CRITICAL_DROWSY')` | Status kesadaran pengemudi saat ini |
| `last_lat` | `DECIMAL(10, 7)` (NULLABLE) | Latitude terakhir dari GPS |
| `last_lng` | `DECIMAL(10, 7)` (NULLABLE) | Longitude terakhir dari GPS |
| `last_speed_kmh` | `FLOAT` (DEFAULT 0) | Kecepatan terakhir ($km/h$) |
| `last_seen_at` | `TIMESTAMP` (NULLABLE) | Waktu *heartbeat* terakhir dari Pi 4 |

### 5. Tabel `fatigue_incidents` (Riwayat Insiden Kantuk & Menguap)
| Kolom | Tipe Data | Keterangan |
| :--- | :--- | :--- |
| `id` | `BIGINT` (PK) | Primary Key |
| `device_id` | `FK -> devices.id` | Alat yang mendeteksi |
| `driver_id` | `FK -> users.id` (NULLABLE) | Pengemudi saat kejadian |
| `family_id` | `FK -> families.id` | Grup keluarga terkait |
| `incident_type` | `ENUM('WARNING_FATIGUE', 'CRITICAL_DROWSY')` | Jenis peringatan |
| `confidence_score` | `FLOAT` | Skor keyakinan model CV ($0.0 - 1.0$) |
| `duration_seconds` | `FLOAT` | Durasi mata tertutup / menguap dalam detik |
| `lat` | `DECIMAL(10, 7)` (NULLABLE) | Titik Latitude lokasi kejadian |
| `lng` | `DECIMAL(10, 7)` (NULLABLE) | Titik Longitude lokasi kejadian |
| `speed_kmh` | `FLOAT` | Kecepatan kendaraan saat kejadian |
| `recorded_at` | `TIMESTAMP` | Waktu kejadian asli di Raspberry Pi (penting untuk offline sync) |

---

## 4. Spesifikasi Endpoint REST API & WebSocket (`winfams-api`)

### A. Autentikasi & Keluarga (Diakses oleh Flutter)
* `POST /api/v1/auth/register` — Registrasi pengguna baru.
* `POST /api/v1/auth/login` — Login & dapatkan JWT Access Token.
* `PUT /api/v1/auth/fcm-token` — Update token FCM HP untuk menerima notifikasi darurat.
* `POST /api/v1/families` — Buat grup keluarga baru (otomatis *generate* `invite_code`).
* `POST /api/v1/families/join` — Gabung ke keluarga menggunakan `invite_code`.
* `GET /api/v1/families/{family_id}/overview` — Ambil daftar anggota keluarga, daftar kendaraan (`devices`), dan posisi terakhirnya.

### B. IoT Edge Telemetry & Insiden (Diakses oleh Raspberry Pi 4 menggunakan `X-Device-API-Key`)
* `POST /api/v1/edge/heartbeat` — Dikirim setiap 5–10 detik oleh Pi 4.
  * **Fungsi:** Mengupdate `last_lat`, `last_lng`, `last_speed_kmh`, `current_state`, dan `last_seen_at` pada tabel `devices`, lalu memancarkannya ke WebSocket grup keluarga.
* `POST /api/v1/edge/incidents` — Dikirim **hanya saat terjadi insiden** (`WARNING_FATIGUE` atau `CRITICAL_DROWSY`) atau saat sinkronisasi data dari SQLite offline queue.
  * **Fungsi:** Menyimpan baris baru ke tabel `fatigue_incidents`, mengupdate status `devices`, memancarkan event darurat ke WebSocket, dan menembak **FCM Push Notification** ke semua anggota keluarga.

### C. Monitoring & Riwayat (Diakses oleh Flutter)
* `GET /api/v1/families/{family_id}/incidents` — Daftar riwayat insiden kantuk (mendukung filter tanggal & pengemudi).
* `GET /api/v1/rest-stops/nearby?lat={lat}&lng={lng}` — Mengembalikan daftar *Rest Area* / SPBU terdekat (via Overpass API / OpenStreetMap) saat pengemudi terdeteksi lelah.
* `WS /ws/families/{family_id}?token={jwt_token}` — Koneksi WebSocket *real-time* untuk menggerakkan pin mobil di peta Flutter tanpa perlu *polling* HTTP berulang-ulang.

---

## 5. Kontrak Data (JSON Payload Schemas)

### A. `HeartbeatPayload` (`POST /api/v1/edge/heartbeat`)
```json
{
  "device_uid": "pi4_car_01",
  "state": "DRIVING",
  "drowsy_confidence": 0.12,
  "yawn_confidence": 0.05,
  "location": {
    "lat": -1.265386,
    "lng": 116.831200,
    "speed_kmh": 64.5
  },
  "timestamp": 1730334600
}
```

### B. `IncidentPayload` (`POST /api/v1/edge/incidents`)
```json
{
  "device_uid": "pi4_car_01",
  "incident_type": "CRITICAL_DROWSY",
  "confidence_score": 0.88,
  "duration_seconds": 2.1,
  "location": {
    "lat": -1.265386,
    "lng": 116.831200,
    "speed_kmh": 72.0
  },
  "recorded_at": 1730334605
}
```

---

## 6. Struktur Folder & Arsitektur Kode (Anti-Spaghetti)

```text
winfams/
├── GEMINI.md                     # Aturan sistem AI & coding guardrails
├── winfams_prd.md                # Dokumen spesifikasi utama (SSOT)
├── backlog.md                    # Daftar antrean tugas vibe coding
│
├── winfams-edge/                 # [PILAR 1] Kode Python untuk Raspberry Pi 4
│   ├── config/
│   │   └── settings.py           # Konfigurasi threshold, URL API, API Key, pin GPIO
│   ├── models_weights/           # File face_landmarker.task atau yolov8n_ncnn_model
│   ├── core/
│   │   ├── camera_stream.py      # Thread khusus baca frame webcam
│   │   ├── detector.py           # Wrapper Pre-trained Model (MediaPipe / YOLO)
│   │   └── state_machine.py      # Penentu status: NORMAL, WARNING, CRITICAL
│   ├── hardware/
│   │   ├── buzzer_controller.py  # Kontrol GPIO Buzzer non-blocking + Mock Mode
│   │   └── gps_reader.py         # Thread khusus baca serial NMEA GPS + Mock Mode
│   ├── services/
│   │   ├── api_client.py         # Pengirim HTTP async ke FastAPI Backend
│   │   └── local_cache.py        # SQLite buffer saat internet di jalan terputus
│   ├── schemas/
│   │   └── payload.py            # Dataclasses untuk Heartbeat & Incident
│   ├── tests/                    # Unit tests untuk state machine & cache
│   ├── main.py                   # Orchestrator utama di Raspberry Pi
│   └── requirements.txt
│
├── winfams-api/                  # [PILAR 2] Backend FastAPI + SQL Database
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py         # Env settings (DB_URL, JWT_SECRET)
│   │   │   ├── database.py       # SQLAlchemy session & engine setup
│   │   │   └── security.py       # JWT auth & Device API Key verification
│   │   ├── models/               # SQLAlchemy ORM Tables (user, family, device, incident)
│   │   ├── schemas/              # Pydantic Request/Response Schemas
│   │   ├── api/
│   │   │   ├── auth.py           # Endpoint login & register
│   │   │   ├── families.py       # Endpoint grup keluarga & daftar kendaraan
│   │   │   ├── edge.py           # Endpoint penerima data dari Raspberry Pi 4
│   │   │   └── ws.py             # WebSocket broadcaster untuk Live Map Flutter
│   │   ├── services/
│   │   │   └── fcm_notifier.py   # Pengirim Push Notification darurat
│   │   └── main.py               # Entrypoint FastAPI app
│   ├── migrations/               # Alembic SQL migrations
│   ├── tests/                    # Pytest untuk endpoint API
│   └── requirements.txt
│
└── winfams-mobile/               # [PILAR 3] Aplikasi Mobile Flutter
    ├── lib/
    │   ├── core/
    │   │   ├── network/          # Dio client & WebSocket manager
    │   │   ├── theme/            # Styling & warna aplikasi
    │   │   └── constants/        # Base URL API & konstanta
    │   ├── features/
    │   │   ├── auth/             # Login, Register, Join Family
    │   │   ├── live_map/         # Peta keluarga real-time & status pengemudi
    │   │   ├── alerts/           # Layar darurat kantuk & riwayat insiden
    │   │   └── family_hub/       # Info anggota keluarga & Smart Rest-Stop Finder
    │   └── main.dart
    └── pubspec.yaml
```