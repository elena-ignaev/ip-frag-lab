"""Streamlit GUI: IP fragmentation lab (web)."""

from __future__ import annotations

import time

import streamlit as st
from pandas import DataFrame

from ipfrag.diagram import explain_steps
from ipfrag.engine import FragmentationError, fragment_ipv4
from ipfrag.presets import CUSTOM, DEFAULT_SCENARIO, SCENARIOS, SCENARIOS_BY_NAME
from ipfrag.figures import (
    fragment_cards_html,
    header_inspector_figure,
    journey_figure,
    on_wire_figure,
    payload_map_figure,
)

st.set_page_config(
    page_title="IP Fragmentation Lab",
    page_icon="🧩",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem;}
    div[data-testid="stMetric"] {background: #0f172a; border: 1px solid #1e293b;
      border-radius: 12px; padding: 8px 12px;}
    .frag-row {display:flex; gap:12px; flex-wrap:wrap; margin: 4px 0 18px 0; align-items:flex-start;}
    .frag-card {flex:1 1 180px; min-width:180px; background:#0f172a;
      border:2px solid #38bdf8; border-radius:12px; padding:12px;
      transition: transform .16s ease, box-shadow .16s ease, background .16s ease;}
    .frag-card:hover {transform: translateY(-4px); background:#132038;
      box-shadow: 0 12px 30px rgba(56,189,248,.28);}
    .frag-kicker {font-size:11px; letter-spacing:.09em; text-transform:uppercase; color:#94a3b8;}
    .frag-id {font-size:19px; font-weight:700; margin:2px 0 0 0;}
    .wire-bar {height:8px; border-radius:99px; margin:9px 0;}
    .frag-meta {font-size:12px; color:#cbd5e1;}
    .frag-tip {max-height:0; opacity:0; overflow:hidden; font-size:12px; line-height:1.5;
      color:#e2e8f0; transition: max-height .22s ease, opacity .22s ease, margin .22s ease;}
    .frag-card:hover .frag-tip {max-height:220px; opacity:1; margin-top:10px;
      border-top:1px solid #334155; padding-top:8px;}
    .frag-hint {font-size:12px; color:#94a3b8; margin-bottom:2px;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("IPv4 Fragmentation Lab")
st.caption(
    "Watch a datagram hit the MTU gate, split into fragments, and travel to the receiver. "
    "Hover packets, payload slices, and header fields for the offset and flag story."
)

if "packet_size" not in st.session_state:
    st.session_state.packet_size = DEFAULT_SCENARIO.packet_size
    st.session_state.mtu = DEFAULT_SCENARIO.mtu
    st.session_state.header_size = DEFAULT_SCENARIO.header_size
    st.session_state.identification = DEFAULT_SCENARIO.identification
    st.session_state.scenario = DEFAULT_SCENARIO.name


def apply_scenario() -> None:
    """Copy a suggested scenario into the input widgets."""
    scenario = SCENARIOS_BY_NAME.get(st.session_state.scenario)
    if scenario is None:
        return
    st.session_state.packet_size = scenario.packet_size
    st.session_state.mtu = scenario.mtu
    st.session_state.header_size = scenario.header_size
    st.session_state.identification = scenario.identification
    st.session_state.step = 0
    st.session_state.inspect = 1


def mark_custom() -> None:
    """Hand-edited inputs no longer match the named scenario."""
    st.session_state.scenario = CUSTOM


with st.sidebar:
    st.header("Suggested settings")
    st.caption("Not sure what to enter? Pick a scenario and the inputs below fill in.")
    st.selectbox(
        "Scenario",
        [s.name for s in SCENARIOS] + [CUSTOM],
        key="scenario",
        on_change=apply_scenario,
    )
    chosen = SCENARIOS_BY_NAME.get(st.session_state.scenario)
    if chosen is not None:
        st.info(
            f"**{chosen.packet_size} B datagram · MTU {chosen.mtu} · header "
            f"{chosen.header_size} B**\n\n{chosen.why}"
        )
    else:
        st.caption("Adjust the four inputs below however you like.")

    st.divider()
    st.subheader("Datagram inputs")
    packet_size = st.number_input(
        "Packet size (bytes)",
        min_value=20,
        max_value=65535,
        step=1,
        key="packet_size",
        on_change=mark_custom,
        help="Total length of the original datagram, including its IP header.",
    )
    mtu = st.number_input(
        "MTU (bytes)",
        min_value=28,
        max_value=65535,
        step=1,
        key="mtu",
        on_change=mark_custom,
        help="Largest packet the next link accepts. Ethernet is 1500; IPv4 hosts must accept at least 576.",
    )
    header_size = st.select_slider(
        "Header size (bytes)",
        options=list(range(20, 61, 4)),
        key="header_size",
        on_change=mark_custom,
        help="20 B with no options. Options push it up to 60 B, in 4-byte steps.",
    )
    identification = st.number_input(
        "Identification (16-bit)",
        min_value=0,
        max_value=65535,
        key="identification",
        on_change=mark_custom,
        help="Any value 0–65535. Every fragment of this datagram carries the same one.",
    )

    st.divider()
    play = st.button("Play narration", type="primary", width="stretch")
    reset = st.button("Reset highlight", width="stretch")
    st.caption("Use ▶ Send packets on the diagram to animate the forwarding path.")

if "step" not in st.session_state:
    st.session_state.step = 0
if "playing" not in st.session_state:
    st.session_state.playing = False
if "_advance" not in st.session_state:
    st.session_state._advance = False
if "inspect" not in st.session_state:
    st.session_state.inspect = 1

try:
    result = fragment_ipv4(int(packet_size), int(mtu), int(header_size), int(identification))
except FragmentationError as exc:
    st.error(str(exc))
    st.stop()

steps = explain_steps(result)
max_step = len(steps) - 1

if play:
    st.session_state.playing = True
    st.session_state.step = 0
    st.session_state._advance = False
elif reset:
    st.session_state.playing = False
    st.session_state.step = 0
    st.session_state._advance = False
    st.session_state.inspect = 1
elif st.session_state._advance:
    st.session_state._advance = False
    if st.session_state.step >= max_step:
        st.session_state.playing = False
    else:
        st.session_state.step += 1

if st.session_state.step > max_step:
    st.session_state.step = max_step

current = steps[st.session_state.step]
highlight = 0
if result.fragmented:
    for frag in result.fragments:
        if f"Fragment {frag.index}:" in current:
            highlight = frag.index

st.plotly_chart(
    journey_figure(result, highlight),
    width="stretch",
    key="journey_chart",
)

st.html(
    '<div class="frag-hint">Hover a card to expand the byte-range and flag explanation.</div>'
    + fragment_cards_html(result, highlight)
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Fragments", result.fragment_count)
c2.metric("Payload", f"{result.payload_size} B")
c3.metric("Max fragment payload", f"{result.max_fragment_payload} B")
c4.metric("Extra header overhead", f"{result.overhead_bytes} B")

map_col, wire_col = st.columns((1.4, 1))
with map_col:
    map_event = st.plotly_chart(
        payload_map_figure(result, highlight or st.session_state.inspect),
        width="stretch",
        key="payload_map",
        on_select="rerun",
        selection_mode="points",
    )
with wire_col:
    st.plotly_chart(
        on_wire_figure(result, highlight or st.session_state.inspect),
        width="stretch",
        key="on_wire_chart",
    )

inspect = highlight or int(st.session_state.inspect)
try:  # clicking a payload slice pins that fragment in the header inspector
    selection = map_event["selection"] if map_event is not None else None
    points = (selection or {}).get("points") or []
    if points:
        custom = points[0].get("customdata")
        if custom:
            inspect = int(custom[0] if isinstance(custom, (list, tuple)) else custom)
            st.session_state.inspect = inspect
except (TypeError, KeyError, ValueError, IndexError):
    pass
inspect = max(1, min(inspect, result.fragment_count))
pinned = next(f for f in result.fragments if f.index == inspect)

st.plotly_chart(
    header_inspector_figure(pinned),
    width="stretch",
    key="header_inspector",
)

left, right = st.columns((1.35, 1))
with left:
    st.subheader("Fragment table")
    st.dataframe(DataFrame(result.to_rows()), width="stretch", hide_index=True, key="frag_table")
with right:
    st.subheader("Why these numbers?")
    for note in result.notes:
        st.write("• " + note)
    st.subheader("Walk-through")
    st.slider(
        "Narration step",
        min_value=0,
        max_value=max_step,
        key="step",
        disabled=st.session_state.playing,
    )
    st.info(steps[st.session_state.step])

st.markdown(
    """
**How to read the animation**  
1. The grey square is the original datagram leaving Host A.  
2. The dashed orange slot is the **MTU** — nothing larger than that can be forwarded.  
3. Colored squares are fragments; hover them for **which payload bytes**, **Offset ÷ 8**, and **MF**.  
4. Hover the stacked payload bar to see how the original data is sliced. Click a slice to pin the header inspector.
"""
)

if st.session_state.playing:
    st.caption(f"Narration {st.session_state.step + 1} of {len(steps)}")
    time.sleep(1.15)
    st.session_state._advance = True
    st.rerun()
