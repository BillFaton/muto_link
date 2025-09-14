# Quick Start

This guide will get you controlling servos with Muto Link in just a few minutes.

## Prerequisites

Before starting, make sure you have:

- [Muto Link installed](installation.md)
- A Muto baseboard connected to your computer
- At least one servo connected to the baseboard
- The correct serial port identified

## Your First Servo Program

Let's create a simple program to move a servo:

### 1. Find Your Serial Port

=== "Linux"
    ```bash
    # List available ports
    ls /dev/ttyUSB* /dev/ttyACM*
    
    # Common ports:
    # /dev/ttyUSB0 - USB Serial adapter
    # /dev/ttyACM0 - Arduino-style boards
    ```

=== "Windows"
    ```bash
    # Check Device Manager or use PowerShell:
    Get-WmiObject -Class Win32_SerialPort | Select-Object Name,DeviceID
    
    # Common ports: COM3, COM4, COM5
    ```

=== "macOS"
    ```bash
    # List available ports
    ls /dev/tty.usb* /dev/cu.usb*
    
    # Common ports:
    # /dev/tty.usbserial-*
    # /dev/cu.usbserial-*
    ```

### 2. Basic Servo Control

Create a file called `servo_test.py`:

```python
from muto_link import Driver, UsbSerial

# Replace with your serial port
port = "/dev/ttyUSB0"  # Linux/macOS
# port = "COM3"        # Windows

# Create transport and driver
transport = UsbSerial(port)
driver = Driver(transport)

try:
    # Open connection
    driver.open()
    print("Connected to Muto baseboard")
    
    # Enable servo control
    driver.torque_on()
    print("Servo control enabled")
    
    # Move servo 1 to center position (90 degrees) at medium speed
    servo_id = 1
    angle = 90
    speed = 1000
    
    driver.servo_move(servo_id, angle, speed)
    print(f"Moving servo {servo_id} to {angle}° at speed {speed}")
    
    # Wait a moment, then read the position
    import time
    time.sleep(2)
    
    response = driver.read_servo_angle(servo_id)
    print(f"Servo position response: {response.hex()}")
    
finally:
    # Always clean up
    driver.close()
    print("Connection closed")
```

Run the program:

```bash
python servo_test.py
```

### 3. Using Context Manager (Recommended)

The cleaner way to handle connections:

```python
from muto_link import Driver, UsbSerial
import time

# Replace with your serial port
port = "/dev/ttyUSB0"  # Adjust for your system

with Driver(UsbSerial(port)) as driver:
    print("Connected!")
    
    # Enable servo control
    driver.torque_on()
    
    # Move multiple servos
    servos = [1, 2, 3]  # Servo IDs to control
    
    for servo_id in servos:
        # Move to 45 degrees
        driver.servo_move(servo_id, 45, 800)
        print(f"Servo {servo_id} -> 45°")
        time.sleep(1)
        
        # Move to 135 degrees
        driver.servo_move(servo_id, 135, 800)
        print(f"Servo {servo_id} -> 135°")
        time.sleep(1)
        
        # Return to center
        driver.servo_move(servo_id, 90, 800)
        print(f"Servo {servo_id} -> 90°")
        time.sleep(1)
    
    print("Servo dance complete!")
# Connection automatically closed
```

## Command Line Quick Test

You can also test using the command-line interface:

```bash
# Enable servo control
muto torque --on

# Move servo 1 to 90 degrees
muto servo --id 1 --angle 90 --speed 1000

# Read servo position
muto read-angle --id 1

# Use a different port
muto --port COM3 servo --id 1 --angle 45 --speed 500
```

## Common Issues and Solutions

### Permission Denied

If you get permission errors on Linux/macOS:

```bash
# Add your user to the dialout group
sudo usermod -a -G dialout $USER
# Log out and back in
```

### No Response from Servo

1. **Check connections**: Ensure servo is properly connected to baseboard
2. **Verify power**: Make sure baseboard has adequate power supply
3. **Enable torque**: Always call `driver.torque_on()` before moving servos
4. **Check servo ID**: Ensure you're using the correct servo ID

### Wrong Serial Port

```python
# Test connection without servo commands
try:
    with Driver(UsbSerial("/dev/ttyUSB0")) as driver:
        print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
    print("Try a different port")
```

## Understanding the Protocol

Muto Link handles the low-level protocol automatically, but it's useful to understand the basics:

```python
# These are equivalent:
driver.servo_move(1, 90, 1000)

# Low-level version:
addr = 0x40  # Servo move command address
data = bytes([1, 90, 0x03, 0xE8])  # servo_id, angle, speed_hi, speed_lo
driver.write(addr, data)
```

## Next Steps

Now that you have basic servo control working:

1. **[Basic Usage](user-guide/basic-usage.md)** - Learn all the available commands
2. **[CLI Guide](user-guide/cli.md)** - Master the command-line interface

## Complete Example

Here's a more complete example showing various features:

```python
from muto_link import Driver, UsbSerial
import time

def main():
    port = "/dev/ttyUSB0"  # Adjust for your system
    
    with Driver(UsbSerial(port, timeout=0.1)) as driver:
        print("🔗 Connected to Muto baseboard")
        
        # Enable servo control
        driver.torque_on()
        print("⚡ Servo control enabled")
        
        # Servo configuration
        servos = [1, 2, 3]
        positions = [45, 90, 135]
        
        # Move all servos to different positions
        for servo_id, angle in zip(servos, positions):
            driver.servo_move(servo_id, angle, 1200)
            print(f"📍 Servo {servo_id} moving to {angle}°")
        
        # Wait for movement to complete
        time.sleep(2)
        
        # Read all positions
        print("\n📊 Reading servo positions:")
        for servo_id in servos:
            try:
                response = driver.read_servo_angle(servo_id)
                print(f"   Servo {servo_id}: {response.hex()}")
            except Exception as e:
                print(f"   Servo {servo_id}: Error - {e}")
        
        # Disable servo control (allows manual positioning)
        driver.torque_off()
        print("\n🔓 Servo control disabled - servos can be moved manually")

if __name__ == "__main__":
    main()
```

This example demonstrates connection management, servo control, position reading, and proper cleanup. Use it as a template for your own projects!
