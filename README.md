# SystemLens

SystemLens is a production-grade local performance and reliability companion that turns any laptop or mobile-accessible device into a real-time observability dashboard. It monitors CPU, memory, disk, network, battery, and top processes, detects anomalies, and provides actionable recommendations. All data stays on the device by default.

By default, SystemLens now launches as a native desktop app on your device. It still includes a local server mode for advanced users, but the normal experience is a local app window that runs entirely on the device.

## Highlights
- Local-first monitoring with a secure local SQLite store
- Real-time dashboard with live streaming updates
- Anomaly detection using robust statistics and heuristics
- Actionable recommendations for performance issues
- Mobile-friendly UI accessible from the same network

## Quick Start

### 1) Install
```
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

### 2) Run SystemLens as a local app
```
python -m systemlens
```

This opens a native SystemLens window on your device. No browser workflow is required.

### 3) Run server mode instead
```
python -m systemlens run --host 127.0.0.1 --port 8080
```

Use this only if you want browser/network access.

To access on a phone in the same network:
```
python -m systemlens run --host 0.0.0.0 --port 8080
```
Then open `http://<your-laptop-ip>:8080` on your phone.

## Features
- Live metrics: CPU, memory, disk, network, battery
- Top processes by CPU and memory
- Real-time anomaly alerts with recommendations
- History timeline with trends
- Local data retention and cleanup
- GPU and thermal telemetry (best-effort)
- Battery drain modeling
- Role-based access and optional HTTPS
- Export to CSV/JSON and reports
- One-click fix workflows (admin)

## Architecture
- Agent: collects metrics and publishes updates
- Storage: local SQLite with retention
- Detection: anomaly engine with seasonal baselines and per-app thresholds
- API: FastAPI with SSE streaming and security
- UI: responsive dashboard plus native desktop shell

## Security & trust
Enable auth for LAN usage:
```
set SYSTEMLENS_AUTH_ENABLED=true
set SYSTEMLENS_ADMIN_TOKEN=your-admin-token
set SYSTEMLENS_VIEWER_TOKEN=your-viewer-token
```

For HTTPS, generate a self-signed cert:
```
./scripts/generate_cert.ps1
```
Then configure:
```
set SYSTEMLENS_SSL_CERT_PATH=cert.pem
set SYSTEMLENS_SSL_KEY_PATH=key.pem
```

## Privacy
SystemLens runs locally. No data leaves the device unless you explicitly configure remote storage.

## Notes
- GPU metrics are best-effort and may be unavailable on some systems.
- Battery data is only available on laptops.

## Packaging & services
See [docs/packaging.md](docs/packaging.md) for MSI/DMG builds and service setup.
