-- =============================================================================
-- WinFams PostgreSQL Database Schema
-- Single Source of Truth (SSOT) based on winfams_prd.md
-- =============================================================================

-- Drop tables in reverse dependency order if resetting
DROP TABLE IF EXISTS fatigue_incidents CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS family_members CASCADE;
DROP TABLE IF EXISTS families CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- -----------------------------------------------------------------------------
-- 1. Tabel users: Akun pengguna, autentikasi, dan token push notification FCM
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) NOT NULL DEFAULT '',
    fcm_token VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);

-- -----------------------------------------------------------------------------
-- 2. Tabel families: Grup keluarga dan kode undangan
-- -----------------------------------------------------------------------------
CREATE TABLE families (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    invite_code VARCHAR(12) NOT NULL UNIQUE,
    created_by BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_families_invite_code ON families(invite_code);
CREATE INDEX idx_families_created_by ON families(created_by);

-- -----------------------------------------------------------------------------
-- 3. Tabel family_members: Pivot keanggotaan pengguna dalam grup keluarga & peran
-- -----------------------------------------------------------------------------
CREATE TABLE family_members (
    id BIGSERIAL PRIMARY KEY,
    family_id BIGINT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'MONITOR' CHECK (role IN ('DRIVER', 'MONITOR', 'ADMIN')),
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_family_members_user UNIQUE (family_id, user_id)
);

CREATE INDEX idx_family_members_family_id ON family_members(family_id);
CREATE INDEX idx_family_members_user_id ON family_members(user_id);

-- -----------------------------------------------------------------------------
-- 4. Tabel devices: Perangkat Raspberry Pi 4 & status telemetri terakhir
-- -----------------------------------------------------------------------------
CREATE TABLE devices (
    id BIGSERIAL PRIMARY KEY,
    device_uid VARCHAR(64) NOT NULL UNIQUE,
    api_key_hash VARCHAR(255) NOT NULL,
    family_id BIGINT NULL REFERENCES families(id) ON DELETE SET NULL,
    active_driver_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    vehicle_name VARCHAR(100) NOT NULL DEFAULT 'Kendaraan Keluarga',
    is_online BOOLEAN NOT NULL DEFAULT FALSE,
    current_state VARCHAR(32) NOT NULL DEFAULT 'IDLE' CHECK (current_state IN ('IDLE', 'DRIVING', 'WARNING_FATIGUE', 'CRITICAL_DROWSY')),
    last_lat DECIMAL(10, 7) NULL,
    last_lng DECIMAL(10, 7) NULL,
    last_speed_kmh DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    last_seen_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_devices_device_uid ON devices(device_uid);
CREATE INDEX idx_devices_family_id ON devices(family_id);
CREATE INDEX idx_devices_active_driver_id ON devices(active_driver_id);

-- -----------------------------------------------------------------------------
-- 5. Tabel fatigue_incidents: Riwayat deteksi kantuk & menguap pengemudi
-- -----------------------------------------------------------------------------
CREATE TABLE fatigue_incidents (
    id BIGSERIAL PRIMARY KEY,
    device_id BIGINT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    driver_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    family_id BIGINT NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    incident_type VARCHAR(32) NOT NULL CHECK (incident_type IN ('WARNING_FATIGUE', 'CRITICAL_DROWSY')),
    confidence_score DOUBLE PRECISION NOT NULL,
    duration_seconds DOUBLE PRECISION NOT NULL,
    lat DECIMAL(10, 7) NULL,
    lng DECIMAL(10, 7) NULL,
    speed_kmh DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    recorded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fatigue_incidents_device_id ON fatigue_incidents(device_id);
CREATE INDEX idx_fatigue_incidents_driver_id ON fatigue_incidents(driver_id);
CREATE INDEX idx_fatigue_incidents_family_id ON fatigue_incidents(family_id);
CREATE INDEX idx_fatigue_incidents_recorded_at ON fatigue_incidents(recorded_at);
