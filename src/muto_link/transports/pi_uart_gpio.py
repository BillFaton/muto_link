"""Raspberry Pi UART/GPIO transport with optional direction control."""

from typing import Optional
import serial
from .base import Transport
from ..logging import get_logger

logger = get_logger(__name__)


class PiUartGpio(Transport):
    """Raspberry Pi UART transport with optional GPIO direction control.
    
    Provides communication via the Raspberry Pi's built-in UART with optional
    GPIO-based direction control for half-duplex RS-485 transceivers.
    
    Features:
        - Uses Pi's hardware UART (/dev/serial0 by default)
        - Optional GPIO direction control for DE/RE pins
        - Automatic direction switching for half-duplex communication
        
    Example:
        >>> # Standard UART
        >>> transport = PiUartGpio()
        >>> 
        >>> # With direction control for RS-485
        >>> transport = PiUartGpio(direction_pin=17)
    """

    def __init__(
        self, 
        port: str = "/dev/serial0",
        baud: int = 115200, 
        timeout: float = 0.05, 
        direction_pin: Optional[int] = None
    ) -> None:
        """Initialize Pi UART transport.
        
        Args:
            port (str): UART port path - typically '/dev/serial0' for Pi's hardware UART.
            baud (int): Baud rate in bits per second (default: 115200).
            timeout (float): Default read/write timeout in seconds (default: 0.05).
            direction_pin (Optional[int]): Optional GPIO pin number for DE/RE control on RS-485 transceivers.
                         Requires gpiozero library. Pin goes HIGH for transmit, LOW for receive.
                         
        Raises:
            RuntimeError: If gpiozero is not available when direction_pin is specified.
            Exception: If GPIO initialization fails.
            
        Note:
            The Pi UART must be enabled in raspi-config and the console login should be disabled.
        """
        self.port = port
        self.baud = baud
        self.timeout = timeout
        self.direction_pin = direction_pin
        self._serial: Optional[serial.Serial] = None
        self._direction_control = None
        
        logger.info(f"PiUartGpio transport created: port={port}, baud={baud}, direction_pin={direction_pin}")
        
        if direction_pin is not None:
            logger.info(f"Initializing GPIO direction control on pin {direction_pin}")
            try:
                from gpiozero import LED  # type: ignore
                self._direction_control = LED(direction_pin)
                logger.info("GPIO direction control initialized successfully")
            except ImportError:
                raise RuntimeError(
                    f"gpiozero not available, cannot use direction_pin={direction_pin}. "
                    "Install with: pip install gpiozero"
                )
            except Exception as e:
                logger.error(f"Failed to initialize GPIO control on pin {direction_pin}: {e}")
                raise

    def open(self) -> None:
        """Open the UART connection.
        
        Establishes connection to the Pi's UART and initializes GPIO direction control
        if configured. The direction pin is set to receive mode by default.
        
        Raises:
            serial.SerialException: If the UART cannot be opened.
            Exception: For other connection errors.
            
        Note:
            Ensure the Pi UART is enabled and not used by the console before calling this.
        """
        if self._serial is not None and self._serial.is_open:
            logger.debug("Pi UART connection already open")
            return
        
        logger.info(f"Opening Pi UART: {self.port} at {self.baud} baud")
        
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
            
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()
            
            # Set direction to receive by default
            if self._direction_control is not None:
                self._direction_control.off()  # DE/RE low = receive mode
                logger.debug(f"Direction control set to receive mode (pin {self.direction_pin} = LOW)")
            
            logger.info("Pi UART opened successfully")
            
        except serial.SerialException as e:
            logger.error(f"Failed to open Pi UART: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error opening Pi UART: {e}")
            raise

    def close(self) -> None:
        """Close the UART connection.
        
        Safely closes the UART connection and cleans up GPIO resources.
        Close errors are logged but do not raise exceptions.
        """
        if self._serial is not None and self._serial.is_open:
            logger.info("Closing Pi UART")
            try:
                self._serial.close()
                logger.info("Pi UART closed successfully")
            except Exception as e:
                logger.warning(f"Error closing Pi UART: {e}")
        self._serial = None
        
        if self._direction_control is not None:
            logger.debug(f"Cleaning up GPIO direction control (pin {self.direction_pin})")
            try:
                self._direction_control.close()
                logger.debug("GPIO direction control cleaned up successfully")
            except Exception as e:
                logger.warning(f"Error cleaning up GPIO direction control: {e}")

    def write(self, data: bytes) -> int:
        """Write data to the UART.
        
        Sends data to the UART with automatic direction control for half-duplex operation.
        Direction pin is set to transmit mode, data is sent and flushed, then direction
        is returned to receive mode.
        
        Args:
            data (bytes): Bytes to transmit.
            
        Returns:
            int: Number of bytes written.
            
        Raises:
            RuntimeError: If transport is not open.
            serial.SerialException: If write operation fails.
            Exception: For other write errors.
        """
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("Transport not open")
        
        logger.debug(f"Writing {len(data)} bytes: {data.hex()}")
        
        # Set direction to transmit
        if self._direction_control is not None:
            logger.debug(f"Setting direction to transmit (pin {self.direction_pin} = HIGH)")
            self._direction_control.on()  # DE/RE high = transmit mode
            
        try:
            written = self._serial.write(data)
            self._serial.flush()  # Ensure data is sent before switching direction
            bytes_written = written if written is not None else 0
            logger.debug(f"Write completed: {bytes_written} bytes")
            return bytes_written
            
        except serial.SerialException as e:
            logger.error(f"Pi UART write error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Pi UART write: {e}")
            raise
        finally:
            # Set direction back to receive
            if self._direction_control is not None:
                logger.debug(f"Setting direction to receive (pin {self.direction_pin} = LOW)")
                self._direction_control.off()  # DE/RE low = receive mode

    def read(self, size: int, timeout: Optional[float] = None) -> bytes:
        """Read data from the UART.
        
        Reads data from the UART with direction control ensured to be in receive mode.
        May return fewer bytes than requested if timeout occurs.
        
        Args:
            size (int): Maximum number of bytes to read.
            timeout (Optional[float]): Read timeout in seconds (None uses instance default).
            
        Returns:
            bytes: Bytes read from the UART (may be shorter than requested).
            
        Raises:
            RuntimeError: If transport is not open.
            serial.SerialException: If read operation fails.
            Exception: For other read errors.
        """
        if self._serial is None or not self._serial.is_open:
            raise RuntimeError("Transport not open")
            
        effective_timeout = timeout if timeout is not None else self.timeout
        logger.debug(f"Reading up to {size} bytes (timeout={effective_timeout}s)")
            
        # Ensure direction is set to receive
        if self._direction_control is not None:
            self._direction_control.off()  # DE/RE low = receive mode
            
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
            logger.error(f"Pi UART read error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Pi UART read: {e}")
            raise

    def __repr__(self) -> str:
        """String representation for debugging.
        
        Returns:
            str: Human-readable representation showing port, baud rate, direction pin, and status.
        """
        status = "open" if (self._serial and self._serial.is_open) else "closed"
        dir_pin = f", dir_pin={self.direction_pin}" if self.direction_pin else ""
        return f"PiUartGpio(port='{self.port}', baud={self.baud}{dir_pin}, {status})"
