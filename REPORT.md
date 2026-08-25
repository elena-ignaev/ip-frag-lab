# Implementation Report — IPv4 Fragmentation Lab

## 1. Purpose

This program is a **network-layer teaching lab**. It does not transmit traffic. The student supplies **packet size**, **MTU**, and **header size**; the software applies IPv4 fragmentation rules (RFC 791) and shows each fragment’s **length**, **Fragment Offset**, and **flags** in two graphical interfaces.

## 2. Architecture

| Layer | File | Role |
| --- | --- | --- |
| Engine | `ipfrag/engine.py` | Validates inputs; computes fragments |
| Narration | `ipfrag/diagram.py` | Step text, colours, hover explanations |
| Figures | `ipfrag/figures.py` | Plotly path animation, payload map, header inspector |
| Web GUI | `streamlit_app.py` | Streamlit page, hover cards, narration player |
| Desktop GUI | `qt_app.py` | PyQt6 animated canvas with hover tooltips |
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

The goal of the visuals is to make fragmentation feel like an event on a link rather than a static table.

**Streamlit (web).**

1. **Path animation** — the datagram leaves Host A, stops at the router's dashed **MTU gate**, and the fragments then cross to Host B one at a time. Driven by Plotly animation frames with **▶ Send packets**, **❚❚ Pause**, and a scrubber labelled by stage (“leaving A”, “at MTU gate”, “F2 in flight”).
2. **Hover on any packet** — reports on-wire size, the header/payload split, which original payload bytes it carries, the Offset ÷ 8 arithmetic, Identification, and why MF is 0 or 1.
3. **Fragment cards** — CSS hover expands each card to show the byte range and flag meaning.
4. **Payload map** — the original payload as coloured slices, so students see the data being cut. Clicking a slice pins that fragment.
5. **Header inspector** — the pinned fragment's IPv4 fields as hoverable boxes (Identification, Flags, Fragment Offset, Total Length), each with a teaching note.
6. **On-wire size vs MTU** — bars against a dashed MTU ceiling, showing every fragment now fits.
7. **Play narration** — steps the written walk-through and highlights the matching fragment everywhere.

**PyQt6 (desktop).** The canvas draws Host A → router → Host B with the same story: a `QTimer` moves the datagram to the MTU gate, then releases fragments along the link. Hovering a fragment square shows a tooltip with the same offset/flag explanation and prints its byte range under the diagram; hovering a table row highlights the matching packet.

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
