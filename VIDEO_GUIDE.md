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

## Shot 3 — Streamlit: send the packets (2 min)

**Do:**

1. Run `streamlit run streamlit_app.py` and wait for the browser.
2. Sidebar: Packet size **4000**, MTU **1500**, Header **20**, Identification **777** (or pick the Ethernet preset).
3. Click **▶ Send packets** on the diagram. Let the datagram reach the dashed MTU gate and the three fragments cross to Host B.
4. **Hover fragment 2** — hold still so the tooltip is readable on camera.
5. Hover each **fragment card** so it expands.
6. **Hover, then click, the middle slice** of “Which original bytes go in which fragment?” and show the header inspector updating.
7. Hover **Fragment Offset** and **Flags** in the header inspector.
8. Click **Play narration** and let one or two steps advance.

**Say:**  
“Payload is 3980 bytes. Each non-final fragment can carry 1480 bytes because (1500 − 20) is already a multiple of 8. The tooltip shows fragment 2 carrying original bytes 1480 to 2959, so the Offset field is 1480 divided by 8 — that is 185. MF stays 1 until the last fragment, which tells Host B when it can reassemble.”

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
2. Click **Load 4000 / 1500 / 20**, then **Animate send**.
3. Hover a coloured fragment square — show the tooltip and the byte-range line under the diagram.
4. Hover a row in the fragment table and point out the matching packet lighting up.

**Say:**  
“The desktop app is the packaged executable. The same story plays here: the datagram stops at the MTU gate, then each fragment travels with its own copied header. Hovering any fragment explains its offset and flags.”

---

## Shot 6 — Close (15–20 s)

**Say:**  
“Inputs are packet size, MTU, and header size. Outputs are fragment lengths, offsets in 8-byte units, and DF/MF flags, visualized in both a browser lab and a desktop GUI.”

---

## On-screen checklist (put in a corner title card if you want)

- [ ] 4000 / 1500 / 20 → 3 fragments  
- [ ] Offsets 0, 185, 370  
- [ ] MF 1, 1, 0  
- [ ] Animation: datagram → MTU gate → fragments in flight  
- [ ] Hover a fragment (tooltip with byte range)  
- [ ] Click a payload slice → header inspector  
- [ ] Fit case: no fragmentation  
- [ ] Show executable or `python qt_app.py`
