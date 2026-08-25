# Implementation Report — IPv4 Fragmentation Lab

## 1. Purpose

This program is a **network-layer teaching lab**. It does not transmit traffic. The student supplies **packet size**, **MTU**, and **header size**; the software applies IPv4 fragmentation rules (RFC 791) and shows each fragment’s **length**, **Fragment Offset**, and **flags** in two graphical interfaces.

## 2. Architecture

| Layer | File | Role |
| --- | --- | --- |
| Engine | `ipfrag/engine.py` | Validates inputs; computes fragments |
| Narration | `ipfrag/diagram.py` | Step text and fragment colours |
| Web GUI | `streamlit_app.py` | Streamlit + Plotly animation |
| Desktop GUI | `qt_app.py` | PyQt6 canvas, table, QTimer animation |
| Tests | `tests/test_engine.py` | Checks the textbook 4000/1500/20 example |
| Executable | PyInstaller on `qt_app.py` | Windowed desktop app |

Both GUIs call the same function, `fragment_ipv4(...)`. Changing the math in one place keeps the web and desktop labs consistent.

## 3. Fragmentation rules implemented

1. **Original payload** = packet size − header size.
2. If packet size ≤ MTU, emit **one** packet: Offset = 0, MF = 0.
3. Otherwise the **maximum payload of a non-final fragment** is  
   \(\lfloor (\mathrm{MTU} - \mathrm{header}) / 8 \rfloor \times 8\).  
   Alignment to 8 bytes is required because the **Fragment Offset** field counts 8-byte units.
4. Each fragment **copies the IP header** (same Identification). Payload is sliced sequentially.
5. **MF = 1** on every fragment except the last; **DF = 0** in this lab so fragmentation is allowed.
6. Last fragment may have a payload that is **not** a multiple of 8.

Worked example used in tests and the demo video:

- Inputs: 4000 B datagram, MTU 1500, header 20.
- Payload = 3980 B; max non-final payload = 1480 B.
- Fragments: 1480 / 1480 / 1020 B payload; totals 1500 / 1500 / 1040 B.
- Offsets: 0, 185, 370 (because 1480/8 = 185).
- Flags: MF=1, MF=1, MF=0.

## 4. Graphical user interfaces

**Streamlit.** Sidebar inputs, optional presets, a stacked-bar Plotly diagram (original datagram vs fragments), a table of fields, and **Play animation**, which walks the narration steps and highlights the fragment being explained.

**PyQt6.** Form on the left; custom-painted bars on the right; results table. **Fragment** shows the full result immediately. **Animate** uses `QTimer` to reveal fragments one by one.

## 5. How to run and how to obtain an executable

```text
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
streamlit run streamlit_app.py
python qt_app.py
pyinstaller --noconfirm --windowed --name IPFragLab --add-data "ipfrag:ipfrag" qt_app.py
```

The marked assignment executable is the PyQt6 build in `dist/`. Streamlit remains the browser demo (`streamlit run`).

## 6. Limitations (intentional)

- IPv4 only (no IPv6 fragmentation extension headers).
- No overlapping-fragment or “evil” offset cases; those belong to security courses, not this lab.
- Options in the header are modelled only as a larger header length (20–60, multiple of 4).
