"""HTML and CSS dashboard template for WinFams Edge live web monitor."""

DASHBOARD_HTML: str = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>WinFams Edge Driver Monitor</title>
  <style>
    :root {
      --bg: #0b0f19;
      --card-bg: #151d30;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --accent: #3b82f6;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --border: #232f48;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding: 16px; min-height: 100vh; }
    .header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
    .title-group { display: flex; align-items: center; gap: 12px; }
    .logo-badge { background: #1e3a8a; color: #60a5fa; font-weight: 700; padding: 6px 12px; border-radius: 8px; font-size: 14px; letter-spacing: 1px; }
    h1 { font-size: 20px; font-weight: 700; }
    .live-indicator { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--success); font-weight: 600; }
    .dot { width: 10px; height: 10px; background: var(--success); border-radius: 50%; box-shadow: 0 0 10px var(--success); animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } 100% { opacity: 1; transform: scale(1); } }
    .grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 20px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 16px; overflow: hidden; }
    .video-container { position: relative; width: 100%; border-radius: 8px; overflow: hidden; background: #000; aspect-ratio: 4/3; display: flex; align-items: center; justify-content: center; }
    .video-container img { width: 100%; height: 100%; object-fit: contain; }
    .card-title { font-size: 14px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 14px; }
    .metrics-col { display: flex; flex-direction: column; gap: 16px; }
    .status-banner { padding: 16px; border-radius: 10px; text-align: center; font-size: 22px; font-weight: 800; letter-spacing: 1px; transition: all 0.3s; }
    .status-normal { background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid var(--success); }
    .status-warning { background: rgba(245, 158, 11, 0.2); color: var(--warning); border: 1px solid var(--warning); animation: pulse 1s infinite; }
    .status-critical { background: rgba(239, 68, 68, 0.25); color: var(--danger); border: 2px solid var(--danger); box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); animation: pulse 0.5s infinite; }
    .gauge-group { display: flex; flex-direction: column; gap: 8px; margin-top: 6px; }
    .gauge-label { display: flex; justify-content: space-between; font-size: 13px; font-weight: 500; }
    .gauge-bar-bg { width: 100%; height: 12px; background: #1f293d; border-radius: 6px; overflow: hidden; position: relative; }
    .gauge-bar-fill { height: 100%; width: 0%; border-radius: 6px; transition: width 0.2s, background-color 0.2s; }
    .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
    .info-box { background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border); border-radius: 8px; padding: 10px; }
    .info-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; }
    .info-val { font-size: 15px; font-weight: 700; margin-top: 2px; }
  </style>
</head>
<body>
  <div class="header">
    <div class="title-group">
      <span class="logo-badge">WINFAMS EDGE</span>
      <h1>Driver Safety Live Cockpit</h1>
    </div>
    <div class="live-indicator"><span class="dot"></span> LIVE MONITOR</div>
  </div>

  <div class="grid">
    <div class="card">
      <div class="card-title">Live In-Cabin Camera Stream</div>
      <div class="video-container">
        <img src="/video_feed" alt="Menghubungkan ke Kamera Edge...">
      </div>
    </div>

    <div class="metrics-col">
      <div class="card">
        <div class="card-title">Kondisi Pengemudi</div>
        <div id="status-banner" class="status-banner status-normal">NORMAL (ALERT)</div>
      </div>

      <div class="card">
        <div class="card-title">Analisis Kelelahan (MediaPipe AI)</div>
        <div class="gauge-group">
          <div class="gauge-label">
            <span>Tingkat Pejaman Mata (Drowsy)</span>
            <span id="drowsy-val" style="font-weight:700">0.00</span>
          </div>
          <div class="gauge-bar-bg">
            <div id="drowsy-fill" class="gauge-bar-fill" style="background:var(--success)"></div>
          </div>
        </div>
        <div class="gauge-group" style="margin-top:14px">
          <div class="gauge-label">
            <span>Bukaan Mulut / Menguap (Yawn)</span>
            <span id="yawn-val" style="font-weight:700">0.00</span>
          </div>
          <div class="gauge-bar-bg">
            <div id="yawn-fill" class="gauge-bar-fill" style="background:var(--accent)"></div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Telemetri Kendaraan & Sistem</div>
        <div class="info-grid">
          <div class="info-box"><div class="info-label">Kecepatan</div><div id="speed-val" class="info-val">0 km/h</div></div>
          <div class="info-box"><div class="info-label">Alarm Buzzer</div><div id="buzzer-val" class="info-val" style="color:var(--success)">IDLE</div></div>
          <div class="info-box"><div class="info-label">Koordinat GPS</div><div id="gps-val" class="info-val">- / -</div></div>
          <div class="info-box"><div class="info-label">Perangkat</div><div id="device-val" class="info-val">pi4_car_01</div></div>
        </div>
      </div>
    </div>
  </div>

  <script>
    async function updateStatus() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) return;
        const d = await res.json();
        
        const banner = document.getElementById('status-banner');
        banner.className = 'status-banner';
        if (d.state === 'CRITICAL_DROWSY') {
          banner.innerText = '🚨 BAHAYA: MICROSLEEP!';
          banner.classList.add('status-critical');
        } else if (d.state === 'WARNING_FATIGUE') {
          banner.innerText = '⚠️ PERINGATAN: MENGUAP';
          banner.classList.add('status-warning');
        } else {
          banner.innerText = '🛡️ NORMAL (FOKUS)';
          banner.classList.add('status-normal');
        }

        const dScore = Math.min(100, Math.round((d.drowsy_confidence || 0) * 100));
        document.getElementById('drowsy-val').innerText = (d.drowsy_confidence || 0).toFixed(2);
        const dFill = document.getElementById('drowsy-fill');
        dFill.style.width = dScore + '%';
        dFill.style.backgroundColor = dScore >= 55 ? 'var(--danger)' : 'var(--success)';

        const yScore = Math.min(100, Math.round((d.yawn_confidence || 0) * 100));
        document.getElementById('yawn-val').innerText = (d.yawn_confidence || 0).toFixed(2);
        const yFill = document.getElementById('yawn-fill');
        yFill.style.width = yScore + '%';
        yFill.style.backgroundColor = yScore >= 60 ? 'var(--warning)' : 'var(--accent)';

        if (d.location) {
          const spd = d.location.speed_kmh ? d.location.speed_kmh.toFixed(1) : 0;
          document.getElementById('speed-val').innerText = spd + ' km/h';
          if (d.location.lat && d.location.lng) {
            document.getElementById('gps-val').innerText = d.location.lat.toFixed(4) + ', ' + d.location.lng.toFixed(4);
          }
        }
        if (d.buzzer_active) {
          document.getElementById('buzzer-val').innerText = 'ALARM BEEP';
          document.getElementById('buzzer-val').style.color = 'var(--danger)';
        } else {
          document.getElementById('buzzer-val').innerText = 'IDLE';
          document.getElementById('buzzer-val').style.color = 'var(--success)';
        }
      } catch (err) {}
    }
    setInterval(updateStatus, 400);
  </script>
</body>
</html>
"""

