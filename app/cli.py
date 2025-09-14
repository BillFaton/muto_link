"""
CLI interface for Muto servo control.
"""

import sys
from typing import Optional

import typer
from typing_extensions import Annotated

from muto_link.core.driver import Driver
from muto_link.transports.usb_serial import UsbSerial
from muto_link.transports.pi_uart_gpio import PiUartGpio
from muto_link.logging import get_logger, set_global_log_level

logger = get_logger(__name__)

app = typer.Typer(
    name="muto",
    help="Control Muto baseboard servos",
    no_args_is_help=True,
)


def create_transport(
    backend: str,
    port: str,
    baud: int,
    dir_pin: Optional[int],
    log_level: Optional[str] = None,
) -> UsbSerial | PiUartGpio:
    """Create transport based on backend choice."""
    if log_level:
        logger.info(f"Setting log level to {log_level}")
        set_global_log_level(log_level)
    
    logger.info(f"Creating {backend} transport: port={port}, baud={baud}, dir_pin={dir_pin}")
    
    if backend.lower() == "usb":
        return UsbSerial(port=port, baud=baud)
    elif backend.lower() == "pi":
        return PiUartGpio(baud=baud, direction_pin=dir_pin)
    else:
        logger.error(f"Unknown backend: {backend}")
        typer.echo(f"Error: Unknown backend '{backend}'. Use 'usb' or 'pi'.", err=True)
        raise typer.Exit(1)


