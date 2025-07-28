```
# Huawei LTE Signal Monitor

🛠️ **Just a quick tool made to adjust an LTE antenna for maximum signal and speed**.

This desktop GUI app connects to a Huawei LTE router and displays realtime signal data (RSRP, RSRQ, SINR), band info, and local tower metadata to help you align your antenna or diagnose connection quality.

## 📦 Features

- Realtime signal refresh (RSRP, RSRQ, SINR, EARFCN, band)
- Estimated yagi antenna spacing
- eNodeB and Sector display
- Local `towers.json` support for rich tower metadata
- Automatic tower discovery from Cell ID
- Auto-fallback if metadata is missing
- Offline, local-only — no internet dependency
- Customizable via `config.json`

---

## 🖥️ Requirements

- Python 3.7+
- `huawei-lte-api`
- `tkinter` (included with most Python installations)

---

## 🐍 Recommended: Use a Virtual Environment

Create and activate a Python virtual environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it (Linux/macOS)
source .venv/bin/activate

# Activate it (Windows)
.venv\Scripts\activate
```

Install dependencies using `requirements.txt`:

```bash
pip install -r requirements.txt
```

To deactivate the virtual environment:

```bash
deactivate
```

---

## ⚙️ Configuration

### `config.json`

Example:

```json
{
  "router_host": "http://192.168.8.1/",
  "username": "admin",
  "password": "admin123",
  "refresh_interval": 1
}
```

- `router_host`: Base URL to the router (without credentials)
- `username` / `password`: Router login
- `refresh_interval`: How often to poll signal info (in seconds)

---

### `towers.json`

Stores custom tower metadata by eNodeB + Sector key.

Example:

```json
{
  "162336_11": {
    "label": "Puskaru — Väimela, Loosu küla, Võru vald",
    "location": "Võru County, 65505, Estonia",
    "region": 2143,
    "mcc": 248,
    "mnc": 3,
    "bands": [1, 3, 20],
    "type": "MACRO",
    "first_seen": "2024-10-25",
    "last_seen": "2025-07-23",
    "cells": {
      "41558027": {
        "sector": 11,
        "band": 3,
        "earfcn": 1574,
        "rsrp": -87,
        "rsrq": -5,
        "snr": 21,
        "direction": "N (343°)",
        "bandwidth_mhz": 20
      }
    },
    "contributed_by": ["VeixES", "Lordami", "Mapitall"],
    "last_generated": "2025-07-23 10:48"
  }
}
```

- Tower key format: `"eNodeBID_SectorID"`
- On first detection of an unknown tower, a placeholder will be added automatically for manual editing.

---

## 🧠 How It Works

1. The app logs into your Huawei router using credentials from `config.json`.
2. It fetches live signal metrics every few seconds.
3. It extracts the eNodeB and sector from the Cell ID.
4. If a match exists in `towers.json`, tower and cell metadata are shown.
5. If not, it adds a new empty row to `towers.json` for user annotation.

---

## 🖼️ GUI Preview

- Signal metrics displayed with dynamic color coding:
  - 🟢 Good
  - 🟠 Fair
  - 🔴 Poor
- eNodeB and Sector shown at top
- Metadata shown below when available:
  - Location
  - Bands
  - Contributors
  - Cell-level metrics (RSRP, RSRQ, Direction, etc.)

---

## 🚀 Running the App

```bash
# (If using virtual environment, activate it first)
python hua_signal.py
```

Make sure `config.json` is in the same directory.

---

## 📁 File Structure

```
.
├── hua_signal.py          # Main app script
├── config.json            # Router credentials and polling config
├── towers.json            # Tower metadata (optional, autogrows)
├── requirements.txt       # Python dependencies
├── LICENSE                # MIT license
├── .gitignore             # Ignored files (e.g., .venv/)
└── README.md              # You're reading it
```

---

## 📚 Acknowledgements

This project uses the excellent [`huawei-lte-api`](https://github.com/Salamek/huawei-lte-api) Python library  
© [Jan Salamek](https://github.com/Salamek) – Licensed under [LGPL-3.0](https://www.gnu.org/licenses/lgpl-3.0.html)

> "Unofficial Huawei LTE router API implementation for Python"

Project link:  
🔗 https://github.com/Salamek/huawei-lte-api#readme

---

## 🧑‍💻 Author

Built by Magnus Jaaska  
Data gathered with help from [CellMapper.net](https://www.cellmapper.net/)

---

## 📜 License

MIT License
```
