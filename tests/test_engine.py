from ipfrag.engine import FragmentationError, fragment_ipv4
import pytest


def test_classic_4000_1500_20():
    """Kurose/Ross-style example: 4000 B datagram, MTU 1500, 20 B header."""
    result = fragment_ipv4(4000, 1500, 20, identification=777)
    assert result.fragmented is True
    assert result.payload_size == 3980
    assert result.max_fragment_payload == 1480
    assert result.fragment_count == 3

    a, b, c = result.fragments
    assert a.payload_size == 1480 and a.offset_units == 0 and a.mf == 1
    assert b.payload_size == 1480 and b.offset_units == 185 and b.mf == 1
    assert c.payload_size == 1020 and c.offset_units == 370 and c.mf == 0
    assert all(f.identification == 777 for f in result.fragments)
    assert a.total_size == 1500
    assert c.total_size == 1040


def test_no_fragmentation_when_fits():
    result = fragment_ipv4(500, 1500, 20)
    assert result.fragmented is False
    assert result.fragment_count == 1
    assert result.fragments[0].mf == 0
    assert result.fragments[0].offset_units == 0


def test_rejects_mtu_too_small():
    with pytest.raises(FragmentationError):
        fragment_ipv4(1000, 24, 20)


def test_header_must_be_multiple_of_four():
    with pytest.raises(FragmentationError):
        fragment_ipv4(1000, 576, 21)
