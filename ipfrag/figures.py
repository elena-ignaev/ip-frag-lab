"""Plotly figures: on-the-wire send animation, payload map, header inspector."""

from __future__ import annotations

import plotly.graph_objects as go

from ipfrag.diagram import color_for, hover_payload_map, hover_story
from ipfrag.engine import Fragment, FragmentationResult

DARK = dict(
    paper_bgcolor="#020617",
    plot_bgcolor="#020617",
    font=dict(color="#e2e8f0", size=12),
    hoverlabel=dict(bgcolor="#0f172a", font_size=13, font_family="Inter, sans-serif", align="left"),
)


def _marker_size(total: int, max_total: int) -> float:
    return 18 + 28 * (total / max(max_total, 1))


#: Fragments drawn as moving squares. Beyond this, extras are summarised in one
#: marker so the animation stays responsive for very large datagrams.
MAX_ANIMATED_FRAGMENTS = 10

#: Frames spent releasing fragments, independent of fragment count, so a 45-way
#: split animates as fast as a 3-way split.
RELEASE_FRAMES = 26


def _frame_label(i: int, approach: int, pause: int, n: int, release: int) -> str:
    """Human label for the scrubber so students see the stage, not a frame number."""
    if i < approach:
        return "leaving A"
    if i < approach + pause:
        return "at MTU gate"
    if release <= 0:
        return "arriving at B"
    progress = (i - approach - pause) / release
    lead = min(n, max(1, int(progress * n) + 1))
    return f"F{lead} in flight"


