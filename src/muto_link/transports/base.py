"""
Abstract base transport interface for Muto communication.
"""

from abc import ABC, abstractmethod
from typing import Optional


class Transport(ABC):
    """Abstract base class for Muto communication transports."""

    @abstractmethod
    def open(self) -> None:
        """
        Open the transport connection.
        
        Raises:
            Exception: If connection cannot be established
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the transport connection.
        
        Should be safe to call multiple times.
        """
        pass

    @abstractmethod
    def write(self, data: bytes) -> int:
        """
        Write data to the transport.
        
        Args:
            data: Bytes to write
            
        Returns:
            Number of bytes written
            
        Raises:
            Exception: If write fails or transport not open
        """
        pass

    @abstractmethod
    def read(self, size: int, timeout: Optional[float] = None) -> bytes:
        """
        Read data from the transport.
        
        Args:
            size: Number of bytes to read
            timeout: Read timeout in seconds, None for blocking
            
        Returns:
            Bytes read (may be less than requested)
            
        Raises:
            Exception: If read fails or transport not open
        """
        pass

    def __enter__(self) -> "Transport":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
