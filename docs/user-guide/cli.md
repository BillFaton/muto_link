# Command Line Interface

Muto Link includes a comprehensive CLI for quick testing, scripting, and automation. The `muto` command provides access to all servo control functions without writing Python code.

## Basic Commands

### Getting Help

```bash
# General help
muto --help

# Command-specific help
muto servo --help
muto torque --help
```

### Connection Options

All commands support these global options:

```bash
muto [OPTIONS] COMMAND [ARGS]

Options:
  --port TEXT     Serial port (default: /dev/ttyUSB0)
  --backend TEXT  Transport backend: 'usb' or 'pi' (default: usb)
  --log-level     Log level: DEBUG, INFO, WARN, ERROR
  --help          Show help message
```

## Servo Control Commands

### Enable/Disable Servo Control

```bash
# Enable servo control (required before movement)
muto torque --on

# Disable servo control (allows manual positioning)
muto torque --off

# Using different port
muto --port COM3 torque --on
```

### Move Servos

```bash
# Basic servo movement
muto servo --id 1 --angle 90 --speed 1000

# Multiple parameters
muto servo --id 5 --angle 45 --speed 2000

# Using short options
muto servo -i 2 -a 135 -s 800

# Different port and backend
muto --port /dev/serial0 --backend pi servo --id 1 --angle 90 --speed 1500
```

#### Parameter Ranges

- `--id`: Servo ID (1-255)
- `--angle`: Target angle (0-180 degrees)
- `--speed`: Movement speed (0-65535, higher = faster)

### Read Servo Positions

```bash
# Read single servo position
muto read-angle --id 1

# Read multiple servos
muto read-angle --id 1
muto read-angle --id 2
muto read-angle --id 3
```

### Servo Calibration

```bash
# Calibrate servo offset
muto calibrate --id 1 --deviation 100

# Negative deviation (counterclockwise)
muto calibrate --id 2 --deviation -50

# Large adjustment
muto calibrate --id 3 --deviation 500
```

## Backend Selection

### USB Serial (Default)

```bash
# Explicit USB backend
muto --backend usb servo --id 1 --angle 90 --speed 1000

# Common USB ports
muto --port /dev/ttyUSB0 servo --id 1 --angle 90 --speed 1000  # Linux
muto --port COM3 servo --id 1 --angle 90 --speed 1000         # Windows
muto --port /dev/tty.usbserial-* servo --id 1 --angle 90 --speed 1000  # macOS
```

### Raspberry Pi UART

```bash
# Pi UART backend
muto --backend pi servo --id 1 --angle 90 --speed 1000

# Pi with custom port
muto --port /dev/serial0 --backend pi servo --id 1 --angle 90 --speed 1000

# Pi UART is typically /dev/serial0 or /dev/ttyAMA0
```

## Logging and Debugging

### Enable Debug Logging

```bash
# Maximum verbosity for troubleshooting
muto --log-level DEBUG servo --id 1 --angle 90 --speed 1000

# Info level for general operation tracking
muto --log-level INFO servo --id 1 --angle 90 --speed 1000

# Errors only
muto --log-level ERROR servo --id 1 --angle 90 --speed 1000
```

### Environment Variable

Set default log level:

```bash
export MUTO_LOG_LEVEL=DEBUG
muto servo --id 1 --angle 90 --speed 1000
```

## Scripting Examples

### Bash Scripts

```bash
#!/bin/bash
# servo_sequence.sh

PORT="/dev/ttyUSB0"
SPEED=1000

echo "Starting servo sequence..."

# Enable servo control
muto --port $PORT torque --on

# Move servos in sequence
for servo in 1 2 3 4 5; do
    echo "Moving servo $servo..."
    muto --port $PORT servo --id $servo --angle 90 --speed $SPEED
    sleep 1
done

# Sweep all servos
echo "Sweeping servos..."
for angle in 0 45 90 135 180; do
    echo "All servos to $angle degrees"
    for servo in 1 2 3 4 5; do
        muto --port $PORT servo --id $servo --angle $angle --speed 1500 &
    done
    wait
    sleep 2
done

echo "Sequence complete!"
```

### Python Subprocess

