"""Suggested datagram scenarios for students who don't know what to type."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    packet_size: int
    mtu: int
    header_size: int
    identification: int
    why: str


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="Textbook example — 4000 B over Ethernet",
        packet_size=4000,
        mtu=1500,
        header_size=20,
        identification=777,
        why="The standard classroom case. Splits into 3 fragments with offsets 0, 185, 370. "
        "Start here.",
    ),
    Scenario(
        name="No fragmentation needed — small web request",
        packet_size=500,
        mtu=1500,
        header_size=20,
        identification=101,
        why="The datagram already fits the MTU, so it travels whole with MF=0. "
        "Compare this against the case above.",
    ),
    Scenario(
        name="Just barely too big — DSL / PPPoE link",
        packet_size=1500,
        mtu=1492,
        header_size=20,
        identification=222,
        why="Only 8 bytes over the limit, yet it still costs a second packet with a full "
        "header. Shows why fragmentation is expensive.",
    ),
    Scenario(
        name="VPN tunnel shrinks the MTU",
        packet_size=1500,
        mtu=1400,
        header_size=20,
        identification=333,
        why="Encapsulation eats into the MTU, so traffic that crossed Ethernet fine now "
        "has to be split.",
    ),
    Scenario(
        name="Jumbo frame into normal Ethernet",
        packet_size=9000,
        mtu=1500,
        header_size=20,
        identification=444,
        why="A large server-to-server datagram meets an ordinary link. Produces many "
        "fragments — watch the header overhead climb.",
    ),
    Scenario(
        name="Guaranteed minimum IPv4 path (MTU 576)",
        packet_size=4000,
        mtu=576,
        header_size=20,
        identification=555,
        why="576 B is the smallest MTU every IPv4 host must accept. Same datagram, far "
        "more pieces.",
    ),
    Scenario(
        name="Header with options (60 B header)",
        packet_size=4000,
        mtu=1500,
        header_size=60,
        identification=666,
        why="IP options make the header 60 B, leaving less room for payload in every "
        "fragment. Compare the fragment count with the first scenario.",
    ),
    Scenario(
        name="Very small MTU — legacy / constrained link",
        packet_size=2000,
        mtu=296,
        header_size=20,
        identification=888,
        why="An extreme case. Useful for seeing offsets grow in steps of 8-byte units.",
    ),
)

SCENARIOS_BY_NAME = {s.name: s for s in SCENARIOS}

CUSTOM = "Custom — I'll set my own values"

DEFAULT_SCENARIO = SCENARIOS[0]
