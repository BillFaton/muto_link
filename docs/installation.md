# Installation

This guide will help you install Muto Link on your system. The library supports Python 3.11+ and works on Linux, Windows, and macOS.

## Prerequisites

- **Python 3.11 or higher**
- **pip** (Python package installer)
- **Serial port access** (see platform-specific notes below)

## Standard Installation

Install Muto Link using pip:

```bash
pip install muto-link
```

This installs the core library with USB Serial support, which works on all platforms.

## Raspberry Pi Installation

For Raspberry Pi GPIO support, install with the `pi` extra:

```bash
pip install "muto-link[pi]"
```

This adds GPIO control capabilities for direct UART communication and half-duplex RS-485 support.

## Development Installation

For development or contributing to the project:

```bash
# Clone the repository
git clone https://github.com/billfaton/muto_link.git
cd muto_link

# Install in development mode
pip install -e ".[dev]"

# Or with all extras
pip install -e ".[pi,dev]"
```

## Platform-Specific Setup

### Linux

Most Linux distributions require adding your user to the `dialout` group for serial port access:

```bash
sudo usermod -a -G dialout $USER
```

Log out and back in for the changes to take effect.

#### Common Serial Ports
- USB Serial: `/dev/ttyUSB0`, `/dev/ttyACM0`
- Raspberry Pi UART: `/dev/serial0`, `/dev/ttyAMA0`

### Windows

Windows typically works out of the box. Common serial ports:
- USB Serial: `COM3`, `COM4`, `COM5`, etc.

You can find available ports in Device Manager under "Ports (COM & LPT)".

### macOS

macOS usually works without additional setup. Common serial ports:
- USB Serial: `/dev/tty.usbserial-*`, `/dev/cu.usbserial-*`

## Raspberry Pi Specific Setup

### Enable UART

For Raspberry Pi UART communication, enable the serial port:

1. Run `sudo raspi-config`
2. Go to **Interface Options** → **Serial Port**
3. Choose **No** for "login shell over serial"
4. Choose **Yes** for "serial port hardware enabled"
5. Reboot your Pi

### Verify UART Access

Check that the UART is available:

```bash
ls -la /dev/serial*
# Should show: /dev/serial0 -> ttyAMA0 (or similar)
```

### GPIO Permissions

For GPIO control (direction pin for half-duplex), your user needs access to `/dev/gpiomem`:

```bash
sudo usermod -a -G gpio $USER
```

## Verify Installation

Test your installation with a simple script:

```python
# test_installation.py
from muto_link import Driver, UsbSerial

print("Muto Link installed successfully!")
print(f"Available classes: {[cls.__name__ for cls in [Driver, UsbSerial]]}")

# Test basic import
try:
    from muto_link import PiUartGpio
    print("Raspberry Pi support: Available")
except ImportError:
    print("Raspberry Pi support: Not installed (use pip install 'muto-link[pi]')")
```

Run the test:

```bash
python test_installation.py
```

## Docker Installation

For containerized environments:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    udev \
    && rm -rf /var/lib/apt/lists/*

# Install Muto Link
RUN pip install muto-link

# For Raspberry Pi support in container
# RUN pip install "muto-link[pi]"
```

### Docker on Raspberry Pi

To use GPIO and serial ports in Docker on Raspberry Pi:

```bash
docker run --device=/dev/serial0 --device=/dev/gpiomem your-image
```

## Troubleshooting

### Permission Denied Errors

If you get "Permission denied" when accessing serial ports:

**Linux/macOS:**
```bash
# Check current groups
groups

# Add to dialout group (Linux)
sudo usermod -a -G dialout $USER

# Or add to specific group on macOS
sudo dseditgroup -o edit -a $USER -t user wheel
```

**Windows:**  
Run your terminal/IDE as Administrator, or check Device Manager for driver issues.

### Import Errors

**ModuleNotFoundError: No module named 'muto_link'**

Ensure you're using the correct Python environment:
```bash
which python
pip list | grep muto
```

**GPIO/Pi-specific imports failing:**

Install the Pi extras:
```bash
pip install "muto-link[pi]"
```

### Serial Port Not Found

**Linux:**
```bash
# List available serial ports
ls /dev/tty*
dmesg | grep tty  # Check system messages
```

**Windows:**
```bash
# PowerShell: List COM ports
Get-WmiObject -Class Win32_SerialPort | Select-Object Name,DeviceID
```

**macOS:**
```bash
ls /dev/tty.*
ls /dev/cu.*
```

## Next Steps

Once installed, proceed to:

- [Quick Start](getting-started.md) - Your first servo control program
- [Basic Usage](user-guide/basic-usage.md) - Learn the core concepts
- [Raspberry Pi Setup](user-guide/raspberry-pi.md) - Pi-specific configuration

## Dependencies

Muto Link has minimal dependencies:

- **Core**: `pyserial>=3.5`, `typer>=0.12.0`
- **Pi extras**: `gpiozero>=2.0`
- **Development**: `pytest>=6.0`

All dependencies are automatically installed when you install Muto Link.
