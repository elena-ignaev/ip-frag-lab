"""Shared diagram helpers for Streamlit (Plotly) and teaching labels."""

from __future__ import annotations

from ipfrag.engine import FragmentationResult

FRAGMENT_COLORS = [
    "#38bdf8",
    "#818cf8",
    "#34d399",
    "#fbbf24",
    "#fb7185",
    "#c084fc",
    "#2dd4bf",
    "#f97316",
]


def color_for(index: int) -> str:
    return FRAGMENT_COLORS[(index - 1) % len(FRAGMENT_COLORS)]


def hover_story(frag, result: FragmentationResult) -> str:
    """Plain-language tooltip for one fragment (Plotly / Qt)."""
    last = "last piece — MF=0 so the receiver knows the datagram is complete"
    more = "MF=1 — the receiver must wait for later pieces before reassembling"
    mf_why = last if frag.mf == 0 else more
    return (
        f"<b>Fragment {frag.index} of {result.fragment_count}</b><br>"
        f"On the wire: <b>{frag.total_size} B</b> "
        f"(header {frag.header_size} + payload {frag.payload_size})<br>"
        f"Fits MTU {result.mtu} B? "
        f"{'yes' if frag.total_size <= result.mtu else 'no'}<br><br>"
        f"This piece carries original payload bytes "
        f"<b>{frag.offset_bytes}–{frag.payload_end - 1}</b><br>"
        f"Fragment Offset field = {frag.offset_bytes} ÷ 8 = <b>{frag.offset_units}</b><br>"
        f"Identification = <b>{frag.identification}</b> "
        f"(copied onto every fragment of this datagram)<br>"
        f"Flags {frag.flags_bits} → {frag.flags_label}<br>"
        f"{mf_why}"
    )


def hover_story_plain(frag, result: FragmentationResult) -> str:
    return (
        hover_story(frag, result)
        .replace("<br>", "\n")
        .replace("<b>", "")
        .replace("</b>", "")
        .replace("<i>", "")
        .replace("</i>", "")
        .replace("&gt;", ">")
    )


def hover_payload_map(frag, result: FragmentationResult) -> str:
    return (
        f"<b>Original payload slice → Fragment {frag.index}</b><br>"
        f"Bytes {frag.offset_bytes}–{frag.payload_end - 1} of the "
        f"{result.payload_size} B payload<br>"
        f"The router copies a fresh {frag.header_size} B IP header, "
        f"then sends this slice as a {frag.total_size} B packet.<br>"
        f"Offset={frag.offset_units}  {frag.flags_label}<br>"
        f"<i>Click to pin this fragment in the header inspector.</i>"
    )


def explain_steps(result: FragmentationResult) -> list[str]:
    steps = [
        "Start with one IPv4 datagram at the network layer.",
        f"Compare total length {result.packet_size} B with link MTU {result.mtu} B.",
    ]
    if not result.fragmented:
        steps.append("Total length ≤ MTU, so the datagram is sent as a single packet (MF=0).")
        return steps

    steps.append("Total length > MTU, so the router fragments the payload.")
    steps.append(
        f"Non-final payloads are limited to {result.max_fragment_payload} B "
        "(multiple of 8 so the Offset field stays aligned)."
    )
    for frag in result.fragments:
        mf = "1 (more fragments follow)" if frag.more_fragments else "0 (last fragment)"
        steps.append(
            f"Fragment {frag.index}: copy the {frag.header_size} B header, take "
            f"{frag.payload_size} B of payload, set Offset={frag.offset_units} "
            f"({frag.offset_bytes} B), MF={mf}."
        )
    steps.append("The destination host reassembles using Identification + Offset + MF.")
    return steps
