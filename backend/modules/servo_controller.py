import serial

class ServoController:
    def __init__(self, port, baudrate = 9700, timeout = 0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def set_servo(self, idx):
        cmd = f"{idx}\n"
        self.ser.write(cmd.encode())
