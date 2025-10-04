#!/usr/bin/env python3
"""
Example script demonstrating IMU data parsing functionality.

This example shows how to use the new IMU data parsing methods to get
structured, type-safe data from the Muto baseboard IMU sensors.
"""

from muto_link import Sensor, UsbSerial, IMUAngleData, RawIMUData

def main():
    """Demonstrate IMU data parsing with the Muto baseboard."""
    
    # Configuration - adjust the port for your system
    # Common ports: "/dev/ttyUSB0" (Linux), "/dev/cu.usbserial-*" (macOS), "COM*" (Windows)
    port = "/dev/cu.usbserial-1120"  # Update this for your device
    
    print("Muto IMU Data Parsing Example")
    print("=" * 40)
    
    try:
        # Create transport and sensor
        transport = UsbSerial(port=port, baud=115200)
        
        with Sensor(transport) as sensor:
            print(f"Connected to Muto baseboard on {port}")
            print()
            
            # Example 1: Get parsed fusion angle data
            print("1. IMU Fusion Angles (Parsed):")
            print("-" * 30)
            angle_data: IMUAngleData = sensor.get_imu_angle()
            
            print(f"Roll:        {angle_data.roll:5d}")
            print(f"Pitch:       {angle_data.pitch:5d}")  
            print(f"Yaw:         {angle_data.yaw:5d}")
            print(f"Temperature: {angle_data.temperature:3d}")
            print()
            
            # Example 2: Get raw bytes for comparison
            print("2. IMU Fusion Angles (Raw Bytes):")
            print("-" * 30)
            raw_bytes = sensor.read_IMU_angle()
            print(f"Raw data: {raw_bytes.hex()}")
            print(f"As bytes: {raw_bytes}")
            print()
            
            # Example 3: Get parsed 9-axis raw sensor data
            print("3. IMU 9-Axis Raw Data (Parsed):")
            print("-" * 30)
            raw_data: RawIMUData = sensor.get_raw_imu_data()
            
            print("Accelerometer:")
            print(f"  X: {raw_data.accel_x:5d}")
            print(f"  Y: {raw_data.accel_y:5d}")
            print(f"  Z: {raw_data.accel_z:5d}")
            
            print("Gyroscope:")
            print(f"  X: {raw_data.gyro_x:5d}")
            print(f"  Y: {raw_data.gyro_y:5d}")
            print(f"  Z: {raw_data.gyro_z:5d}")
            
            print("Magnetometer:")
            print(f"  X: {raw_data.mag_x:5d}")
            print(f"  Y: {raw_data.mag_y:5d}")
            print(f"  Z: {raw_data.mag_z:5d}")
            print()
            
            # Example 4: Show type safety and field access
            print("4. Type Safety Demonstration:")
            print("-" * 30)
            print(f"Angle data type: {type(angle_data)}")
            print(f"Raw data type:   {type(raw_data)}")
            print(f"Roll value:      {angle_data.roll} (type: {type(angle_data.roll)})")
            print(f"Accel X value:   {raw_data.accel_x} (type: {type(raw_data.accel_x)})")
            print()
            
            # Example 5: Using data in calculations
            print("5. Using Data in Calculations:")
            print("-" * 30)
            
            # Simple example: check if device is roughly level
            # Note: These are raw values, actual angle calculation would need calibration
            if abs(angle_data.roll - 32768) < 1000 and abs(angle_data.pitch - 32768) < 1000:
                print("Device appears to be roughly level")
            else:
                print("Device is tilted")
                
            # Check temperature range
            if angle_data.temperature > 30:
                print("Temperature is warm")
            elif angle_data.temperature < 10:
                print("Temperature is cool")
            else:
                print("Temperature is moderate")
            
            print()
            print("Example completed successfully!")
            
    except FileNotFoundError:
        print(f"Error: Could not find device at {port}")
        print("Please check the port name and ensure the device is connected.")
    except Exception as e:
        print(f"Error: {e}")
        print("Please check your device connection and try again.")

if __name__ == "__main__":
    main()
