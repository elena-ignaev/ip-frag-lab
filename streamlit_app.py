"""Streamlit GUI: IP fragmentation lab (web)."""

from __future__ import annotations

import time

import plotly.graph_objects as go
import streamlit as st
from pandas import DataFrame

from ipfrag.diagram import color_for, explain_steps
from ipfrag.engine import FragmentationError, fragment_ipv4

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
    </style>
    """,
    unsafe_allow_html=True,
)


def packet_figure(result, highlight: int) -> go.Figure:
    fig = go.Figure()
    y_orig = 2.2
    header = result.header_size
    payload = result.payload_size
    total = max(result.packet_size, 1)

    fig.add_trace(
        go.Bar(
            x=[header],
            y=[y_orig],
            base=0,
            orientation="h",
            marker=dict(color="#1e3a5f"),
            name="Header",
            hovertemplate="Original header: %{x} B<extra></extra>",
            showlegend=True,
        )
    )
    fig.add_trace(
        go.Bar(
            x=[payload],
            y=[y_orig],
            base=header,
            orientation="h",
            marker=dict(color="#64748b"),
            name="Original payload",
            hovertemplate="Original payload: %{x} B<extra></extra>",
        )
    )

    for frag in result.fragments:
        y = 1.2 - (frag.index - 1) * 0.55
        line = dict(width=4, color="#facc15") if frag.index == highlight else dict(width=0)
        fig.add_trace(
            go.Bar(
                x=[frag.header_size],
                y=[y],
                base=0,
                orientation="h",
                marker=dict(color="#1e3a5f", line=line),
                hovertemplate=f"F{frag.index} header: {frag.header_size} B<extra></extra>",
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Bar(
                x=[frag.payload_size],
                y=[y],
                base=frag.header_size,
                orientation="h",
                marker=dict(color=color_for(frag.index), line=line),
                name=f"Fragment {frag.index}",
                hovertemplate=(
                    f"F{frag.index}: payload {frag.payload_size} B<br>"
                    f"offset {frag.offset_units} ({frag.offset_bytes} B)<br>"
                    f"{frag.flags_label}<extra></extra>"
                ),
            )
        )
        fig.add_annotation(
            x=frag.header_size + frag.payload_size + total * 0.02,
            y=y,
            text=f"F{frag.index}  off={frag.offset_units}  MF={frag.mf}",
            showarrow=False,
            xanchor="left",
            font=dict(color="#e2e8f0", size=12),
        )

    height = 220 + 70 * result.fragment_count
    fig.update_layout(
        barmode="stack",
        height=height,
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
        font=dict(color="#e2e8f0"),
        legend=dict(orientation="h", y=1.12),
        margin=dict(l=40, r=160, t=40, b=40),
        xaxis=dict(title="Bytes", range=[0, total * 1.35], gridcolor="#1e293b"),
        yaxis=dict(
            tickmode="array",
            tickvals=[2.2] + [1.2 - (i) * 0.55 for i in range(result.fragment_count)],
            ticktext=["Original"] + [f"F{i+1}" for i in range(result.fragment_count)],
            showgrid=False,
        ),
        title="Datagram → fragments (header copied onto each piece)",
    )
    return fig


st.title("IPv4 Fragmentation Lab")
st.caption(
    "Network-layer teaching tool: enter packet size, MTU, and header size. "
    "The lab computes fragment offsets and flags, then animates the split."
)

with st.sidebar:
    st.header("Datagram inputs")
    packet_size = st.number_input("Packet size (bytes)", min_value=20, max_value=65535, value=4000, step=1)
    mtu = st.number_input("MTU (bytes)", min_value=28, max_value=65535, value=1500, step=1)
    header_size = st.select_slider("Header size (bytes)", options=list(range(20, 61, 4)), value=20)
    identification = st.number_input("Identification (16-bit)", min_value=0, max_value=65535, value=777)
    st.divider()
    presets = st.selectbox(
        "Presets",
        (
            "Custom",
            "Ethernet example (4000 / 1500 / 20)",
            "Low MTU path (4000 / 576 / 20)",
            "Already fits (500 / 1500 / 20)",
        ),
    )
    if presets.startswith("Ethernet"):
        packet_size, mtu, header_size = 4000, 1500, 20
    elif presets.startswith("Low"):
        packet_size, mtu, header_size = 4000, 576, 20
    elif presets.startswith("Already"):
        packet_size, mtu, header_size = 500, 1500, 20

    play = st.button("Play animation", type="primary", width="stretch")
    reset = st.button("Reset highlight", width="stretch")

if "step" not in st.session_state:
    st.session_state.step = 0

try:
    result = fragment_ipv4(int(packet_size), int(mtu), int(header_size), int(identification))
except FragmentationError as exc:
    st.error(str(exc))
    st.stop()

steps = explain_steps(result)
max_step = len(steps) - 1

if play:
    st.session_state.step = 0
    placeholder = st.empty()
    status = st.empty()

    for i, text in enumerate(steps):
        st.session_state.step = i
        highlight = 0
        if result.fragmented:
            for frag in result.fragments:
                token = f"Fragment {frag.index}:"
                if token in text:
                    highlight = frag.index
        with placeholder.container():
            st.plotly_chart(packet_figure(result, highlight), width="stretch")
        status.info(f"Step {i + 1}/{len(steps)} — {text}")
        time.sleep(1.15)
else:
    if reset:
        st.session_state.step = 0
    highlight = 0
    current = steps[min(st.session_state.step, max_step)]
    if result.fragmented:
        for frag in result.fragments:
            if f"Fragment {frag.index}:" in current:
                highlight = frag.index
    st.plotly_chart(packet_figure(result, highlight), width="stretch")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Fragments", result.fragment_count)
c2.metric("Payload", f"{result.payload_size} B")
c3.metric("Max fragment payload", f"{result.max_fragment_payload} B")
c4.metric("Extra header overhead", f"{result.overhead_bytes} B")

left, right = st.columns((1.35, 1))
with left:
    st.subheader("Fragment table")
    st.dataframe(DataFrame(result.to_rows()), width="stretch", hide_index=True)
with right:
    st.subheader("Why these numbers?")
    for note in result.notes:
        st.write("• " + note)
    st.subheader("Walk-through")
    step_idx = st.slider("Narration step", 0, max_step, st.session_state.step)
    st.session_state.step = step_idx
    st.info(steps[step_idx])

st.markdown(
    """
**Field reminder (IPv4 header)**  
- **Identification** — same on every fragment of this datagram.  
- **Flags** — `0 DF MF`. This lab always uses DF=0 so fragmentation is allowed. MF=1 means more fragments follow.  
- **Fragment Offset** — payload starting position ÷ 8.
"""
)
