# Muto Link

**Muto Link** is a Python library for controlling servo motors on the Muto baseboard. It provides both a high-level API for servo control and a command-line interface.

## Installation

```bash
pip install muto-link
```

For Raspberry Pi GPIO support:
```bash
pip install "muto-link[pi]"
```

## Quick Start

```python
from muto_link import Driver, UsbSerial

# Connect via USB serial
transport = UsbSerial("/dev/ttyUSB0")  # or "COM3" on Windows
driver = Driver(transport)

# Use context manager for automatic connection handling
with driver:
    # Enable servo control
    driver.torque_on()
    
    # Move servo 5 to 90 degrees at speed 400
    driver.servo_move(servo_id=5, angle=90, speed=400)
    
    # Read servo position
    response = driver.read_servo_angle(servo_id=5)
    print(f"Servo position: {response.hex()}")
```

## API Reference

### Driver Class

The main interface for servo control.

```python
from muto_link import Driver

driver = Driver(transport)
```

#### Connection Management
- `driver.open()` - Open connection
- `driver.close()` - Close connection
- Context manager support: `with driver: ...`

#### Servo Control
- `driver.torque_on()` - Enable servo control
- `driver.torque_off()` - Disable servo control (allows manual positioning)
- `driver.servo_move(servo_id, angle, speed)` - Move servo to angle (0-180°) at speed (0-65535)
- `driver.read_servo_angle(servo_id)` - Read current servo position
- `driver.calibrate_servo(servo_id, deviation)` - Calibrate servo position offset

#### Low-Level Access
- `driver.write(addr, data)` - Send write command
- `driver.read(addr, data)` - Send read command and return response

### Transport Classes

#### UsbSerial
For USB serial connections (most common).

```python
from muto_link import UsbSerial

transport = UsbSerial(
    port="/dev/ttyUSB0",  # "/dev/ttyUSB0" (Linux), "COM3" (Windows)
    baud=115200,          # Default baud rate
    timeout=0.05          # Read timeout in seconds
)
```

#### PiUartGpio
For Raspberry Pi UART with optional GPIO direction control.

```python
from muto_link import PiUartGpio

transport = PiUartGpio(
    port="/dev/serial0",
    baud=115200,
    direction_pin=17      # Optional GPIO pin for half-duplex control
)
```

## Usage Examples

### Basic Servo Control

```python
from muto_link import Driver, UsbSerial

transport = UsbSerial("/dev/ttyUSB0")
driver = Driver(transport)

try:
    driver.open()
    driver.torque_on()
    
    # Move multiple servos
    for servo_id in range(1, 6):
        driver.servo_move(servo_id, 90, 1000)
        
finally:
    driver.close()
```

### Reading Servo Positions

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    # Read positions of servos 1-5
    for servo_id in range(1, 6):
        response = driver.read_servo_angle(servo_id)
        print(f"Servo {servo_id}: {response.hex()}")
```

### Raspberry Pi UART

```python
from muto_link import Driver, PiUartGpio

# Standard UART
transport = PiUartGpio("/dev/serial0")

# UART with direction control for half-duplex
transport = PiUartGpio("/dev/serial0", direction_pin=17)

with Driver(transport) as driver:
    driver.torque_on()
    driver.servo_move(1, 45, 500)
```

## Command Line Interface

Muto Link includes a CLI for quick testing and scripting.

```bash
# Enable servo control
muto torque --on

# Move servo 5 to 90 degrees
muto servo --id 5 --angle 90 --speed 400

# Read servo angle
muto read-angle --id 5

# Use different port
muto --port COM3 servo --id 1 --angle 45 --speed 200

# Raspberry Pi UART
muto --backend pi servo --id 1 --angle 90 --speed 500
```

## Protocol Details

The Muto baseboard uses a custom serial protocol with the following frame format:

```
0x55 0x00 LEN INS ADDR DATA... CHK 0x00 0xAA
```

- **Header**: `0x55 0x00`
- **LEN**: Frame length (LEN through CHK)
- **INS**: Instruction (0x01=write, 0x02=read, 0x12=response)
- **ADDR**: Register address
- **DATA**: Command payload (big-endian for 16-bit values)
- **CHK**: Checksum = `255 - ((LEN + INS + ADDR + DATA...) % 256)`
- **Tail**: `0x00 0xAA`

### Key Registers

| Function | INS | ADDR | Data Format |
|----------|-----|------|-------------|
| Torque ON | 0x01 | 0x26 | `0x00` |
| Torque OFF | 0x01 | 0x27 | `0x00` |
| Move Servo | 0x01 | 0x40 | `servo_id, angle, speed_hi, speed_lo` |
| Read Angle | 0x02 | 0x50 | `servo_id` |
| Calibrate | 0x01 | 0x28 | `servo_id, dev_hi, dev_lo` |

## Raspberry Pi Setup

Enable UART in `raspi-config`:
1. Interface Options → Serial Port
2. Login shell over serial: **No**
3. Serial port hardware: **Yes**

For Docker on Pi:
```bash
docker run --device=/dev/serial0 --device=/dev/gpiomem your-image
```

## Troubleshooting

- **No servo movement**: Ensure `torque_on()` is called first
- **Communication errors**: Check baud rate (115200) and port permissions
- **Pi UART issues**: Verify UART is enabled and login shell disabled
- **Half-duplex problems**: Use `direction_pin` parameter for RS-485 transceivers

## License

MIT
