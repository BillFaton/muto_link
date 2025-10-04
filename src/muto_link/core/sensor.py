"""High-level sensor for Muto baseboard communication."""

from typing import Union, List, NamedTuple
from .protocol import build_frame, pack_uint16_be, unpack_uint16_be
from ..transports.base import Transport
from ..logging import get_logger

logger = get_logger(__name__)


class IMUAngleData(NamedTuple):
    """Parsed IMU fusion angle data.
    
    Attributes:
        roll (int): Roll angle in raw units (0-65535).
        pitch (int): Pitch angle in raw units (0-65535).
        yaw (int): Yaw angle in raw units (0-65535).
        temperature (int): Temperature reading (0-255).
    """
    roll: int
    pitch: int
    yaw: int
    temperature: int


class RawIMUData(NamedTuple):
    """Parsed raw IMU 9-axis sensor data.
    
    Attributes:
        accel_x (int): Accelerometer X-axis raw value (0-65535).
        accel_y (int): Accelerometer Y-axis raw value (0-65535).
        accel_z (int): Accelerometer Z-axis raw value (0-65535).
        gyro_x (int): Gyroscope X-axis raw value (0-65535).
        gyro_y (int): Gyroscope Y-axis raw value (0-65535).
        gyro_z (int): Gyroscope Z-axis raw value (0-65535).
        mag_x (int): Magnetometer X-axis raw value (0-65535).
        mag_y (int): Magnetometer Y-axis raw value (0-65535).
        mag_z (int): Magnetometer Z-axis raw value (0-65535).
    """
    accel_x: int
    accel_y: int
    accel_z: int
    gyro_x: int
    gyro_y: int
    gyro_z: int
    mag_x: int
    mag_y: int
    mag_z: int


class Sensor:
    """High-level sensor for Muto servo control.
    
    This class provides a convenient interface for controlling servos on the Muto
    baseboard. It handles protocol framing, communication, and provides both
    low-level register access and high-level servo control methods.
    
    Example:
        >>> transport = UsbSerial("/dev/ttyUSB0")
        >>> sensor = Sensor(transport)
        >>> with sensor:
        ...     sensor.torque_on()
        ...     sensor.servo_move(1, 90, 1000)    # Positive angle
        ...     sensor.servo_move(2, -45, 500)    # Negative angle
    """

    def __init__(self, transport: Transport) -> None:
        """Initialize sensor with transport.
        
        Args:
            transport (Transport): Transport instance for communication (UsbSerial, PiUartGpio, etc.).
        """
        self.transport = transport
        logger.info(f"Sensor initialized with {type(transport).__name__}")

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

    def read_raw_IMU_angle(self) -> bytes:
        """Read current IMU angle.
            
        Returns:
            bytes: Raw response data containing angle information.
            
        Raises:
            ValueError: If servo_id is out of valid range.
            Exception: If communication fails.
        """
        
        logger.debug(f"Reading IMU angle.")
        return self.read(addr=0x61, data=[0x12])
    def read_IMU_angle(self) -> bytes:
        """Read current IMU angle.
            
        Returns:
            bytes: Raw response data containing angle information.
            
        Raises:
            ValueError: If servo_id is out of valid range.
            Exception: If communication fails.
        """
        
        logger.debug(f"Reading IMU angle.")
        return self.read(addr=0x60, data=[0x07])
    
    def read_battery_level(self) -> bytes:
        """Read battery level from the baseboard.
        
        Returns:
            bytes: Raw response data containing battery level information.
            
        Raises:
            Exception: If communication fails.
        """
        logger.debug("Reading battery level")
        return self.read(addr=0x01, data=[0x01])

    def get_imu_angle(self) -> IMUAngleData:
        """Get parsed IMU fusion angle data.
        
        Reads the IMU fusion calculated angles and temperature, parsing the raw bytes
        into a structured IMUAngleData object with meaningful field names.
        
        Returns:
            IMUAngleData: Parsed angle data containing roll, pitch, yaw, and temperature.
            
        Raises:
            RuntimeError: If response data length is incorrect or communication fails.
            Exception: If communication fails.
            
        Example:
            >>> angle_data = sensor.get_imu_angle()
            >>> print(f"Roll: {angle_data.roll}, Pitch: {angle_data.pitch}")
        """
        logger.debug("Getting parsed IMU angle data")
        raw_data = self.read_IMU_angle()
        
        if len(raw_data) != 7:
            raise RuntimeError(f"Expected 7 bytes for IMU angle data, got {len(raw_data)}")
        
        # Parse according to protocol: roll (data1-2), pitch (data3-4), yaw (data5-6), temp (data7)
        roll = unpack_uint16_be(raw_data[0:2])
        pitch = unpack_uint16_be(raw_data[2:4])
        yaw = unpack_uint16_be(raw_data[4:6])
        temperature = raw_data[6]
        
        logger.debug(f"Parsed IMU angle: roll={roll}, pitch={pitch}, yaw={yaw}, temp={temperature}")
        return IMUAngleData(roll=roll, pitch=pitch, yaw=yaw, temperature=temperature)

    def get_raw_imu_data(self) -> RawIMUData:
        """Get parsed raw IMU 9-axis sensor data.
        
        Reads the raw IMU accelerometer, gyroscope, and magnetometer data, parsing 
        the raw bytes into a structured RawIMUData object with meaningful field names.
        
        Returns:
            RawIMUData: Parsed sensor data containing 9-axis accelerometer, gyroscope, and magnetometer values.
            
        Raises:
            RuntimeError: If response data length is incorrect or communication fails.
            Exception: If communication fails.
            
        Example:
            >>> imu_data = sensor.get_raw_imu_data()
            >>> print(f"Accel X: {imu_data.accel_x}, Gyro X: {imu_data.gyro_x}")
        """
        logger.debug("Getting parsed raw IMU data")
        raw_data = self.read_raw_IMU_angle()
        
        if len(raw_data) != 18:
            raise RuntimeError(f"Expected 18 bytes for raw IMU data, got {len(raw_data)}")
        
        # Parse according to protocol:
        # Bytes 1-6: accelerometer x,y,z
        # Bytes 7-12: gyroscope x,y,z  
        # Bytes 13-18: magnetometer x,y,z
        accel_x = unpack_uint16_be(raw_data[0:2])
        accel_y = unpack_uint16_be(raw_data[2:4])
        accel_z = unpack_uint16_be(raw_data[4:6])
        
        gyro_x = unpack_uint16_be(raw_data[6:8])
        gyro_y = unpack_uint16_be(raw_data[8:10])
        gyro_z = unpack_uint16_be(raw_data[10:12])
        
        mag_x = unpack_uint16_be(raw_data[12:14])
        mag_y = unpack_uint16_be(raw_data[14:16])
        mag_z = unpack_uint16_be(raw_data[16:18])
        
        logger.debug(f"Parsed raw IMU data: accel=({accel_x},{accel_y},{accel_z}), "
                    f"gyro=({gyro_x},{gyro_y},{gyro_z}), mag=({mag_x},{mag_y},{mag_z})")
        
        return RawIMUData(
            accel_x=accel_x, accel_y=accel_y, accel_z=accel_z,
            gyro_x=gyro_x, gyro_y=gyro_y, gyro_z=gyro_z,
            mag_x=mag_x, mag_y=mag_y, mag_z=mag_z
        )

    def __enter__(self) -> "Sensor":
        """Context manager entry.
        
        Returns:
            Sensor: Self for use in with statement.
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
