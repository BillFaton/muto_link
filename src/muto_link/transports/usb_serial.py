"""USB Serial transport implementation using pyserial."""

from typing import Optional
import serial
from .base import Transport
from ..logging import get_logger

logger = get_logger(__name__)


class UsbSerial(Transport):
    """USB Serial transport implementation using pyserial.
    
    Provides communication with the Muto baseboard via USB-to-serial adapters
    or direct USB serial connections. Supports configurable baud rates and timeouts.
    
    Example:
        >>> transport = UsbSerial("/dev/ttyUSB0", baud=115200)
        >>> transport.open()
        >>> transport.write(frame_data)
        >>> response = transport.read(10)
        >>> transport.close()
    """

    def __init__(self, port: str, baud: int = 115200, timeout: float = 0.05) -> None:
        """Initialize USB Serial transport.
        
        Args:
            port (str): Serial port path - '/dev/ttyUSB0' (Linux), 'COM3' (Windows), etc.
            baud (int): Baud rate in bits per second (default: 115200).
            timeout (float): Default read/write timeout in seconds (default: 0.05).
            
        Note:
            The timeout affects both read and write operations. A shorter timeout
            provides faster failure detection but may cause issues on slower systems.
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        logger.info(f"UsbSerial transport created: port={port}, baud={baud}")

    def open(self) -> None:
        """Open the serial connection.
        
        Establishes connection to the serial port with configured parameters.
        Buffers are automatically flushed after opening.
        
        Raises:
            serial.SerialException: If the serial port cannot be opened.
            Exception: For other connection errors.
        """
        if self._serial is not None and self._serial.is_open:
            logger.debug("Serial connection already open")
            return
        
        logger.info(f"Opening serial port: {self.port} at {self.baud} baud")
        
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout,
                write_timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Clear any stale data
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            logger.info(f"Serial port opened successfully: {self.port}")
            
        except serial.SerialException as e:
            logger.error(f"Failed to open serial port {self.port}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error opening serial port {self.port}: {e}")
            raise

    def close(self) -> None:
        """Close the serial connection.
        
        Safely closes the serial port connection. If the port is already closed
        or was never opened, this method does nothing.
        
        Note:
            Close errors are logged as warnings but do not raise exceptions.
        """
        if self._serial is not None and self._serial.is_open:
            logger.info(f"Closing serial port: {self.port}")
            try:
                self._serial.close()
                logger.info("Serial port closed successfully")
            except Exception as e:
                logger.warning(f"Error closing serial port: {e}")
        self._serial = None

    def write(self, data: bytes) -> int:
        """Write data to the serial port.
        
        Sends data to the serial port and ensures it's transmitted immediately
        by flushing the output buffer.
        
        Args:
            data (bytes): Bytes to transmit.
            
        Returns:
            int: Number of bytes written (should equal len(data) for successful writes).
            
        Raises:
            RuntimeError: If transport is not open.
            serial.SerialException: If write operation fails.
            Exception: For other write errors.
        """
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("Transport not open")
        
        logger.debug(f"Writing {len(data)} bytes: {data.hex()}")
        
        try:
            written = self._serial.write(data)
            self._serial.flush()  # Ensure immediate transmission
            bytes_written = written if written is not None else 0
            logger.debug(f"Write completed: {bytes_written} bytes")
            return bytes_written
            
        except serial.SerialException as e:
            logger.error(f"Serial write error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during serial write: {e}")
            raise

    def read(self, size: int, timeout: Optional[float] = None) -> bytes:
        """Read data from the serial port.
        
        Reads up to the specified number of bytes from the serial port.
        May return fewer bytes if timeout occurs or end of data is reached.
        
        Args:
            size (int): Maximum number of bytes to read.
            timeout (Optional[float]): Read timeout in seconds (None uses instance default).
            
        Returns:
            bytes: Bytes read from the port (may be shorter than requested size).
            
        Raises:
            RuntimeError: If transport is not open.
            serial.SerialException: If read operation fails.
            Exception: For other read errors.
        """
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("Transport not open")
        
        effective_timeout = timeout if timeout is not None else self.timeout
        logger.debug(f"Reading up to {size} bytes (timeout={effective_timeout}s)")
        
        try:
            if timeout is not None:
                old_timeout = self._serial.timeout
                self._serial.timeout = timeout
                try:
                    data = self._serial.read(size)
                finally:
                    self._serial.timeout = old_timeout
            else:
                data = self._serial.read(size)
            
            if data:
                logger.debug(f"Read {len(data)} bytes: {data.hex()}")
            else:
                logger.debug("Read timeout - no data received")
                
            return data
            
        except serial.SerialException as e:
            logger.error(f"Serial read error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during serial read: {e}")
            raise

    def __repr__(self) -> str:
        """String representation for debugging.
        
        Returns:
            str: Human-readable representation showing port, baud rate, and status.
        """
        status = "open" if (self._serial and self._serial.is_open) else "closed"
        return f"UsbSerial(port='{self.port}', baud={self.baud}, {status})"