```python
import subprocess
import time

def muto_command(args):
    """Execute muto CLI command."""
    cmd = ["muto", "--port", "/dev/ttyUSB0"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout

# Enable servo control
muto_command(["torque", "--on"])

# Move servos
servos_and_angles = [(1, 45), (2, 90), (3, 135)]
for servo_id, angle in servos_and_angles:
    muto_command(["servo", "--id", str(servo_id), "--angle", str(angle), "--speed", "1000"])
    time.sleep(0.5)
```

### PowerShell (Windows)

```powershell
# servo_test.ps1

$port = "COM3"
$speed = 1000

Write-Host "Starting servo test..."

# Enable servo control
& muto --port $port torque --on

# Test servo movement
$servos = 1..5
foreach ($servo in $servos) {
    Write-Host "Testing servo $servo"
    & muto --port $port servo --id $servo --angle 90 --speed $speed
    Start-Sleep -Seconds 1
}

Write-Host "Test complete!"
```

## Automation and Integration

### Systemd Service (Linux)

Create a service file `/etc/systemd/system/muto-servo.service`:

```ini
[Unit]
Description=Muto Servo Control Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/muto --port /dev/ttyUSB0 torque --on
ExecStop=/usr/local/bin/muto --port /dev/ttyUSB0 torque --off
RemainAfterExit=yes
User=pi
Group=dialout

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable muto-servo.service
sudo systemctl start muto-servo.service
```

### Cron Jobs

```bash
# crontab -e

# Enable servo control at startup
@reboot /usr/local/bin/muto --port /dev/ttyUSB0 torque --on

# Reset all servos to center position every hour
0 * * * * /usr/local/bin/muto --port /dev/ttyUSB0 servo --id 1 --angle 90 --speed 1000

# Disable servos at midnight for safety
0 0 * * * /usr/local/bin/muto --port /dev/ttyUSB0 torque --off
```

### Docker Integration

```dockerfile
FROM python:3.11-slim

RUN pip install muto-link

# Add your script
COPY servo_control.sh /app/
RUN chmod +x /app/servo_control.sh

ENTRYPOINT ["/app/servo_control.sh"]
```

Run with device access:

```bash
docker run --device=/dev/ttyUSB0 your-muto-image
```

## Troubleshooting CLI Issues

### Command Not Found

```bash
# Check installation
which muto
pip list | grep muto

# Reinstall if needed
pip install --force-reinstall muto-link
```

### Permission Issues

```bash
# Check port permissions
ls -la /dev/ttyUSB0

# Add user to dialout group (Linux)
sudo usermod -a -G dialout $USER
# Log out and back in
```

### Communication Errors

```bash
# Test with debug logging
muto --log-level DEBUG --port /dev/ttyUSB0 torque --on

# Check available ports
ls /dev/tty*  # Linux/macOS
# Use Device Manager on Windows
```

### No Servo Response

1. **Verify power**: Ensure baseboard has adequate power
2. **Check connections**: Verify servo connections to baseboard
3. **Enable torque**: Always run `torque --on` before servo commands
4. **Test servo ID**: Verify you're using the correct servo ID

## Advanced Usage

### Batch Operations

```bash
# Create a servo position file
cat > positions.txt << EOF
1 45 1000
2 90 1200  
3 135 800
4 60 1500
5 120 1000
EOF

# Execute batch movements
while read servo angle speed; do
    muto servo --id $servo --angle $angle --speed $speed
done < positions.txt
```

### JSON Output (Future Enhancement)

```bash
# This could be added in future versions
muto read-angle --id 1 --format json
# {"servo_id": 1, "angle": 90, "raw_response": "..."}
```

### Configuration Files (Future Enhancement)

```bash
# Future: Support for config files
muto --config servo_config.yaml servo --id 1 --angle 90
```

## Exit Codes

The CLI returns standard exit codes:

- `0`: Success
- `1`: General error (connection, communication, etc.)
- `2`: Invalid arguments
- `130`: Interrupted by user (Ctrl+C)

Use in scripts:

```bash
if muto --port /dev/ttyUSB0 torque --on; then
    echo "Servo control enabled successfully"
    muto --port /dev/ttyUSB0 servo --id 1 --angle 90 --speed 1000
else
    echo "Failed to enable servo control"
    exit 1
fi
```

## Next Steps

- [Basic Usage](basic-usage.md) - Learn the Python API
- [Advanced Usage](advanced-usage.md) - Complex servo control scenarios
- [API Reference](../api-reference/driver.md) - Complete API documentation
- [Examples](../examples/basic-servo-control.md) - Real-world examples