@app.command()
def torque(
    on: Annotated[bool, typer.Option("--on", help="Turn torque on")] = False,
    off: Annotated[bool, typer.Option("--off", help="Turn torque off")] = False,
    backend: Annotated[str, typer.Option("--backend", help="Transport backend to use")] = "usb",
    port: Annotated[str, typer.Option("--port", help="Serial port (USB backend only)")] = "/dev/ttyUSB0",
    baud: Annotated[int, typer.Option("--baud", help="Baud rate")] = 115200,
    dir_pin: Annotated[Optional[int], typer.Option("--dir-pin", help="Direction control GPIO pin (Pi backend only)")] = None,
    log_level: Annotated[Optional[str], typer.Option("--log-level", help="Log level (DEBUG, INFO, WARN, ERROR)")] = None,
) -> None:
    """Control servo torque."""
    if on == off:  # Both True or both False
        logger.error("Invalid torque command: must specify either --on or --off")
        typer.echo("Error: Specify either --on or --off", err=True)
        raise typer.Exit(1)

    action = "ON" if on else "OFF"
    logger.info(f"Torque command: {action}")

    try:
        transport = create_transport(backend, port, baud, dir_pin, log_level)
        with Driver(transport) as driver:
            if on:
                driver.torque_on()
                typer.echo("Torque ON")
                logger.info("Torque enabled successfully")
            else:
                driver.torque_off()
                typer.echo("Torque OFF")
                logger.info("Torque disabled successfully")
    except Exception as e:
        logger.error(f"Torque command failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def servo(
    servo_id: Annotated[int, typer.Option("--id", help="Servo ID (1-18)")],
    angle: Annotated[int, typer.Option("--angle", help="Target angle (0-180)")],
    speed: Annotated[int, typer.Option("--speed", help="Movement speed (0-65535)")],
    backend: Annotated[str, typer.Option("--backend", help="Transport backend to use")] = "usb",
    port: Annotated[str, typer.Option("--port", help="Serial port (USB backend only)")] = "/dev/ttyUSB0",
    baud: Annotated[int, typer.Option("--baud", help="Baud rate")] = 115200,
    dir_pin: Annotated[Optional[int], typer.Option("--dir-pin", help="Direction control GPIO pin (Pi backend only)")] = None,
    log_level: Annotated[Optional[str], typer.Option("--log-level", help="Log level (DEBUG, INFO, WARN, ERROR)")] = None,
) -> None:
    """Move a servo to specified position."""
    logger.info(f"Servo move command: servo_id={servo_id}, angle={angle}, speed={speed}")
    
    try:
        transport = create_transport(backend, port, baud, dir_pin, log_level)
        with Driver(transport) as driver:
            driver.servo_move(servo_id, angle, speed)
            typer.echo(f"Servo {servo_id} -> {angle}° @ speed {speed}")
            logger.info(f"Servo {servo_id} move command completed successfully")
    except Exception as e:
        logger.error(f"Servo move command failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def read_angle(
    servo_id: Annotated[int, typer.Option("--id", help="Servo ID (1-18)")],
    backend: Annotated[str, typer.Option("--backend", help="Transport backend to use")] = "usb",
    port: Annotated[str, typer.Option("--port", help="Serial port (USB backend only)")] = "/dev/ttyUSB0",
    baud: Annotated[int, typer.Option("--baud", help="Baud rate")] = 115200,
    dir_pin: Annotated[Optional[int], typer.Option("--dir-pin", help="Direction control GPIO pin (Pi backend only)")] = None,
    log_level: Annotated[Optional[str], typer.Option("--log-level", help="Log level (DEBUG, INFO, WARN, ERROR)")] = None,
) -> None:
    """Read current servo angle."""
    logger.info(f"Read angle command: servo_id={servo_id}")
    
    try:
        transport = create_transport(backend, port, baud, dir_pin, log_level)
        with Driver(transport) as driver:
            response = driver.read_servo_angle(servo_id)
            # Response format is implementation-specific
            # Display as hex for now since exact format isn't specified
            typer.echo(f"Servo {servo_id} angle data: {response.hex()}")
            logger.info(f"Read angle command completed: servo_id={servo_id}, response={response.hex()}")
    except Exception as e:
        logger.error(f"Read angle command failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def calibrate(
    servo_id: Annotated[int, typer.Option("--id", help="Servo ID (1-18)")],
    deviation: Annotated[int, typer.Option("--deviation", help="Calibration deviation (0-65535)")],
    backend: Annotated[str, typer.Option("--backend", help="Transport backend to use")] = "usb",
    port: Annotated[str, typer.Option("--port", help="Serial port (USB backend only)")] = "/dev/ttyUSB0",
    baud: Annotated[int, typer.Option("--baud", help="Baud rate")] = 115200,
    dir_pin: Annotated[Optional[int], typer.Option("--dir-pin", help="Direction control GPIO pin (Pi backend only)")] = None,
    log_level: Annotated[Optional[str], typer.Option("--log-level", help="Log level (DEBUG, INFO, WARN, ERROR)")] = None,
) -> None:
    """Calibrate servo position deviation."""
    logger.info(f"Calibrate command: servo_id={servo_id}, deviation={deviation}")
    
    try:
        transport = create_transport(backend, port, baud, dir_pin, log_level)
        with Driver(transport) as driver:
            driver.calibrate_servo(servo_id, deviation)
            typer.echo(f"Servo {servo_id} calibrated with deviation {deviation}")
            logger.info(f"Calibrate command completed successfully: servo_id={servo_id}")
    except Exception as e:
        logger.error(f"Calibrate command failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def battery(
    backend: Annotated[str, typer.Option("--backend", help="Transport backend to use")] = "usb",
    port: Annotated[str, typer.Option("--port", help="Serial port (USB backend only)")] = "/dev/ttyUSB0",
    baud: Annotated[int, typer.Option("--baud", help="Baud rate")] = 115200,
    dir_pin: Annotated[Optional[int], typer.Option("--dir-pin", help="Direction control GPIO pin (Pi backend only)")] = None,
    log_level: Annotated[Optional[str], typer.Option("--log-level", help="Log level (DEBUG, INFO, WARN, ERROR)")] = None,
) -> None:
    """Read battery level."""
    logger.info("Battery level command")
    
    try:
        transport = create_transport(backend, port, baud, dir_pin, log_level)
        with Driver(transport) as driver:
            response = driver.read_battery_level()
            typer.echo(f"Battery level: {response}")
            logger.info(f"Battery level command completed: response={response.hex()}")
    except Exception as e:
        logger.error(f"Battery level command failed: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
