# Basic Usage

This guide covers the fundamental concepts and operations in Muto Link for everyday servo control tasks.

## Core Concepts

### Driver and Transport

Muto Link uses a two-layer architecture:

- **Driver**: High-level API for servo control
- **Transport**: Hardware communication layer (USB Serial, Pi UART, etc.)

```python
from muto_link import Driver, UsbSerial

# Create transport for your hardware
transport = UsbSerial("/dev/ttyUSB0")

# Create driver with the transport
driver = Driver(transport)
```

### Connection Management

Always manage connections properly:

```python
# Manual connection management
driver.open()
try:
    # Your servo operations here
    pass
finally:
    driver.close()

# Recommended: Use context manager
with driver:
    # Your servo operations here
    pass  # Connection automatically closed
```

## Essential Operations

### 1. Enable/Disable Servo Control

Before moving servos, you must enable torque:

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    # Enable servo control - servos hold position
    driver.torque_on()
    
    # Your servo movements here
    
    # Disable servo control - servos can be moved manually
    driver.torque_off()
```

!!! warning "Important"
    Always call `torque_on()` before attempting to move servos. Without this, servo movement commands will have no effect.

### 2. Basic Servo Movement

Move servos with precise angle and speed control:

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    # Basic movement: servo_move(servo_id, angle, speed)
    driver.servo_move(servo_id=1, angle=90, speed=1000)
    
    # Parameters:
    # servo_id: 1-255 (check your servo configuration)
    # angle: 0-180 degrees
    # speed: 0-65535 (higher = faster)
```

#### Speed Guidelines

- **Slow**: 200-500 - Smooth, precise movements
- **Medium**: 800-1500 - Good balance of speed and control
- **Fast**: 2000-5000 - Quick movements
- **Maximum**: 10000+ - Fastest possible (may cause jerky motion)

### 3. Reading Servo Positions

Get current servo positions:

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    # Read servo position
    response = driver.read_servo_angle(servo_id=1)
    print(f"Raw response: {response.hex()}")
    
    # The response is raw bytes from the servo
    # You'll need to parse it according to your servo specifications
```

### 4. Servo Calibration

Adjust servo center positions:

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    # Calibrate servo offset
    # deviation: signed 16-bit value (-32768 to 32767)
    driver.calibrate_servo(servo_id=1, deviation=100)
    
    # Negative deviation rotates counterclockwise
    driver.calibrate_servo(servo_id=2, deviation=-50)
```

## Working with Multiple Servos

### Sequential Control

Move servos one after another:

```python
import time

with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    servos = [1, 2, 3, 4, 5]
    target_angle = 90
    
    for servo_id in servos:
        driver.servo_move(servo_id, target_angle, 1000)
        time.sleep(0.5)  # Brief pause between movements
```

### Synchronized Movement

Start all movements at once:

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    # Define movements
    movements = [
        (1, 45, 1200),   # servo 1 to 45° at speed 1200
        (2, 90, 1000),   # servo 2 to 90° at speed 1000  
        (3, 135, 800),   # servo 3 to 135° at speed 800
        (4, 60, 1500),   # servo 4 to 60° at speed 1500
    ]
    
    # Send all commands quickly
    for servo_id, angle, speed in movements:
        driver.servo_move(servo_id, angle, speed)
    
    # Wait for completion
    time.sleep(2)
```

### Reading Multiple Servos

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    servo_ids = [1, 2, 3, 4, 5]
    
    print("Current servo positions:")
    for servo_id in servo_ids:
        try:
            response = driver.read_servo_angle(servo_id)
            print(f"  Servo {servo_id}: {response.hex()}")
        except Exception as e:
            print(f"  Servo {servo_id}: Error - {e}")
```

## Error Handling

Handle common errors gracefully:

```python
from muto_link import Driver, UsbSerial

def safe_servo_control():
    try:
        with Driver(UsbSerial("/dev/ttyUSB0", timeout=0.1)) as driver:
            driver.torque_on()
            driver.servo_move(1, 90, 1000)
            
    except FileNotFoundError:
        print("Serial port not found. Check your connection.")
    except PermissionError:
        print("Permission denied. Check user permissions for serial port.")
    except TimeoutError:
        print("Communication timeout. Check baseboard connection.")
    except Exception as e:
        print(f"Unexpected error: {e}")

safe_servo_control()
```

## Parameter Validation

Muto Link automatically validates and clamps parameters:

```python
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    # These values will be automatically clamped to valid ranges:
    driver.servo_move(1, 200, 70000)  # angle -> 180, speed -> 65535
    driver.servo_move(2, -10, -100)   # angle -> 0, speed -> 0
    
    # Servo IDs are also validated (1-255)
    # driver.servo_move(0, 90, 1000)  # Would raise ValueError
```

## Transport Configuration

### USB Serial Options

```python
from muto_link import UsbSerial

# Basic configuration
transport = UsbSerial("/dev/ttyUSB0")

# Advanced configuration
transport = UsbSerial(
    port="/dev/ttyUSB0",
    baud=115200,        # Baud rate (default: 115200)
    timeout=0.05        # Read timeout in seconds (default: 0.05)
)
```

### Raspberry Pi UART

```python
from muto_link import PiUartGpio

# Basic UART
transport = PiUartGpio("/dev/serial0")

# With direction control for half-duplex RS-485
transport = PiUartGpio(
    port="/dev/serial0",
    baud=115200,
    direction_pin=17    # GPIO pin for TX/RX control
)
```

## Best Practices

### 1. Always Use Context Managers

```python
# ✅ Good - Automatic cleanup
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    # ... your code ...

# ❌ Avoid - Manual cleanup required
driver = Driver(UsbSerial("/dev/ttyUSB0"))
driver.open()
# ... your code ...
driver.close()  # Easy to forget!
```

### 2. Handle Servo Limits

```python
def safe_servo_move(driver, servo_id, angle, speed):
    # Clamp to safe ranges
    angle = max(0, min(180, angle))
    speed = max(0, min(5000, speed))  # Reasonable speed limit
    
    driver.servo_move(servo_id, angle, speed)
```

### 3. Add Delays for Physical Movement

```python
import time

with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    
    # Large movements need time to complete
    driver.servo_move(1, 0, 1000)
    time.sleep(1)  # Wait for movement
    
    driver.servo_move(1, 180, 1000)
    time.sleep(1)  # Wait for movement
```

### 4. Graceful Shutdown

```python
import signal
import sys

driver = None

def signal_handler(sig, frame):
    if driver:
        driver.torque_off()  # Disable servos
        driver.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Your main program
with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
    driver.torque_on()
    # ... your servo control code ...
```

## Next Steps

Now that you understand basic usage:

- [CLI Guide](cli.md) - Command-line interface for testing
- [API Reference](../api-reference/) - Complete method documentation
