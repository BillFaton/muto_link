# Troubleshooting

This guide covers common issues when using Muto Link and how to resolve them.

## Connection Issues

### Serial Port Not Found

**Error Messages:**
- `FileNotFoundError: [Errno 2] No such file or directory: '/dev/ttyUSB0'`
- `serial.serialutil.SerialException: could not open port 'COM3'`

**Solutions:**

=== "Linux"
    ```bash
    # List available serial ports
    ls /dev/tty*
    
    # Look for USB serial devices
    ls /dev/ttyUSB* /dev/ttyACM*
    
    # Check system messages for USB devices
    dmesg | grep tty
    ```

=== "Windows"
    ```powershell
    # List COM ports in PowerShell
    Get-WmiObject -Class Win32_SerialPort | Select-Object Name,DeviceID
    
    # Or check Device Manager → Ports (COM & LPT)
    ```

=== "macOS"
    ```bash
    # List available serial ports
    ls /dev/tty.* /dev/cu.*
    
    # Look specifically for USB serial
    ls /dev/tty.usb* /dev/cu.usb*
    ```

### Permission Denied

**Error Messages:**
- `PermissionError: [Errno 13] Permission denied: '/dev/ttyUSB0'`
- `serial.serialutil.SerialException: [Errno 13] Permission denied`

**Solutions:**

=== "Linux"
    ```bash
    # Add user to dialout group
    sudo usermod -a -G dialout $USER
    
    # Log out and back in, or use:
    newgrp dialout
    
    # Verify group membership
    groups
    
    # Alternative: Temporary permission (not recommended)
    sudo chmod 666 /dev/ttyUSB0
    ```

=== "macOS"
    ```bash
    # Add user to specific groups
    sudo dseditgroup -o edit -a $USER -t user wheel
    sudo dseditgroup -o edit -a $USER -t user admin
    ```

=== "Windows"
    ```powershell
    # Run terminal/IDE as Administrator
    # Or check driver installation in Device Manager
    ```

### Device Busy

**Error Message:**
- `serial.serialutil.SerialException: [Errno 16] Device or resource busy: '/dev/ttyUSB0'`

**Solutions:**

```bash
# Find processes using the port (Linux)
sudo lsof /dev/ttyUSB0

# Kill the process if safe to do so
sudo kill <PID>

# Or restart the system to free all ports
```

## Communication Issues

### No Response from Servo

**Symptoms:**
- Servo doesn't move despite sending commands
- No error messages but no action

**Troubleshooting Steps:**

1. **Enable torque first:**
   ```python
   driver.torque_on()  # Must be called before servo movement
   ```

2. **Check power supply:**
   - Verify baseboard has adequate power (usually 6-12V)
   - Check LED indicators on baseboard
   - Ensure servos are properly connected

3. **Verify servo ID:**
   ```python
   # Make sure you're using the correct servo ID (1-18)
   driver.servo_move(servo_id=1, angle=90, speed=1000)  # Not 0!
   ```

4. **Test with CLI:**
   ```bash
   muto --log-level DEBUG torque --on
   muto --log-level DEBUG servo --id 1 --angle 90 --speed 1000
   ```

### Communication Timeout

**Error Messages:**
- `TimeoutError: Communication timeout`
- No response when reading servo positions

**Solutions:**

1. **Increase timeout:**
   ```python
   # Longer timeout for slower connections
   transport = UsbSerial("/dev/ttyUSB0", timeout=0.5)
   
   # Or when reading
   response = transport.read(10, timeout=2.0)
   ```

2. **Check cable connections:**
   - Ensure all connections are secure
   - Try a different USB cable
   - Check for electromagnetic interference

3. **Verify baud rate:**
   ```python
   # Most Muto baseboards use 115200 (default)
   transport = UsbSerial("/dev/ttyUSB0", baud=115200)
   
   # Some may use different rates
   transport = UsbSerial("/dev/ttyUSB0", baud=9600)
   ```

### Invalid Response

**Error Messages:**
- `RuntimeError: Invalid response header`
- `RuntimeError: Invalid frame length`

**Solutions:**

1. **Clear buffers:**
   ```python
   # Re-open connection to clear stale data
   driver.close()
   time.sleep(0.1)
   driver.open()
   ```

2. **Check for data corruption:**
   ```python
   # Enable debug logging to see raw data
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Verify protocol:**
   - Ensure you're connecting to a Muto baseboard
   - Check that no other software is communicating simultaneously

## Raspberry Pi Specific Issues

### UART Not Available

**Error Message:**
- `FileNotFoundError: [Errno 2] No such file or directory: '/dev/serial0'`

**Solutions:**

1. **Enable UART in raspi-config:**
   ```bash
   sudo raspi-config
   # Interface Options → Serial Port
   # Login shell over serial: No
   # Serial port hardware: Yes
   sudo reboot
   ```

2. **Verify UART device:**
   ```bash
   ls -la /dev/serial*
   # Should show: /dev/serial0 -> ttyAMA0
   
   # If not available, check:
   ls /dev/ttyAMA* /dev/ttyS*
   ```

3. **Check for Bluetooth conflicts:**
   ```bash
   # Disable Bluetooth if using primary UART
   sudo systemctl disable hciuart
   
   # Add to /boot/config.txt:
   # dtoverlay=disable-bt
   ```

### GPIO Permission Issues

**Error Messages:**
- Permission denied when using direction_pin
- GPIO-related errors

**Solutions:**

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Verify GPIO access
ls -la /dev/gpiomem

# For Docker containers
docker run --device=/dev/gpiomem your-image
```

