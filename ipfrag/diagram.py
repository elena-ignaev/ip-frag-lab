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
