# IPv4 Fragmentation Lab

Teaching tool for the **network layer**: enter packet size, MTU, and IP header size, then see how an IPv4 datagram is fragmented (offsets, DF/MF flags) in two GUIs.

- **Streamlit** — browser lab with a playable animation (`streamlit_app.py`)
- **PyQt6** — desktop lab with a canvas animation (`qt_app.py`)
- Shared engine: `ipfrag/engine.py` (RFC 791 rules, no packets are sent)

## Setup

```bash
cd ip-frag-lab
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Web GUI:

```bash
streamlit run streamlit_app.py
```

Desktop GUI:

```bash
python qt_app.py
```

Tests:

```bash
pytest -q
```

## Build a desktop executable (PyQt6)

```bash
pyinstaller --noconfirm --windowed --name IPFragLab \
  --add-data "ipfrag:ipfrag" \
  qt_app.py
```

On macOS the app appears under `dist/IPFragLab.app`. On Windows you get `dist/IPFragLab/IPFragLab.exe`.

The Streamlit UI is meant to be run from source (`streamlit run`). Packaging Streamlit as a single file is possible via `run_web.py` but is heavier; the assignment executable is the PyQt6 app.

## Classic check

| Input | Result |
| --- | --- |
| Packet 4000, MTU 1500, header 20 | 3 fragments: 1480/1480/1020 payload, offsets 0 / 185 / 370, MF 1 / 1 / 0 |
