"""
Tests for Muto driver implementation with fake transport.
"""

import pytest
from typing import Optional, List
from muto_link.core.driver import Driver
from muto_link.transports.base import Transport


class FakeTransport(Transport):
    """Fake transport that records writes and returns canned responses."""

    def __init__(self) -> None:
        self.is_open = False
        self.written_data: List[bytes] = []
        self.read_responses: List[bytes] = []
        self.read_index = 0

    def open(self) -> None:
        """Open the fake transport."""
        self.is_open = True

    def close(self) -> None:
        """Close the fake transport."""
        self.is_open = False

    def write(self, data: bytes) -> int:
        """Record written data."""
        if not self.is_open:
            raise RuntimeError("Transport not open")
        self.written_data.append(data)
        return len(data)

    def read(self, size: int, timeout: Optional[float] = None) -> bytes:
        """Return canned response data."""
        if not self.is_open:
            raise RuntimeError("Transport not open")
        
        if self.read_index < len(self.read_responses):
            response = self.read_responses[self.read_index]
            # Return the requested number of bytes from the current response
            if len(response) <= size:
                # Return entire response and move to next
                self.read_index += 1
                return response
            else:
                # Return partial response and update the remaining data
                result = response[:size]
                self.read_responses[self.read_index] = response[size:]
                return result
        return bytes()  # No more responses

    def add_read_response(self, data: bytes) -> None:
        """Add a canned read response."""
        self.read_responses.append(data)

    def reset(self) -> None:
        """Reset recorded data."""
        self.written_data.clear()
        self.read_responses.clear()
        self.read_index = 0


