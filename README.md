# IPv4 Fragmentation Lab

Teaching tool for the **network layer**: enter packet size, MTU, and IP header size, then watch an IPv4 datagram hit the MTU limit and travel onward as fragments, with offsets and DF/MF flags explained on hover.

- **Streamlit** — browser lab: animated forwarding path, hoverable packets, payload map, header inspector (`streamlit_app.py`)
- **PyQt6** — desktop lab: animated canvas with hover tooltips (`qt_app.py`)
- Shared engine: `ipfrag/engine.py` (RFC 791 rules, no packets are sent)
- Shared figures: `ipfrag/figures.py`

### What you can interact with

| Interaction | What it teaches |
| --- | --- |
| **▶ Send packets** | Datagram reaches the router's MTU gate, then fragments cross the link one by one |
| Hover a moving packet | On-wire size, the payload bytes it carries, `Offset ÷ 8`, Identification, why MF is 0 or 1 |
| Hover a fragment card | Byte range and flag meaning, expanded in place |
| Hover / click the payload map | Which original bytes became which fragment; clicking pins it in the header inspector |
| Hover a header field | Meaning of Identification, Flags, Fragment Offset, Total Length for that fragment |
| Scrub the path slider | Step through stages: leaving A → at MTU gate → Fn in flight |
| **Play narration** | Walks the written explanation, highlighting the matching fragment |

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