## Software Issues

### Import Errors

**Error Messages:**
- `ModuleNotFoundError: No module named 'muto_link'`
- `ImportError: cannot import name 'PiUartGpio'`

**Solutions:**

1. **Verify installation:**
   ```bash
   pip list | grep muto
   which python
   ```

2. **Reinstall if needed:**
   ```bash
   pip uninstall muto-link
   pip install muto-link
   
   # Or with Pi support
   pip install "muto-link[pi]"
   ```

3. **Check Python environment:**
   ```bash
   # Make sure you're in the right environment
   python --version
   pip --version
   ```

### CLI Command Not Found

**Error Message:**
- `command not found: muto`

**Solutions:**

```bash
# Check if installed
pip show muto-link

# Reinstall with --force-reinstall
pip install --force-reinstall muto-link

# Or use python -m
python -m app.cli servo --id 1 --angle 90 --speed 1000
```

## Debugging Techniques

### Enable Debug Logging

```python
from muto_link.logging import set_global_log_level

# Enable maximum verbosity
set_global_log_level('DEBUG')

# Or via environment variable
import os
os.environ['MUTO_LOG_LEVEL'] = 'DEBUG'
```

```bash
# CLI with debug logging
MUTO_LOG_LEVEL=DEBUG muto servo --id 1 --angle 90 --speed 1000
```

### Test Connection Without Servos

```python
from muto_link import Driver, UsbSerial

def test_connection():
    try:
        transport = UsbSerial("/dev/ttyUSB0", timeout=1.0)
        with Driver(transport) as driver:
            print("✓ Connection successful")
            
            # Test basic command (should work even without servos)
            driver.torque_on()
            print("✓ Torque command sent")
            
            # Test read command
            try:
                battery = driver.read_battery_level()
                print(f"✓ Battery response: {battery.hex()}")
            except Exception as e:
                print(f"⚠ Battery read failed: {e}")
                
    except Exception as e:
        print(f"✗ Connection failed: {e}")

test_connection()
```

### Raw Communication Test

```python
def test_raw_communication():
    transport = UsbSerial("/dev/ttyUSB0", timeout=1.0)
    
    try:
        transport.open()
        
        # Send torque on command
        frame = bytes([0x55, 0x00, 0x05, 0x01, 0x26, 0x00, 0xD4, 0x00, 0xAA])
        written = transport.write(frame)
        print(f"Sent {written} bytes: {frame.hex()}")
        
        # Try to read any response
        response = transport.read(100, timeout=2.0)
        if response:
            print(f"Received: {response.hex()}")
        else:
            print("No response received")
            
    finally:
        transport.close()

test_raw_communication()
```

## Performance Issues

### Slow Servo Response

**Symptoms:**
- Servos move slowly despite high speed values
- Delayed response to commands

**Solutions:**

1. **Check speed values:**
   ```python
   # Higher values = faster movement
   driver.servo_move(1, 90, 5000)  # Fast
   driver.servo_move(1, 90, 500)   # Slow
   ```

2. **Optimize timeouts:**
   ```python
   # Shorter timeouts for faster operations
   transport = UsbSerial("/dev/ttyUSB0", timeout=0.01)
   ```

3. **Reduce logging overhead:**
   ```python
   # Use INFO or WARN level in production
   set_global_log_level('INFO')
   ```

### High CPU Usage

**Causes:**
- DEBUG logging in tight loops
- Very short timeouts causing rapid retries

**Solutions:**

```python
# Optimize for production
set_global_log_level('WARN')
transport = UsbSerial("/dev/ttyUSB0", timeout=0.05)

# Add delays in control loops
import time
for i in range(100):
    driver.servo_move(1, angle, speed)
    time.sleep(0.01)  # Small delay to reduce CPU load
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** with DEBUG level enabled
2. **Search GitHub Issues**: [muto_link issues](https://github.com/billfaton/muto_link/issues)
3. **Create a new issue** with:
   - Your operating system and Python version
   - Complete error message and stack trace
   - Minimal code example that reproduces the issue
   - Hardware setup description

## Hardware Checklist

Before reporting software issues, verify:

- [ ] Baseboard power LED is on
- [ ] Servo connections are secure
- [ ] USB/Serial cable is working (test with other devices)
- [ ] No loose connections
- [ ] Adequate power supply for your servo load
- [ ] Servo IDs are configured correctly (1-18)

## Common Error Patterns

| Error Type | Likely Cause | Quick Fix |
|------------|--------------|-----------|
| Permission denied | User not in dialout group | `sudo usermod -a -G dialout $USER` |
| Port not found | Wrong port path | Check `ls /dev/tty*` |
| Device busy | Another program using port | `sudo lsof /dev/ttyUSB0` |
| No servo response | Torque not enabled | Call `driver.torque_on()` first |
| Communication timeout | Cable/connection issue | Check connections, increase timeout |
| Invalid response | Protocol mismatch | Verify you're connected to Muto baseboard |

Most issues can be resolved by checking connections, permissions, and ensuring `torque_on()` is called before servo commands.
