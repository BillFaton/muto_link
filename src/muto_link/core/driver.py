"""High-level driver for Muto baseboard communication."""

from typing import Union, List
from .protocol import build_frame, pack_uint16_be
from ..transports.base import Transport
from ..logging import get_logger

logger = get_logger(__name__)


class Driver:
    """High-level driver for Muto servo control.
    
    This class provides a convenient interface for controlling servos on the Muto
    baseboard. It handles protocol framing, communication, and provides both
    low-level register access and high-level servo control methods.
    
    Example:
        >>> transport = UsbSerial("/dev/ttyUSB0")
        >>> driver = Driver(transport)
        >>> with driver:
        ...     driver.torque_on()
        ...     driver.servo_move(1, 90, 1000)
    """

    def __init__(self, transport: Transport) -> None:
        """Initialize driver with transport.
        
        Args:
            transport (Transport): Transport instance for communication (UsbSerial, PiUartGpio, etc.).
        """
        self.transport = transport
        logger.info(f"Driver initialized with {type(transport).__name__}")

    def open(self) -> None:
        """Open the transport connection.
        
        Raises:
            Exception: If transport connection cannot be established.
        """
        logger.info("Opening transport connection")
        try:
            self.transport.open()
            logger.info("Transport connection opened successfully")
        except Exception as e:
            logger.error(f"Failed to open transport: {e}")
            raise

    def close(self) -> None:
        """Close the transport connection.
        
        Note:
            This method logs warnings for close errors but does not raise exceptions.
        """
        logger.info("Closing transport connection")
        try:
            self.transport.close()
            logger.info("Transport connection closed successfully")
        except Exception as e:
            logger.warning(f"Error closing transport: {e}")

    def write(self, addr: int, data: Union[List[int], bytes]) -> None:
        """Send a write command to the Muto baseboard.
        
        Args:
            addr (int): Register address (0-255).
            data (Union[List[int], bytes]): Data to write, either as list of integers (0-255) or bytes.
            
        Raises:
            ValueError: If data contains invalid byte values.
            Exception: If communication fails.
        """
        logger.debug(f"Write command: addr=0x{addr:02X}, data_len={len(data)}")
        
        if isinstance(data, list):
            for i, val in enumerate(data):
                if not (0 <= val <= 255):
                    raise ValueError(f"Data[{i}] must be 0-255, got {val}")
            data_bytes = bytes(data)
        else:
            data_bytes = data
            
        try:
            frame = build_frame(ins=0x01, addr=addr, data=data_bytes)
            self.transport.write(frame)
            logger.debug(f"Write command completed: addr=0x{addr:02X}")
        except Exception as e:
            logger.error(f"Write command failed: {e}")
            raise

    def read(self, addr: int, data: Union[List[int], bytes]) -> bytes:
        """Send a read command and return response data.
        
        Args:
            addr (int): Register address to read from (0-255).
            data (Union[List[int], bytes]): Command data, either as list of integers (0-255) or bytes.
            
        Returns:
            bytes: Response data bytes from the baseboard.
            
        Raises:
            ValueError: If data contains invalid byte values.
            RuntimeError: If communication fails or response is invalid.
        """
        logger.debug(f"Read command: addr=0x{addr:02X}, data_len={len(data)}")
        
        if isinstance(data, list):
            for i, val in enumerate(data):
                if not (0 <= val <= 255):
                    raise ValueError(f"Data[{i}] must be 0-255, got {val}")
            data_bytes = bytes(data)
        else:
            data_bytes = data
            
        try:
            frame = build_frame(ins=0x02, addr=addr, data=data_bytes)
            self.transport.write(frame)
            logger.debug("Read command sent, waiting for response")
            
            # Read response header to get frame length
            header = self.transport.read(3, timeout=1.0)
            if len(header) != 3:
                raise RuntimeError("Failed to read response header")
                
            if header[0] != 0x55 or header[1] != 0x00:
                raise RuntimeError(f"Invalid response header: {header.hex()}")
                
            frame_len = header[2]
            if frame_len < 5:
                raise RuntimeError(f"Invalid frame length: {frame_len}")
            
            # Read remaining frame data
            remaining = self.transport.read(frame_len - 3, timeout=1.0)
            if len(remaining) < frame_len - 3:
                raise RuntimeError("Failed to read complete response")
                
            full_frame = header + remaining
            logger.debug(f"Response received: {len(full_frame)} bytes")
            
            # Verify frame tail
            if full_frame[-2:] != bytes([0x00, 0xAA]):
                raise RuntimeError(f"Invalid response tail: {full_frame[-2:].hex()}")
                
            # Extract data payload (skip header, length, instruction, address, checksum, tail)
            data_start = 5  # Skip LEN + INS + ADR
            data_end = len(full_frame) - 3  # Skip CHK + tail
            response_data = full_frame[data_start:data_end]
            
            logger.debug(f"Read command completed: addr=0x{addr:02X}, response_len={len(response_data)}")
            return response_data
            
        except Exception as e:
            logger.error(f"Read command failed: {e}")
            raise

    def torque_on(self) -> None:
        """Enable servo torque (command control).
        
        Enables torque on all servos, allowing them to be controlled by commands.
        Must be called before moving servos.
        
        Raises:
            Exception: If communication fails.
        """
        logger.info("Enabling servo torque")
        self.write(addr=0x26, data=[0x00])

    def torque_off(self) -> None:
        """Disable servo torque (allows manual positioning).
        
        Disables torque on all servos, allowing manual positioning but disabling
        command control until torque is re-enabled or unit is power-cycled.
        
        Raises:
            Exception: If communication fails.
        """
        logger.info("Disabling servo torque")
        self.write(addr=0x27, data=[0x00])

    def servo_move(self, servo_id: int, angle: int, speed: int) -> None:
        """Move servo to specified angle at given speed.
        
        Args:
            servo_id (int): Servo ID (1-18).
            angle (int): Target angle in degrees (0-180), will be clamped to valid range.
            speed (int): Movement speed (0-65535), will be clamped to valid range.
            
        Raises:
            ValueError: If servo_id is out of valid range.
            Exception: If communication fails.
            
        Example:
            >>> driver.servo_move(5, 90, 1000)  # Move servo 5 to 90° at speed 1000
        """
        if not (1 <= servo_id <= 18):
            raise ValueError(f"Servo ID must be 1-18, got {servo_id}")
        
        # Clamp values to valid ranges
        original_angle, original_speed = angle, speed
        angle = max(0, min(180, angle))
        speed = max(0, min(0xFFFF, speed))
        
        if original_angle != angle or original_speed != speed:
            logger.debug(f"Values clamped: angle {original_angle}->{angle}, speed {original_speed}->{speed}")
        
        logger.info(f"Moving servo {servo_id} to {angle}° at speed {speed}")
        speed_bytes = pack_uint16_be(speed)
        data = [servo_id, angle, speed_bytes[0], speed_bytes[1]]
        self.write(addr=0x40, data=data)

    def read_servo_angle(self, servo_id: int) -> bytes:
        """Read current servo angle.
        
        Args:
            servo_id (int): Servo ID (1-18).
            
        Returns:
            bytes: Raw response data containing angle information.
            
        Raises:
            ValueError: If servo_id is out of valid range.
            Exception: If communication fails.
        """
        if not (1 <= servo_id <= 18):
            raise ValueError(f"Servo ID must be 1-18, got {servo_id}")
        
        logger.debug(f"Reading angle for servo {servo_id}")
        return self.read(addr=0x50, data=[servo_id])

    def calibrate_servo(self, servo_id: int, deviation: int) -> None:
        """Calibrate servo position deviation.
        
        Args:
            servo_id (int): Servo ID (1-18).
            deviation (int): Calibration deviation value (0-65535), will be clamped.
            
        Raises:
            ValueError: If servo_id is out of valid range.
            Exception: If communication fails.
        """
        if not (1 <= servo_id <= 18):
            raise ValueError(f"Servo ID must be 1-18, got {servo_id}")
        
        original_deviation = deviation
        deviation = max(0, min(0xFFFF, deviation))
        
        if original_deviation != deviation:
            logger.debug(f"Deviation clamped from {original_deviation} to {deviation}")
        
        logger.info(f"Calibrating servo {servo_id} with deviation {deviation}")
        dev_bytes = pack_uint16_be(deviation)
        data = [servo_id, dev_bytes[0], dev_bytes[1]]
        self.write(addr=0x28, data=data)

    def read_battery_level(self) -> bytes:
        """Read battery level from the baseboard.
        
        Returns:
            bytes: Raw response data containing battery level information.
            
        Raises:
            Exception: If communication fails.
        """
        logger.debug("Reading battery level")
        return self.read(addr=0x01, data=[0x01])

    def __enter__(self) -> "Driver":
        """Context manager entry.
        
        Returns:
            Driver: Self for use in with statement.
        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit.
        
        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.close()
