# Muto Link

**Muto Link** is a Python library for controlling servo motors on the Muto baseboard. It provides both a high-level API for servo control and a command-line interface with hardware-agnostic serial communication support.

## Features

✨ **Easy to Use** - Simple, intuitive API for servo control  
🔌 **Hardware Agnostic** - Supports USB Serial and Raspberry Pi UART  
🎯 **Precise Control** - Full servo positioning and speed control  
📊 **Comprehensive Logging** - Built-in logging and debugging support  
🖥️ **CLI Interface** - Command-line tools for quick testing  
🐍 **Python 3.11+** - Modern Python with type hints

## Quick Example

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

## Supported Platforms

- **Linux** (Ubuntu, Debian, Raspberry Pi OS)
- **Windows** (Windows 10/11)
- **macOS** (Intel and Apple Silicon)

## Transport Options

- **USB Serial** - Most common, works on all platforms
- **Raspberry Pi UART** - Direct GPIO communication with optional direction control
- **Custom Transports** - Extensible architecture for additional communication methods

## Getting Started

Ready to start controlling servos? Check out our guides:

- [Installation](installation.md) - Get Muto Link installed on your system
- [Quick Start](getting-started.md) - Your first servo control program
- [Basic Usage](user-guide/basic-usage.md) - Learn the core concepts
- [API Reference](api-reference/driver.md) - Complete API documentation

## Community and Support

- 📚 [Documentation](https://billfaton.github.io/muto_link/)
- 🐛 [Issues](https://github.com/billfaton/muto_link/issues)
- 💡 [Discussions](https://github.com/billfaton/muto_link/discussions)
- 📖 [Contributing](development/contributing.md)

## License

MIT License - see the [LICENSE](https://github.com/billfaton/muto_link/blob/main/LICENSE) file for details.
