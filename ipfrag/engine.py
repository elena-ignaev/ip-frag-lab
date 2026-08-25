"""RFC 791 IPv4 datagram fragmentation (teaching model).

This module does not send packets. It only computes fragment sizes, offsets,
and flags so students can see how a router splits a datagram to fit an MTU.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class FragmentationError(ValueError):
    """Raised when inputs cannot produce a valid IPv4 fragment set."""


@dataclass(frozen=True)
class Fragment:
    index: int
    identification: int
    header_size: int
    payload_size: int
    offset_bytes: int
    more_fragments: bool

    @property
    def offset_units(self) -> int:
        """Fragment Offset field: payload start in units of 8 bytes."""
        return self.offset_bytes // 8

    @property
    def payload_end(self) -> int:
        """First payload byte *not* carried by this fragment (exclusive)."""
        return self.offset_bytes + self.payload_size

    @property
    def total_size(self) -> int:
        return self.header_size + self.payload_size

    @property
    def mf(self) -> int:
        return 1 if self.more_fragments else 0

    @property
    def df(self) -> int:
        return 0

    @property
    def flags_bits(self) -> str:
        """3-bit Flags field: reserved | DF | MF."""
        return f"0{self.df}{self.mf}"

    @property
    def flags_label(self) -> str:
        return f"DF={self.df} MF={self.mf}"

    def to_row(self) -> dict[str, object]:
        return {
            "Fragment": self.index,
            "ID": self.identification,
            "Header (B)": self.header_size,
            "Payload (B)": self.payload_size,
            "Total (B)": self.total_size,
            "Offset (bytes)": self.offset_bytes,
            "Offset (×8)": self.offset_units,
            "Flags": self.flags_bits,
            "DF": self.df,
            "MF": self.mf,
        }


@dataclass
class FragmentationResult:
    packet_size: int
    mtu: int
    header_size: int
    payload_size: int
    max_fragment_payload: int
    identification: int
    fragmented: bool
    fragments: list[Fragment] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def fragment_count(self) -> int:
        return len(self.fragments)

    @property
    def overhead_bytes(self) -> int:
        extra_headers = max(0, self.fragment_count - 1) * self.header_size
        return extra_headers

    def to_rows(self) -> list[dict[str, object]]:
        return [frag.to_row() for frag in self.fragments]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise FragmentationError(message)


def fragment_ipv4(
    packet_size: int,
    mtu: int,
    header_size: int = 20,
    identification: int = 1,
) -> FragmentationResult:
    """Split an IPv4 datagram so each fragment fits in ``mtu``.

    Parameters
    ----------
    packet_size:
        Total original datagram length (header + payload), in bytes.
    mtu:
        Maximum transmission unit of the outgoing link, in bytes.
    header_size:
        IPv4 header length copied onto every fragment (20–60).
    identification:
        Identification field shared by all fragments of this datagram.
    """
    _require(packet_size > 0, "Packet size must be a positive number of bytes.")
    _require(mtu > 0, "MTU must be a positive number of bytes.")
    _require(20 <= header_size <= 60, "IPv4 header size must be between 20 and 60 bytes.")
    _require(header_size % 4 == 0, "IPv4 header size must be a multiple of 4 (IHL units).")
    _require(packet_size >= header_size, "Packet size cannot be smaller than the header.")
    _require(mtu > header_size, "MTU must be larger than the IP header.")
    _require(0 <= identification <= 65535, "Identification must fit in 16 bits.")

    payload_size = packet_size - header_size
    notes: list[str] = [
        f"Original datagram = {header_size} B header + {payload_size} B payload "
        f"= {packet_size} B.",
        f"Each fragment carries its own {header_size} B header.",
        "Fragment Offset is stored in units of 8 bytes, so each fragment's payload "
        "(except possibly the last) is a multiple of 8.",
    ]

    if packet_size <= mtu:
        fragment = Fragment(
            index=1,
            identification=identification,
            header_size=header_size,
            payload_size=payload_size,
            offset_bytes=0,
            more_fragments=False,
        )
        notes.append("Datagram already fits the MTU, so no fragmentation occurs (MF=0).")
        return FragmentationResult(
            packet_size=packet_size,
            mtu=mtu,
            header_size=header_size,
            payload_size=payload_size,
            max_fragment_payload=payload_size,
            identification=identification,
            fragmented=False,
            fragments=[fragment],
            notes=notes,
        )

    usable = mtu - header_size
    max_fragment_payload = usable - (usable % 8)
    _require(
        max_fragment_payload >= 8,
        "MTU is too small: after the header, fewer than 8 bytes remain for payload. "
        "IPv4 requires non-last fragment payloads to be a multiple of 8 bytes.",
    )

    notes.append(
        f"Maximum payload per non-final fragment = floor(({mtu} − {header_size}) / 8) × 8 "
        f"= {max_fragment_payload} B."
    )

    fragments: list[Fragment] = []
    remaining = payload_size
    offset_bytes = 0
    index = 1

    while remaining > 0:
        is_last = remaining <= max_fragment_payload
        chunk = remaining if is_last else max_fragment_payload
        fragments.append(
            Fragment(
                index=index,
                identification=identification,
                header_size=header_size,
                payload_size=chunk,
                offset_bytes=offset_bytes,
                more_fragments=not is_last,
            )
        )
        remaining -= chunk
        offset_bytes += chunk
        index += 1

    notes.append(
        f"Produced {len(fragments)} fragments. Extra header overhead = "
        f"{(len(fragments) - 1) * header_size} B."
    )

    return FragmentationResult(
        packet_size=packet_size,
        mtu=mtu,
        header_size=header_size,
        payload_size=payload_size,
        max_fragment_payload=max_fragment_payload,
        identification=identification,
        fragmented=True,
        fragments=fragments,
        notes=notes,
    )
