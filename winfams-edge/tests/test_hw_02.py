"""Unit tests for HW-02: GPS Serial Reader Thread."""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hardware.gps_reader import GPSReader
from schemas.payload import LocationData


def test_gps_reader_force_mock_initialization() -> None:
    """Test GPSReader initializes properly with mock fallback."""
    reader = GPSReader(
        force_mock=True,
        mock_lat=-1.265386,
        mock_lng=116.831200,
        mock_speed_kmh=45.0,
        mock_heading=180.0,
    )
    assert reader.is_mock is True
    assert reader.has_fix is True

    loc = reader.get_location()
    assert isinstance(loc, LocationData)
    assert loc.lat == -1.265386
    assert loc.lng == 116.831200
    assert loc.speed_kmh == 45.0
    assert loc.heading == 180.0
    reader.close()


def test_gps_reader_invalid_port_fallback() -> None:
    """Test GPSReader automatically falls back to mock when serial port is missing."""
    reader = GPSReader(port="/dev/non_existent_ttyUSB999", force_mock=False)
    assert reader.is_mock is True
    reader.close()


def test_gps_reader_parse_gga_valid() -> None:
    """Test parsing a valid $GPGGA NMEA sentence."""
    reader = GPSReader(force_mock=True)
    # Standard NMEA 0183 GGA sentence
    # Lat: 48 deg 07.038 min N = 48.1173
    # Lng: 11 deg 31.000 min E = 11.516667
    # Fix quality = 1 (GPS fix)
    sentence = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    success = reader.parse_nmea_sentence(sentence)

    assert success is True
    assert reader.has_fix is True
    loc = reader.get_location()
    assert loc.lat is not None and abs(loc.lat - 48.1173) < 0.001
    assert loc.lng is not None and abs(loc.lng - 11.516667) < 0.001
    reader.close()


def test_gps_reader_parse_gga_no_fix() -> None:
    """Test parsing $GPGGA when satellite fix is lost (quality = 0)."""
    reader = GPSReader(force_mock=True)
    # Fix quality = 0 (no fix), valid checksum *7E
    sentence = "$GPGGA,123519,4807.038,N,01131.000,E,0,00,99.9,545.4,M,46.9,M,,*7E"
    success = reader.parse_nmea_sentence(sentence)

    assert success is True
    assert reader.has_fix is False
    loc = reader.get_location()
    assert loc.lat is None
    assert loc.lng is None
    reader.close()


def test_gps_reader_parse_rmc_valid() -> None:
    """Test parsing a valid $GPRMC NMEA sentence with speed in knots converted to km/h."""
    reader = GPSReader(force_mock=True)
    # Status = A (valid)
    # Speed = 22.4 knots = 22.4 * 1.852 = 41.4848 km/h
    # Heading = 84.4 degrees
    sentence = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
    success = reader.parse_nmea_sentence(sentence)

    assert success is True
    assert reader.has_fix is True
    loc = reader.get_location()
    assert loc.lat is not None and abs(loc.lat - 48.1173) < 0.001
    assert loc.lng is not None and abs(loc.lng - 11.516667) < 0.001
    assert abs(loc.speed_kmh - 41.48) < 0.05
    assert loc.heading == 84.4
    reader.close()


def test_gps_reader_parse_rmc_void() -> None:
    """Test parsing $GPRMC with void status ('V') resets fix."""
    reader = GPSReader(force_mock=True)
    sentence = "$GPRMC,123519,V,,,,,,,230394,,,N*51"
    success = reader.parse_nmea_sentence(sentence)

    assert success is True
    assert reader.has_fix is False
    loc = reader.get_location()
    assert loc.lat is None
    assert loc.lng is None
    assert loc.speed_kmh == 0.0
    reader.close()


def test_gps_reader_parse_malformed() -> None:
    """Test parsing garbage or non-NMEA strings returns False gracefully."""
    reader = GPSReader(force_mock=True)
    assert reader.parse_nmea_sentence("NOT_AN_NMEA_SENTENCE") is False
    assert reader.parse_nmea_sentence("$GPGGA,CORRUPTED*FF") is False
    assert reader.parse_nmea_sentence("") is False
    reader.close()


def test_gps_reader_set_mock_location() -> None:
    """Test manually updating mock location."""
    reader = GPSReader(force_mock=True)
    reader.set_mock_location(lat=-6.2088, lng=106.8456, speed_kmh=80.0, heading=90.0)
    loc = reader.get_location()
    assert loc.lat == -6.2088
    assert loc.lng == 106.8456
    assert loc.speed_kmh == 80.0
    assert loc.heading == 90.0
    assert reader.has_fix is True
    reader.close()


def test_gps_reader_thread_lifecycle() -> None:
    """Test starting, running, and stopping background thread cleanly."""
    with GPSReader(force_mock=True) as reader:
        assert reader._worker_thread is not None
        assert reader._worker_thread.is_alive()
        time.sleep(0.1)

    assert reader._worker_thread is None
