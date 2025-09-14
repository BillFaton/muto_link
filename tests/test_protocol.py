"""
Tests for Muto protocol implementation.
"""

import pytest
from muto_link.core.protocol import build_frame, checksum, pack_uint16_be, unpack_uint16_be


class TestChecksum:
    """Test checksum calculation."""

    def test_basic_checksum(self) -> None:
        """Test basic checksum calculation."""
        # From the docs: control buzzer example
        # CHK = 255 - (0x09 + 0x01 + 0x18 + 0xFF) % 256
        payload = bytes([0x09, 0x01, 0x18, 0xFF])
        expected = 255 - ((0x09 + 0x01 + 0x18 + 0xFF) % 256)
        assert checksum(payload) == expected

    def test_checksum_overflow(self) -> None:
        """Test checksum with sum overflow."""
        # Create payload that sums > 255
        payload = bytes([0xFF, 0xFF, 0x01])  # Sum = 511
        expected = 255 - (511 % 256)  # 255 - 255 = 0
        assert checksum(payload) == 0

    def test_empty_payload_raises(self) -> None:
        """Test that empty payload raises ValueError."""
        with pytest.raises(ValueError, match="Payload cannot be empty"):
            checksum(bytes())


class TestPackUnpack:
    """Test big-endian packing/unpacking."""

    def test_pack_uint16_be(self) -> None:
        """Test 16-bit big-endian packing."""
        assert pack_uint16_be(0x0190) == bytes([0x01, 0x90])  # speed=400
        assert pack_uint16_be(0x0000) == bytes([0x00, 0x00])
        assert pack_uint16_be(0xFFFF) == bytes([0xFF, 0xFF])

    def test_pack_out_of_range(self) -> None:
        """Test packing out-of-range values."""
        with pytest.raises(ValueError, match="Value must be 0-65535"):
            pack_uint16_be(-1)
        with pytest.raises(ValueError, match="Value must be 0-65535"):
            pack_uint16_be(65536)

    def test_unpack_uint16_be(self) -> None:
        """Test 16-bit big-endian unpacking."""
        assert unpack_uint16_be(bytes([0x01, 0x90])) == 0x0190
        assert unpack_uint16_be(bytes([0x00, 0x00])) == 0x0000
        assert unpack_uint16_be(bytes([0xFF, 0xFF])) == 0xFFFF

    def test_unpack_wrong_length(self) -> None:
        """Test unpacking wrong length data."""
        with pytest.raises(ValueError, match="Expected 2 bytes"):
            unpack_uint16_be(bytes([0x01]))
        with pytest.raises(ValueError, match="Expected 2 bytes"):
            unpack_uint16_be(bytes([0x01, 0x02, 0x03]))


class TestBuildFrame:
    """Test frame building."""

    def test_torque_on_frame(self) -> None:
        """Test torque ON frame."""
        # INS=0x01, ADR=0x26, DATA=[0x00]
        frame = build_frame(ins=0x01, addr=0x26, data=bytes([0x00]))
        
        # Expected: 55 00 LEN 01 26 00 CHK 00 AA
        # LEN = 5 (LEN + INS + ADR + DATA + CHK)
        # CHK = 255 - ((5 + 1 + 0x26 + 0) % 256) = 255 - 44 = 211 = 0xD3
        expected = bytes([0x55, 0x00, 0x05, 0x01, 0x26, 0x00, 0xD3, 0x00, 0xAA])
        assert frame == expected

    def test_servo_move_frame(self) -> None:
        """Test servo move frame (id=5, angle=90, speed=400)."""
        # INS=0x01, ADR=0x40, DATA=[5, 90, 0x01, 0x90] (speed=400=0x0190)
        data = bytes([5, 90, 0x01, 0x90])
        frame = build_frame(ins=0x01, addr=0x40, data=data)
        
        # Expected: 55 00 LEN 01 40 05 5A 01 90 CHK 00 AA  
        # LEN = 8 (LEN + INS + ADR + 4*DATA + CHK)
        # CHK = 255 - ((8 + 1 + 0x40 + 5 + 90 + 1 + 0x90) % 256)
        # Sum = 8 + 1 + 64 + 5 + 90 + 1 + 144 = 313
        # CHK = 255 - (313 % 256) = 255 - 57 = 198 = 0xC6
        expected = bytes([0x55, 0x00, 0x08, 0x01, 0x40, 0x05, 0x5A, 0x01, 0x90, 0xC6, 0x00, 0xAA])
        assert frame == expected

    def test_read_angle_frame(self) -> None:
        """Test read servo angle frame (id=5)."""
        # INS=0x02, ADR=0x50, DATA=[5]
        frame = build_frame(ins=0x02, addr=0x50, data=bytes([5]))
        
        # Expected: 55 00 LEN 02 50 05 CHK 00 AA
        # LEN = 5 (LEN + INS + ADR + DATA + CHK)  
        # CHK = 255 - ((5 + 2 + 0x50 + 5) % 256) = 255 - 92 = 163 = 0xA3
        expected = bytes([0x55, 0x00, 0x05, 0x02, 0x50, 0x05, 0xA3, 0x00, 0xAA])
        assert frame == expected

    def test_frame_validation(self) -> None:
        """Test frame parameter validation."""
        # Invalid instruction
        with pytest.raises(ValueError, match="Instruction must be 0-255"):
            build_frame(ins=256, addr=0x26, data=bytes([0x00]))
        
        # Invalid address
        with pytest.raises(ValueError, match="Address must be 0-255"):
            build_frame(ins=0x01, addr=256, data=bytes([0x00]))
        
        # Data too long
        with pytest.raises(ValueError, match="Data too long"):
            build_frame(ins=0x01, addr=0x26, data=bytes(251))

    def test_empty_data(self) -> None:
        """Test frame with empty data."""
        frame = build_frame(ins=0x01, addr=0x26, data=bytes())
        
        # Expected: 55 00 04 01 26 CHK 00 AA (no data bytes)
        # LEN = 4 (LEN + INS + ADR + CHK)
        # CHK = 255 - ((4 + 1 + 0x26) % 256) = 255 - 43 = 212 = 0xD4
        expected = bytes([0x55, 0x00, 0x04, 0x01, 0x26, 0xD4, 0x00, 0xAA])
        assert frame == expected
