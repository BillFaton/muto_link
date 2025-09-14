"""Core protocol implementation for Muto baseboard communication.

Frame format: header(0x55,0x00) LEN INS ADR DATA... CHK tail(0x00,0xAA)
"""

from ..logging import get_logger

logger = get_logger(__name__)


def build_frame(ins: int, addr: int, data: bytes) -> bytes:
    """Build a complete Muto protocol frame.
    
    Constructs a properly formatted frame according to the Muto protocol specification:
    Header(0x55,0x00) + LEN + INS + ADR + DATA + CHK + Tail(0x00,0xAA)
    
    Args:
        ins (int): Instruction byte - 0x01 for write, 0x02 for read, 0x12 for data return.
        addr (int): Address/register byte (0-255).
        data (bytes): Data payload as bytes (max 250 bytes to leave room for frame overhead).
        
    Returns:
        bytes: Complete frame as bytes ready for transmission.
        
    Raises:
        ValueError: If parameters are out of valid range.
        
    Example:
        >>> frame = build_frame(0x01, 0x26, bytes([0x00]))  # Torque ON command
    """
    if not (0 <= ins <= 255):
        raise ValueError(f"Instruction must be 0-255, got {ins}")
    if not (0 <= addr <= 255):
        raise ValueError(f"Address must be 0-255, got {addr}")
    if len(data) > 250:
        raise ValueError(f"Data too long: {len(data)} bytes (max 250)")
    
    logger.debug(f"Building frame: ins=0x{ins:02X}, addr=0x{addr:02X}, data_len={len(data)}")
    
    # Frame length includes LEN through CHK (8 = LEN + INS + ADR + CHK + frame overhead)
    frame_length = len(data) + 8
    payload = bytes([frame_length, ins, addr]) + data
    chk = checksum(payload)
    
    frame = (
        bytes([0x55, 0x00]) +    # Header
        payload +                # LEN + INS + ADR + DATA
        bytes([chk]) +          # CHK
        bytes([0x00, 0xAA])     # Tail
    )
    
    logger.debug(f"Frame built: len={frame_length}, checksum=0x{chk:02X}, total_size={len(frame)}")
    return frame


def checksum(payload: bytes) -> int:
    """Calculate Muto protocol checksum.
    
    Implements the checksum algorithm specified in the Muto protocol documentation.
    The checksum is calculated as the inverted low byte of the sum of all payload bytes.
    
    Formula: CHK = 255 - ((sum from LEN through DATA) % 256)
    
    Args:
        payload (bytes): Bytes to checksum - must include LEN, INS, ADR, and DATA but exclude CHK itself.
        
    Returns:
        int: Checksum byte (0-255).
        
    Raises:
        ValueError: If payload is empty.
        
    Note:
        The payload should contain the frame data from LEN through the last DATA byte,
        but should NOT include the checksum byte itself.
    """
    if not payload:
        raise ValueError("Payload cannot be empty")
    
    checksum_value = (255 - sum(payload)) % 256
    logger.debug(f"Checksum calculated: payload_sum={sum(payload) % 256}, checksum=0x{checksum_value:02X}")
    return checksum_value


def pack_uint16_be(value: int) -> bytes:
    """Pack a 16-bit unsigned integer as big-endian bytes.
    
    Converts an integer value to two bytes in big-endian (network) byte order,
    with the most significant byte first.
    
    Args:
        value (int): Integer value (0-65535).
        
    Returns:
        bytes: Two bytes in big-endian order [high_byte, low_byte].
        
    Raises:
        ValueError: If value is outside the valid 16-bit unsigned range.
        
    Example:
        >>> pack_uint16_be(1000)  # Returns bytes([0x03, 0xE8])
    """
    if not (0 <= value <= 0xFFFF):
        raise ValueError(f"Value must be 0-65535, got {value}")
    
    return bytes([(value >> 8) & 0xFF, value & 0xFF])


def unpack_uint16_be(data: bytes) -> int:
    """Unpack big-endian bytes to a 16-bit unsigned integer.
    
    Converts two bytes in big-endian (network) byte order to an integer value.
    
    Args:
        data (bytes): Exactly 2 bytes in big-endian order [high_byte, low_byte].
        
    Returns:
        int: Integer value (0-65535).
        
    Raises:
        ValueError: If data is not exactly 2 bytes.
        
    Example:
        >>> unpack_uint16_be(bytes([0x03, 0xE8]))  # Returns 1000
    """
    if len(data) != 2:
        raise ValueError(f"Expected 2 bytes, got {len(data)}")
    
    return (data[0] << 8) | data[1]
