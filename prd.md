# Product Requirements Document (PRD): WinFams

**Sistem Deteksi Kelelahan Pengemudi (IoT Edge) & Pemantauan Keselamatan Keluarga Terintegrasi**

## 1. Ringkasan Eksekutif & Visi Produk

* **Nama Produk:** WinFams (Winners Family Safety / Window to Family Safety)
* **Visi:** Menurunkan risiko kecelakaan lalu lintas akibat *microsleep* atau kelelahan melalui pemantauan *real-time* di dalam kabin kendaraan (Edge AI), sekaligus memberikan ketenangan pikiran bagi anggota keluarga di rumah melalui pemantauan lokasi dan notifikasi darurat instan.
* **Tujuan Dokumen:** Menjadi *Single Source of Truth* (SSOT) yang terhubung dengan `GEMINI.md` dan `backlog.md` untuk proses *vibe coding* agar menghasilkan kode berstandar produksi, modular, bersih (*clean architecture*), tanpa *AI slop* dan *spaghetti code*.

## 2. Arsitektur Sistem & Tech Stack (Strict Spec)

### A. Edge Device (In-Car Unit - Raspberry Pi 4)

* **Hardware:** Raspberry Pi 4 (RAM minimal 4GB), USB Webcam (720p @ 30fps, disarankan Night Vision/IR), Modul GPS (U-blox NEO-6M/8M via UART/Serial), Active Buzzer 5V (via GPIO).
* **OS & Runtime:** Raspberry Pi OS Lite (64-bit), Python 3.10+.
* **Pre-trained Computer Vision Model (Tanpa Buat Rumus Manual):**
  Pilih salah satu dari dua opsi model *off-the-shelf* berikut (diatur lewat `settings.py`):
  1. **Opsi A (Direkomendasikan - Paling Ringan & Tanpa Training):** `MediaPipe Face Landmarker` (`face_landmarker.task`) dengan fitur **`output_face_blendshapes=True`**. Model ini sudah memiliki klasifikasi skor bawaan (*out-of-the-box* dari $0.0$ hingga $1.0$) untuk:
     * `eyeBlinkLeft` & `eyeBlinkRight` (Skor $> 0.55$ = Mata tertutup).
     * `jawOpen` (Skor $> 0.60$ = Menguap).
  2. **Opsi B (Object Detection Pre-trained):** Model **YOLOv8n / YOLOv11n Drowsiness Detection** dari Roboflow Universe (kelas: `awake`, `drowsy`, `yawn`, `closed_eye`) yang diekspor ke format **NCNN** atau **TFLite (INT8)** menggunakan library `ultralytics` agar berjalan $\ge 15\text{ FPS}$ di CPU ARM Raspberry Pi 4.
* **Supporting Libraries:**
  * `OpenCV` (`cv2`) – Akuisisi frame kamera secara *multithreaded*.
  * `gpiozero` – Kontrol aktuator buzzer secara non-blocking.
  * `pyserial` & `pynmea2` – Parsing data koordinat mentah NMEA dari modul GPS.

### B. Cloud Backend & Real-Time Broker

* **Platform:** Firebase (Firestore + Realtime Database + Cloud Messaging / FCM).
* **Protokol Komunikasi:**
  * Edge ke Cloud: Firebase Admin SDK / REST + Offline SQLite Queue (jika kendaraan melewati area susah sinyal).
  * Cloud ke Mobile: FCM untuk *High-Priority Alert* & Realtime Database Stream untuk pergerakan pin peta.

### C. Aplikasi Mobile (WinFams App)

* **Framework:** Flutter (Dart 3.x).
* **State Management:** `Flutter Riverpod` (`riverpod_annotation` & `freezed`).
* **Peta & Geospasial:** `flutter_map` (OpenStreetMap) atau `google_maps_flutter`.

## 3. Spesifikasi Fitur Utama

### 3.1. Edge AI: Deteksi Kantuk Berbasis Pre-trained Model (Pi 4)

1. **Deteksi Mata Tertutup (*Microsleep*):**
   * Menggunakan output langsung dari model CV (`eyeBlinkLeft/Right > 0.55` pada MediaPipe Blendshapes ATAU class `closed_eye`/`drowsy` dengan `confidence > 0.65` pada YOLO NCNN).
   * **Trigger:** Jika kondisi terdeteksi secara kontinu selama $\ge 1.5\text{ detik}$, sistem memicu status `CRITICAL_DROWSY`.
2. **Deteksi Menguap (*Yawning / Early Fatigue*):**
   * Menggunakan output `jawOpen > 0.60` (MediaPipe) ATAU class `yawn` (YOLO).
   * **Trigger:** Jika terdeteksi selama $\ge 2.5\text{ detik}$ sebanyak 3 kali dalam rentang 10 menit, sistem memicu status `WARNING_FATIGUE`.
