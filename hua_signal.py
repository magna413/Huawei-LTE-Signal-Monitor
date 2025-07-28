import tkinter as tk
from huawei_lte_api.Client import Client
from huawei_lte_api.Connection import Connection
import threading
import time
import requests
import json
import os

# Load config
CONFIG_PATH = "config.json"
CONFIG = {
    "router_host": "http://192.168.8.1/",
    "username": "admin",
    "password": "admin123",
    "refresh_interval": 1

}
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        CONFIG.update(json.load(f))

TOWER_INFO_FILE = "towers.json"
tower_info = {}

# Load or initialize tower info
if os.path.exists(TOWER_INFO_FILE):
    with open(TOWER_INFO_FILE, "r") as f:
        tower_info = json.load(f)
else:
    with open(TOWER_INFO_FILE, "w") as f:
        json.dump({}, f, indent=2)

ROUTER_URL = CONFIG["router_host"]
USERNAME = CONFIG["username"]
PASSWORD = CONFIG["password"]
REFRESH_INTERVAL = CONFIG["refresh_interval"]

REFERENCE = {
    "rsrp": {"label": "RSRP (Signal Power)", "good": -80, "fair": -90, "unit": "dBm", "desc": "Good: >-80, Fair: >-90, Poor: <=-90"},
    "rsrq": {"label": "RSRQ (Signal Quality)", "good": -10, "fair": -14, "unit": "dB", "desc": "Good: >-10, Fair: >-14, Poor: <=-14"},
    "sinr": {"label": "SINR (Signal-to-Noise)", "good": 10, "fair": 0, "unit": "dB", "desc": "Good: >10, Fair: >0, Poor: <=0"},
}

def parse_dl_freq(earfcn_str):
    try:
        if "DL:" in earfcn_str:
            dl_val = int(earfcn_str.split("DL:")[1].split()[0])
            if 0 <= dl_val <= 599:
                return 2110 + 0.1 * (dl_val - 0), "1"
            elif 1200 <= dl_val <= 1949:
                return 1805 + 0.1 * (dl_val - 1200), "3"
            elif 2750 <= dl_val <= 3449:
                return 2620 + 0.1 * (dl_val - 2750), "7"
            elif 6150 <= dl_val <= 6449:
                return 791 + 0.1 * (dl_val - 6150), "20"
        return None, None
    except:
        return None, None

def fetch_signal():
    try:
        auth_url = ROUTER_URL.replace("http://", f"http://{USERNAME}:{PASSWORD}@")
        with Connection(auth_url) as connection:
            client = Client(connection)
            return client.device.signal()
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}


class SignalMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Huawei LTE Signal Monitor")
        self.root.geometry("600x500")
        self.labels = {}
        self.enb_id = None
        self.last_cell_id = None
        self.last_lac = None
        self.metadata_frame = tk.Frame(root)
        self.metadata_frame.pack(pady=5)
        self.metadata_labels = {}

        for key in ["rsrp", "rsrq", "sinr", "band", "cell_id", "earfcn", "band_freq", "yagi_spacing"]:
            frame = tk.Frame(root)
            frame.pack(pady=3)

            label_text = REFERENCE.get(key, {}).get("label", key.replace("_", " ").title())
            label = tk.Label(frame, text=f"{label_text}: ", font=("Arial", 13))
            label.pack(side="left")

            value_label = tk.Label(frame, text="-", font=("Arial", 13, "bold"))
            value_label.pack(side="left")
            self.labels[key] = value_label

            if key in REFERENCE:
                hint = REFERENCE[key]["desc"]
                ref_label = tk.Label(frame, text=f"({hint})", font=("Arial", 9), fg="gray")
                ref_label.pack(side="left")

        self.status_label = tk.Label(root, text="", fg="red", font=("Arial", 11))
        self.status_label.pack(pady=10)

        separator = tk.Label(root, text="\u2500" * 70, fg="gray")
        separator.pack(pady=5)

        tower_frame = tk.Frame(root)
        tower_frame.pack()

        self.tower_label = tk.Label(tower_frame, text="Tower: eNodeB - / Sector -", font=("Arial", 12))
        self.tower_label.pack()

        self.update_loop()

    def update_tower_info(self, cell_id):
        try:
            enb = int(cell_id) // 256
            sector = int(cell_id) % 256
            self.enb_id = enb
            tower_key = f"{enb}_{sector}"
            data = tower_info.get(tower_key)

            label_text = f"Tower: eNodeB {enb} / Sector {sector}"
            if isinstance(data, dict) and "label" in data:
                label_text += f" - {data['label']}"

            self.tower_label.config(text=label_text)

            # Clear previous metadata
            for widget in self.metadata_frame.winfo_children():
                widget.destroy()

            if isinstance(data, dict):
                self._add_meta_row("Location", data.get("location", "-"))
                self._add_meta_row("Bands", ", ".join(map(str, data.get("bands", []))))
                self._add_meta_row("Type", data.get("type", "-"))
                self._add_meta_row("Region (TAC/LAC)", str(data.get("region", "-")))
                self._add_meta_row("First Seen", data.get("first_seen", "-"))
                self._add_meta_row("Last Seen", data.get("last_seen", "-"))

                contrib = ", ".join(data.get("contributed_by", []))
                self._add_meta_row("Contributors", contrib if contrib else "-")

                # Show cell details for this sector only
                if "cells" in data:
                    matching_cells = {
                        k: v for k, v in data["cells"].items()
                        if v.get("sector") == sector
                    }
                    for cid, cell in matching_cells.items():
                        self._add_meta_row(f"Cell {cid} EARFCN", str(cell.get("earfcn", "-")))
                        self._add_meta_row(f"Band", f"B{cell.get('band', '-')}")
                        self._add_meta_row(f"Direction", cell.get("direction", "-"))
                        self._add_meta_row(f"RSRP", f"{cell.get('rsrp', '-')} dBm")
                        self._add_meta_row(f"RSRQ", f"{cell.get('rsrq', '-')} dB")
                        self._add_meta_row(f"SNR", f"{cell.get('snr', '-')} dB")
                        self._add_meta_row(f"Bandwidth", f"{cell.get('bandwidth_mhz', '-') or '-'} MHz")

            else:
                self._add_meta_row("Info", "No metadata available.")
                # Add stub entry for editing
                tower_info[tower_key] = {}
                with open(TOWER_INFO_FILE, "w") as f:
                    json.dump(tower_info, f, indent=2)

        except Exception as e:
            self.tower_label.config(text="Tower: Unknown")
            self.enb_id = None


    def update_loop(self):
        def loop():
            while True:
                data = fetch_signal()
                self.root.after(0, self.update_ui, data)
                time.sleep(REFRESH_INTERVAL)
        threading.Thread(target=loop, daemon=True).start()

    def update_ui(self, data):
        is_error = "error" in data
        self.root.title("Huawei LTE Signal Monitor" + (" ❌" if is_error else " ✅"))
        if is_error:
            message = data.get("error", "Unknown error")
            self.status_label.config(text=f"\u26A0\ufe0f {message}", fg="red")
        else:
            self.status_label.config(text="Router connection OK", fg="green")
            
        
        dl_freq_mhz, _ = parse_dl_freq("" if is_error else data.get("earfcn", ""))
        spacing_text = "-"
        if dl_freq_mhz:
            wavelength_m = 300 / dl_freq_mhz
            spacing_cm = round((wavelength_m / 2) * 100)
            spacing_text = f"~{spacing_cm} cm"

        for key, label in self.labels.items():
            color = "gray" if is_error else "black"
            if key == "band_freq":
                label.config(text=f"{dl_freq_mhz:.2f} MHz" if dl_freq_mhz else "-", fg=color)
                continue
            if key == "yagi_spacing":
                label.config(text=spacing_text, fg=color)
                continue
            val = "-" if is_error else data.get(key, "-")
            if key in REFERENCE and not is_error:
                try:
                    numeric = float(val.replace("dBm", "").replace("dB", ""))
                    good = REFERENCE[key]["good"]
                    fair = REFERENCE[key]["fair"]
                    color = "green" if numeric > good else "orange" if numeric > fair else "red" if key == "sinr" else \
                            "green" if numeric >= good else "orange" if numeric >= fair else "red"
                except:
                    color = "black"
            label.config(text=val, fg=color)

        if not is_error:
            new_cell_id = data.get("cell_id")
            new_lac = data.get("tac") or data.get("lac")
            if new_cell_id and new_cell_id != self.last_cell_id:
                self.update_tower_info(new_cell_id)
                self.last_cell_id = new_cell_id
            if new_lac:
                self.last_lac = new_lac
    def _add_meta_row(self, label, value):
        row = tk.Frame(self.metadata_frame)
        row.pack(anchor="w")
        tk.Label(row, text=f"{label}:", font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(row, text=f" {value}", font=("Arial", 10)).pack(side="left")

def main():
    root = tk.Tk()
    app = SignalMonitorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
