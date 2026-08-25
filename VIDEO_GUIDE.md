# Video demonstration script (about 4–6 minutes)

Use this as a shot list. Record **screen + voice**. Show the terminal once, then spend most of the time in the GUIs.

## Before you press record

1. Open a terminal in the project folder.
2. Activate the venv: `source .venv/bin/activate`
3. Have two commands ready:
   - `streamlit run streamlit_app.py`
   - `python qt_app.py`
4. Optional: open `dist/IPFragLab.app` (macOS) or `dist/IPFragLab/IPFragLab.exe` (Windows) to prove the executable.

Suggested layout: IDE or Finder with `ipfrag/engine.py` visible for 20 seconds, then full-screen GUI.

---

## Shot 1 — Introduce the problem (30–40 s)

**Show:** README or this lab’s title screen.

**Say:**  
“This application teaches **IPv4 fragmentation** at the network layer. A datagram that is larger than the next link’s **MTU** cannot be sent as one piece. The router splits the **payload**, copies the **IP header** onto each piece, and sets **Fragment Offset** and the **More Fragments** flag so the destination can reassemble.”

---

## Shot 2 — Point at the source (20–30 s)

**Show:** `ipfrag/engine.py` function `fragment_ipv4`.

**Say:**  
“All arithmetic lives in one engine. Streamlit and PyQt6 are only front ends. That keeps the web demo and the desktop executable consistent.”

---

## Shot 3 — Streamlit: textbook example (90 s)

**Do:**

1. Run `streamlit run streamlit_app.py` and wait for the browser.
2. Sidebar: Packet size **4000**, MTU **1500**, Header **20**, Identification **777** (or pick the Ethernet preset).
3. Click **Play animation**. Let it run.
4. Pause on the table. Point at Offset ×8 = 0, 185, 370 and MF = 1, 1, 0.

**Say:**  
“Payload is 3980 bytes. Each non-final fragment can carry 1480 bytes because (1500 − 20) is already a multiple of 8. Offset 185 means the second fragment starts 1480 bytes into the original payload. The last fragment has MF = 0.”

---

## Shot 4 — Streamlit: contrast cases (45 s)

**Do:**

1. Preset **Already fits (500 / 1500 / 20)**. Show a single fragment, MF=0.
2. Preset **Low MTU path (4000 / 576 / 20)**. Show many small fragments.

**Say:**  
“If the datagram already fits, there is no split. A smaller MTU produces more fragments and more extra headers — that is the overhead of fragmentation.”

---

## Shot 5 — PyQt6 desktop / executable (60–90 s)

**Do:**

1. Run `python qt_app.py` **or** launch `IPFragLab` from `dist/`.
2. Click **Load 4000 / 1500 / 20**, then **Animate**.
3. Scroll the notes panel and the table.

**Say:**  
“The desktop app is the packaged executable. Animate draws each fragment in order so you can see the header copied every time.”

---

## Shot 6 — Close (15–20 s)

**Say:**  
“Inputs are packet size, MTU, and header size. Outputs are fragment lengths, offsets in 8-byte units, and DF/MF flags, visualized in both a browser lab and a desktop GUI.”

---

## On-screen checklist (put in a corner title card if you want)

- [ ] 4000 / 1500 / 20 → 3 fragments  
- [ ] Offsets 0, 185, 370  
- [ ] MF 1, 1, 0  
- [ ] Fit case: no fragmentation  
- [ ] Show executable or `python qt_app.py`