3. **Respon Lokal Instan (Zero-Latency):**
   * Saat `CRITICAL_DROWSY` terpicu, Buzzer langsung berbunyi di thread terpisah tanpa menghentikan pembacaan kamera.
4. **Telemetry & Offline Sync:**
   * Mengirimkan koordinat GPS ($Latitude, Longitude, Speed$) setiap 10 detik saat kendaraan bergerak ($Speed > 5\text{ km/h}$).
   * Menyimpan log insiden ke SQLite lokal jika offline, dan sinkronisasi otomatis saat kembali online.

### 3.2. Mobile App: Family Monitoring & Safety Features (Flutter)

1. **Live Family Map Dashboard:** Posisi *real-time* kendaraan anggota keluarga, indikator kecepatan, status perangkat (Online/Offline/Driving), dan indikator kesegaran pengemudi.
2. **Instant Emergency Alert:** Notifikasi prioritas tinggi saat `CRITICAL_DROWSY` disertai titik lokasi kejadian dan tombol cepat **"Hubungi Pengemudi"**.
3. **Driver Safety Score & Trip History:** Riwayat rute perjalanan dan titik lokasi insiden kantuk.
4. **Smart Rest-Stop Recommendation:** Rekomendasi *Rest Area* atau SPBU terdekat saat status `WARNING_FATIGUE` muncul.
5. **Geofencing / Safe Zones:** Notifikasi otomatis saat kendaraan tiba atau berangkat dari Rumah/Kantor/Sekolah.

## 4. Kontrak Data (Data Models / JSON Schema)

### A. `DeviceStatus` (Realtime Node: `/devices/{device_id}/status`)

```json
{
  "device_id": "pi4_car_01",
  "driver_uid": "user_123",
  "is_online": true,
  "state": "DRIVING",
  "drowsy_confidence": 0.12,
  "yawn_confidence": 0.05,
  "location": {
    "lat": -1.265386,
    "lng": 116.831200,
    "speed_kmh": 64.5,
    "heading": 180.0
  },
  "last_updated": 1730334600
}
```

### B. `FatigueIncident` (Collection: `incidents`)

```json
{
  "incident_id": "inc_987654",
  "device_id": "pi4_car_01",
  "driver_uid": "user_123",
  "family_group_id": "fam_001",
  "type": "CRITICAL_DROWSY",
  "confidence_score": 0.88,
  "duration_seconds": 2.1,
  "location": {
    "lat": -1.265386,
    "lng": 116.831200,
    "speed_kmh": 72.0
  },
  "timestamp": 1730334605,
  "resolved": false
}
```

## 5. Struktur Folder & Arsitektur Kode (Anti-Spaghetti)

### A. Struktur Proyek Raspberry Pi (`winfams-edge/`)

```text
winfams-edge/
├── config/
│   └── settings.py          # Konfigurasi threshold, path model (.task / NCNN), pin GPIO
├── models_weights/          # Tempat menyimpan file face_landmarker.task atau yolov8n_ncnn_model
├── core/
│   ├── camera_stream.py     # Thread khusus baca frame webcam
│   ├── detector.py          # Wrapper Pre-trained Model (MediaPipe Blendshapes / YOLO NCNN)
│   └── state_machine.py     # Penentu status: NORMAL, WARNING, atau CRITICAL berdasarkan durasi
├── hardware/
│   ├── buzzer_controller.py # Kontrol GPIO Buzzer non-blocking
│   └── gps_reader.py        # Thread khusus baca serial NMEA GPS
├── services/
│   ├── cloud_sync.py        # Pengiriman data ke Firebase
│   └── local_cache.py       # SQLite buffer saat offline
├── schemas/
│   └── payload.py           # Dataclasses untuk DeviceStatus & FatigueIncident
├── main.py                  # Orchestrator / Dependency Injection saja
└── requirements.txt
```

### B. Struktur Proyek Flutter (`winfams-mobile/`)

```text
lib/
├── core/
│   ├── constants/
│   ├── theme/
│   └── utils/
├── features/
│   ├── auth/
│   ├── live_map/
│   ├── alerts/
│   └── family_hub/
└── main.dart
```

## 6. Alur Kerja Vibe Coding dengan `GEMINI.md` dan `backlog.md`

1. Pastikan file `GEMINI.md`, `winfams_prd.md`, dan `backlog.md` berada di *root directory* proyek.
2. AI akan selalu membaca `GEMINI.md` sebagai instruksi utama, mengacu pada desain di `winfams_prd.md`, dan mengeksekusi tugas satu per satu sesuai urutan di `backlog.md`.