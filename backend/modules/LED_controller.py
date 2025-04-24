import serial

class LEDController:
    def __init__(self, port, num_leds = 60, baudrate = 9600, timeout = 0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.num_leds = num_leds

    def set_led(self, idx, brightness):
        cmd = f"{idx},{brightness}\n"
        self.ser.write(cmd.encode())

    def clear_all(self):
        for i in range(self.num_leds):
            self.set_led(i, 0)