import serial
import time

def connect_to_arduino(serial_port, baud_rate):
    try:
        ser = serial.Serial(serial_port, baud_rate)
        print(f"Connected to Arduino on {serial_port} at {baud_rate} baud.")
        time.sleep(2)  # Wait for the serial connection to establish
        return ser
    except serial.SerialException as e:
        print(f"Failed to connect to Arduino: {e}")
        return None

def send_toggle_command(ser):
    ser.write(b't')