def journey_figure(result: FragmentationResult, highlight: int = 0) -> go.Figure:
    """Animate a datagram hitting the MTU gate, then fragments crossing the link."""
    shown = result.fragments[:MAX_ANIMATED_FRAGMENTS]
    hidden = result.fragment_count - len(shown)
    n = len(shown)
    approach = 12
    pause = 5
    release = RELEASE_FRAMES
    total_frames = approach + pause + release

    src, gate, dst = 0.9, 5.0, 9.1
    lanes = {frag.index: 1.15 - (frag.index - 1) * (2.3 / max(n, 1)) for frag in shown}
    #: fraction of the release window before fragment k starts moving
    stagger = {frag.index: (frag.index - 1) / max(n, 1) * 0.55 for frag in shown}

    def original_trace(x: float, stuck: bool) -> go.Scatter:
        why = (
            f"Original datagram {result.packet_size} B at the sender.<br>"
            f"Payload {result.payload_size} B + header {result.header_size} B."
        )
        if stuck:
            why = (
                f"<b>Too wide for this link</b><br>"
                f"Datagram {result.packet_size} B &gt; MTU {result.mtu} B.<br>"
                f"The router must fragment the payload; it cannot squeeze the whole packet through."
                if result.fragmented
                else (
                    f"Datagram {result.packet_size} B ≤ MTU {result.mtu} B.<br>"
                    f"No split needed — send as one packet (MF=0)."
                )
            )
        return go.Scatter(
            x=[x],
            y=[0.2],
            mode="markers+text",
            text=["DATAGRAM"],
            textposition="top center",
            marker=dict(
                size=_marker_size(result.packet_size, result.packet_size),
                color="#64748b",
                line=dict(width=3, color="#f8fafc"),
                symbol="square",
            ),
            name="Original datagram",
            hovertemplate=why + "<extra></extra>",
            showlegend=False,
        )

    def fragment_trace(frag: Fragment, x: float, visible: bool) -> go.Scatter:
        accent = highlight == frag.index
        return go.Scatter(
            x=[x] if visible else [None],
            y=[lanes[frag.index]] if visible else [None],
            mode="markers+text",
            text=[f"F{frag.index}"],
            textposition="middle center",
            textfont=dict(size=11, color="#020617", family="Arial Black"),
            marker=dict(
                size=_marker_size(frag.total_size, result.mtu),
                color=color_for(frag.index),
                line=dict(width=4 if accent else 1, color="#facc15" if accent else "#0f172a"),
                symbol="square",
            ),
            name=f"Fragment {frag.index}",
            customdata=[[frag.index]],
            hovertemplate=hover_story(frag, result) + "<extra></extra>",
            showlegend=False,
        )

    def empty_original() -> go.Scatter:
        t = original_trace(src, False)
        t.x, t.y = [None], [None]
        return t

    def traces_for(frame_i: int) -> list:
        if frame_i < approach:
            x = src + (gate - src) * (frame_i / max(approach - 1, 1))
            items = [original_trace(x, False)]
            items.extend(fragment_trace(f, gate, False) for f in shown)
            return items
        if frame_i < approach + pause:
            items = [original_trace(gate, True)]
            items.extend(fragment_trace(f, gate, False) for f in shown)
            return items

        t = (frame_i - approach - pause) / max(release - 1, 1)
        items = [empty_original()]
        for frag in shown:
            start = stagger[frag.index]
            local = (t - start) / max(1.0 - start, 0.05)
            if local <= 0:
                items.append(fragment_trace(frag, gate, False))
                continue
            local = min(1.0, local)
            items.append(fragment_trace(frag, gate + (dst - gate) * local, True))
        return items

    frames = [go.Frame(data=traces_for(i), name=str(i)) for i in range(total_frames)]
    fig = go.Figure(data=traces_for(0), frames=frames)

    fig.add_shape(
        type="rect",
        x0=-0.2,
        x1=1.6,
        y0=-1.7,
        y1=1.7,
        fillcolor="#132a44",
        line_width=0,
        layer="below",
    )
    fig.add_shape(
        type="rect",
        x0=8.4,
        x1=10.2,
        y0=-1.7,
        y1=1.7,
        fillcolor="#132a44",
        line_width=0,
        layer="below",
    )
    fig.add_shape(
        type="line",
        x0=1.6,
        x1=8.4,
        y0=0,
        y1=0,
        line=dict(color="#1e293b", width=10),
        layer="below",
    )
    fig.add_shape(
        type="rect",
        x0=4.55,
        x1=5.45,
        y0=-1.7,
        y1=1.7,
        fillcolor="rgba(249,115,22,0.10)",
        line=dict(color="#f97316", width=2, dash="dash"),
        layer="below",
    )
    fig.add_annotation(x=0.7, y=1.55, text="Host A  (sender)", showarrow=False, font=dict(size=13))
    fig.add_annotation(
        x=5.0,
        y=1.55,
        text=f"Router  ·  MTU gate {result.mtu} B",
        showarrow=False,
        font=dict(size=13, color="#fdba74"),
    )
    fig.add_annotation(x=9.3, y=1.55, text="Host B  (reassemble)", showarrow=False, font=dict(size=13))
    footnote = "Packets move left → right. Hover a square for offset, flags, and which payload bytes it carries."
    if hidden > 0:
        footnote += f"  ({hidden} further fragments omitted from the animation — see the table.)"
    fig.add_annotation(
        x=5.0,
        y=-1.45,
        text=footnote,
        showarrow=False,
        font=dict(size=11, color="#94a3b8"),
    )

    fig.update_layout(
        **DARK,
        height=420,
        margin=dict(l=24, r=24, t=36, b=48),
        title="Sending across the link (play to watch fragmentation)",
        xaxis=dict(range=[-0.4, 10.4], visible=False),
        yaxis=dict(range=[-1.8, 1.8], visible=False),
        hovermode="closest",
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                showactive=False,
                x=1.0,
                y=1.22,
                xanchor="right",
                yanchor="top",
                pad=dict(r=4, t=0),
                bgcolor="#1e293b",
                bordercolor="#38bdf8",
                font=dict(color="#e2e8f0", size=12),
                buttons=[
                    dict(
                        label="▶ Send packets",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=90, redraw=True),
                                fromcurrent=True,
                                mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="❚❚ Pause",
                        method="animate",
                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=0,
                y=-0.04,
                len=0.86,
                x=0.07,
                pad=dict(t=6),
                currentvalue=dict(prefix="Scrub the path: ", font=dict(size=12, color="#94a3b8")),
                font=dict(size=10, color="#64748b"),
                steps=[
                    dict(
                        method="animate",
                        args=[[str(i)], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
                        label=_frame_label(i, approach, pause, n, release),
                    )
                    for i in range(0, total_frames, max(1, total_frames // 10))
                ],
            )
        ],
    )
    return fig


def payload_map_figure(result: FragmentationResult, highlight: int = 0) -> go.Figure:
    """Original payload as colored slices — hover/click maps bytes to a fragment."""
    fig = go.Figure()
    for frag in result.fragments:
        accent = frag.index == highlight
        fig.add_trace(
            go.Bar(
                y=["Original payload"],
                x=[frag.payload_size],
                orientation="h",
                marker=dict(
                    color=color_for(frag.index),
                    line=dict(width=3 if accent else 1, color="#facc15" if accent else "#020617"),
                ),
                name=f"F{frag.index}",
                customdata=[[frag.index, frag.offset_bytes, frag.payload_end, frag.offset_units, frag.mf]],
                hovertemplate=hover_payload_map(frag, result) + "<extra></extra>",
            )
        )
    fig.update_layout(
        **DARK,
        barmode="stack",
        height=180,
        margin=dict(l=120, r=24, t=48, b=40),
        title="Which original bytes go in which fragment?  (hover a slice · click to inspect)",
        xaxis=dict(title="Payload byte offset", range=[0, max(result.payload_size, 1)], gridcolor="#1e293b"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=1.25),
        hovermode="closest",
    )
    return fig


def on_wire_figure(result: FragmentationResult, highlight: int = 0) -> go.Figure:
    """Each fragment's on-wire length against the MTU ceiling."""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[f"F{f.index}" for f in result.fragments],
            y=[f.total_size for f in result.fragments],
            marker=dict(
                color=[color_for(f.index) for f in result.fragments],
                line=dict(
                    width=[3 if f.index == highlight else 0 for f in result.fragments],
                    color="#facc15",
                ),
            ),
            customdata=[
                [f.index, f.header_size, f.payload_size, f.offset_units, f.mf] for f in result.fragments
            ],
            hovertemplate=(
                "Fragment %{x}<br>On-wire %{y} B = %{customdata[1]} B header + %{customdata[2]} B payload<br>"
                "Offset=%{customdata[3]}  MF=%{customdata[4]}<br>"
                "Must be ≤ MTU so this packet can leave the router.<extra></extra>"
            ),
            showlegend=False,
        )
    )
    fig.add_hline(
        y=result.mtu,
        line_dash="dash",
        line_color="#f97316",
        annotation_text=f"MTU {result.mtu} B",
        annotation_position="top left",
        annotation_font_color="#fdba74",
    )
    fig.update_layout(
        **DARK,
        height=260,
        margin=dict(l=48, r=24, t=48, b=40),
        title="On-wire size vs MTU",
        yaxis=dict(title="Bytes", gridcolor="#1e293b", rangemode="tozero"),
        xaxis=dict(title="Fragment"),
        hovermode="x unified",
    )
    return fig


