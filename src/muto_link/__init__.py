"""Muto Link - Python library for Muto baseboard servo control.

This library provides a high-level API for controlling servo motors connected to
the Muto baseboard via serial communication protocols.

Basic usage:
    >>> from muto_link import Driver, UsbSerial
    >>> with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    ...     driver.torque_on()
    ...     driver.servo_move(servo_id=1, angle=90, speed=1000)
"""

from .core.driver import Driver
from .core.sensor import Sensor, IMUAngleData, RawIMUData
from .transports.usb_serial import UsbSerial
from .transports.pi_uart_gpio import PiUartGpio
from .transports.base import Transport
from . import logging

__version__ = "0.1.0"

__all__ = [
    "Driver",
    "Sensor",
    "IMUAngleData",
    "RawIMUData",
    "UsbSerial", 
    "PiUartGpio",
    "Transport",
    "logging",
]