class TestDriver:
    """Test driver functionality."""

    def test_torque_on(self) -> None:
        """Test torque ON command."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with driver:
            driver.torque_on()
        
        # Should have written one frame
        assert len(transport.written_data) == 1
        
        # Expected frame: 55 00 05 01 26 00 D3 00 AA
        expected = bytes([0x55, 0x00, 0x05, 0x01, 0x26, 0x00, 0xD3, 0x00, 0xAA])
        assert transport.written_data[0] == expected

    def test_torque_off(self) -> None:
        """Test torque OFF command."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with driver:
            driver.torque_off()
        
        # Should have written one frame
        assert len(transport.written_data) == 1
        
        # Expected frame: 55 00 05 01 27 00 D2 00 AA
        # CHK = 255 - ((5 + 1 + 0x27 + 0) % 256) = 255 - 45 = 210 = 0xD2
        expected = bytes([0x55, 0x00, 0x05, 0x01, 0x27, 0x00, 0xD2, 0x00, 0xAA])
        assert transport.written_data[0] == expected

    def test_servo_move(self) -> None:
        """Test servo move command."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with driver:
            driver.servo_move(servo_id=5, angle=90, speed=400)
        
        # Should have written one frame
        assert len(transport.written_data) == 1
        
        # Expected frame: 55 00 0C 01 40 05 7F 01 90 9D 00 AA  
        # angle=90° → protocol 127=0x7F, speed=400=0x0190, so speed_hi=0x01, speed_lo=0x90
        expected = bytes([0x55, 0x00, 0x0C, 0x01, 0x40, 0x05, 0x7F, 0x01, 0x90, 0x9D, 0x00, 0xAA])
        assert transport.written_data[0] == expected

    def test_servo_move_clamping(self) -> None:
        """Test servo move with clamped values."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with driver:
            # Test angle clamping (angle > 90 should be clamped to 90)
            driver.servo_move(servo_id=1, angle=200, speed=100)
        
        frame = transport.written_data[0]
        # Extract angle from frame (position 6: servo_id=1, angle=90 maps to protocol 127)
        assert frame[6] == 127  # Angle 90° should map to protocol value 127
        
        transport.reset()
        
        with driver:
            # Test speed clamping (speed > 65535 should be clamped to 65535)
            driver.servo_move(servo_id=1, angle=90, speed=70000)
        
        frame = transport.written_data[0]
        # Extract speed from frame (positions 7-8: speed_hi=0xFF, speed_lo=0xFF)
        assert frame[7] == 0xFF and frame[8] == 0xFF  # Speed should be clamped to 65535

    def test_servo_move_validation(self) -> None:
        """Test servo move parameter validation."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with pytest.raises(ValueError, match="Servo ID must be 1-18"):
            with driver:
                driver.servo_move(servo_id=0, angle=90, speed=400)
        
        with pytest.raises(ValueError, match="Servo ID must be 1-18"):
            with driver:
                driver.servo_move(servo_id=19, angle=90, speed=400)

    def test_read_servo_angle(self) -> None:
        """Test read servo angle command."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        # Set up canned response
        # Response frame: 55 00 05 12 50 5A CHK 00 AA (angle=90=0x5A)
        # LEN = 5 (LEN + INS + ADR + DATA + CHK), CHK = 255 - ((5 + 0x12 + 0x50 + 0x5A) % 256) = 255 - 193 = 62 = 0x3E
        response_frame = bytes([0x55, 0x00, 0x05, 0x12, 0x50, 0x5A, 0x3E, 0x00, 0xAA])
        transport.add_read_response(response_frame)
        
        with driver:
            result = driver.read_servo_angle(servo_id=5)
        
        # Should have written read command
        assert len(transport.written_data) == 1
        
        # Expected command frame: 55 00 05 02 50 05 A3 00 AA
        expected_cmd = bytes([0x55, 0x00, 0x05, 0x02, 0x50, 0x05, 0xA3, 0x00, 0xAA])
        assert transport.written_data[0] == expected_cmd
        
        # Should return angle data (0x5A = 90)
        assert result == bytes([0x5A])

    def test_calibrate_servo(self) -> None:
        """Test servo calibration command."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with driver:
            driver.calibrate_servo(servo_id=5, deviation=1000)
        
        # Should have written one frame
        assert len(transport.written_data) == 1
        
        # Expected frame: 55 00 07 01 28 05 03 E8 CHK 00 AA
        # deviation=1000=0x03E8, so dev_hi=0x03, dev_lo=0xE8
        # CHK = 255 - ((7 + 1 + 0x28 + 5 + 3 + 0xE8) % 256)
        # Sum = 7 + 1 + 40 + 5 + 3 + 232 = 288
        # CHK = 255 - (288 % 256) = 255 - 32 = 223 = 0xDF
        expected = bytes([0x55, 0x00, 0x07, 0x01, 0x28, 0x05, 0x03, 0xE8, 0xDF, 0x00, 0xAA])
        assert transport.written_data[0] == expected

    def test_calibrate_servo_validation(self) -> None:
        """Test calibrate servo parameter validation."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with pytest.raises(ValueError, match="Servo ID must be 1-18"):
            with driver:
                driver.calibrate_servo(servo_id=0, deviation=1000)

    def test_write_with_list_data(self) -> None:
        """Test write method with list data."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with driver:
            driver.write(addr=0x26, data=[0x00])
        
        # Should produce same result as torque_on()
        expected = bytes([0x55, 0x00, 0x05, 0x01, 0x26, 0x00, 0xD3, 0x00, 0xAA])
        assert transport.written_data[0] == expected

    def test_write_validation(self) -> None:
        """Test write method parameter validation."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        with pytest.raises(ValueError, match="Data\\[0\\] must be 0-255"):
            with driver:
                driver.write(addr=0x26, data=[256])
        
        with pytest.raises(ValueError, match="Data\\[0\\] must be 0-255"):
            with driver:
                driver.write(addr=0x26, data=[-1])

    def test_context_manager(self) -> None:
        """Test driver context manager behavior."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        assert not transport.is_open
        
        with driver:
            assert transport.is_open
            driver.torque_on()
        
        assert not transport.is_open
        assert len(transport.written_data) == 1

    def test_read_communication_error(self) -> None:
        """Test read method with communication errors."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        # Test incomplete header response
        transport.add_read_response(bytes([0x55, 0x00]))  # Incomplete header
        
        with pytest.raises(RuntimeError, match="Failed to read response header"):
            with driver:
                driver.read(addr=0x50, data=[5])

    def test_read_invalid_header(self) -> None:
        """Test read method with invalid header."""
        transport = FakeTransport()
        driver = Driver(transport)
        
        # Test invalid header
        transport.add_read_response(bytes([0x55, 0x01, 0x06]))  # Wrong second header byte
        
        with pytest.raises(RuntimeError, match="Invalid response header"):
            with driver:
                driver.read(addr=0x50, data=[5])