def header_inspector_figure(frag: Fragment) -> go.Figure:
    """IPv4 header fields for one fragment; hover each box for the teaching note."""
    cells = [
        (0, 3, "Identification", str(frag.identification), "Same ID on every fragment so Host B can group this datagram."),
        (3.1, 1.2, "Flags", frag.flags_bits, f"Reserved=0, DF={frag.df} (may fragment), MF={frag.mf}."),
        (4.4, 3.6, "Fragment Offset", str(frag.offset_units), f"Payload starts at byte {frag.offset_bytes} (= {frag.offset_units} × 8)."),
        (0, 2.0, "IHL / HLen", str(frag.header_size), "Copied onto this fragment; not shared with siblings."),
        (2.1, 2.9, "Total Length", str(frag.total_size), "Length of THIS packet only (header + this slice), not the original datagram."),
        (5.1, 2.9, "MF meaning", "more" if frag.mf else "last", "MF=1 → more fragments follow. MF=0 → this is the last piece."),
    ]
    fig = go.Figure()
    for x0, w, title, value, tip in cells:
        fig.add_trace(
            go.Bar(
                x=[w],
                y=["IPv4 header (this fragment)"],
                base=x0,
                orientation="h",
                marker=dict(color="#1e3a5f", line=dict(color="#38bdf8", width=1)),
                hovertemplate=f"<b>{title} = {value}</b><br>{tip}<extra></extra>",
                showlegend=False,
            )
        )
        fig.add_annotation(
            x=x0 + w / 2,
            y=0,
            text=f"{title}<br><b>{value}</b>",
            showarrow=False,
            font=dict(size=11, color="#e2e8f0"),
        )
    fig.update_layout(
        **DARK,
        barmode="overlay",
        height=200,
        margin=dict(l=24, r=24, t=36, b=24),
        title=f"Fragment {frag.index} — hover a header field",
        xaxis=dict(range=[-0.1, 8.2], visible=False),
        yaxis=dict(visible=False),
        hovermode="closest",
    )
    return fig


def fragment_cards_html(result: FragmentationResult, highlight: int = 0, limit: int = 12) -> str:
    """Hover-expanding cards. Emitted as one unindented line for st.html."""
    cards = []
    for frag in result.fragments[:limit]:
        glow = "box-shadow:0 0 0 2px #facc15;" if frag.index == highlight else ""
        color = color_for(frag.index)
        mf_note = (
            "Not the last piece — the receiver keeps waiting."
            if frag.mf
            else "Last piece — the receiver can now reassemble."
        )
        cards.append(
            f'<div class="frag-card" style="border-color:{color};{glow}">'
            f'<div class="frag-kicker">Fragment {frag.index}</div>'
            f'<div class="frag-id">ID {frag.identification}</div>'
            f'<div class="wire-bar" style="background:{color}"></div>'
            f'<div class="frag-meta">Offset {frag.offset_units} · MF={frag.mf} · '
            f"{frag.total_size} B on wire</div>"
            f'<div class="frag-tip"><b>Fragment {frag.index} detail</b><br/>'
            f"Carries payload bytes {frag.offset_bytes}–{frag.payload_end - 1}<br/>"
            f"Offset field = {frag.offset_bytes} ÷ 8 = {frag.offset_units}<br/>"
            f"Fresh {frag.header_size} B header copied · {frag.flags_label}<br/>"
            f"{mf_note}</div>"
            f"</div>"
        )
    remaining = result.fragment_count - len(cards)
    if remaining > 0:
        cards.append(
            '<div class="frag-card" style="border-color:#475569">'
            '<div class="frag-kicker">And more</div>'
            f'<div class="frag-id">+{remaining}</div>'
            '<div class="wire-bar" style="background:#475569"></div>'
            '<div class="frag-meta">Remaining fragments are listed in the table below.</div>'
            "</div>"
        )
    return '<div class="frag-row">' + "".join(cards) + "</div>"
