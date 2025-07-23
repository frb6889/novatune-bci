# LED_controller.py
import serial

class LEDController:
    def __init__(self, port, num_leds = 60, baudrate = 9600, timeout = 0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.num_leds = num_leds

    """ def set_led(self, idx, brightness1, brightness2, brightness3):
        cmd = f"{idx},{brightness1},{brightness2},{brightness3}\n"
        self.ser.write(cmd.encode()) """

    def set_led(self, idx, is_gradiant, old_r, old_g, old_b, new_r, new_g, new_b):
        # is_gradiant: 1 为渐变，0 为不渐变，-1 为默认从0到黄的渐变效果
        cmd = f"{idx},{is_gradiant},{old_r},{old_g},{old_b},{new_r},{new_g},{new_b}\n"
        self.ser.write(cmd.encode())
    
    def to_yellow(self, idx):
        self.set_led(idx, -1, 0, 0, 0, 100, 255, 0)

    def to_green(self, idx):
        self.set_led(idx, 1, 100, 255, 0, 0, 255, 0)
    
    def turn_off_one(self,idx):
        self.set_led(idx, 0, 0, 0, 0, 0, 0, 0)

    def clear_all(self):
        for i in range(self.num_leds):
            self.set_led(i,0,0,0,0,0,0,0)