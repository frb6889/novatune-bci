
import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

import serial
from config import *
from modules.LED_controller import LEDController

serial_port = SERIAL_PORT

def test_serial_connection(port):
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            if ser.is_open:
                print(f"✅ 串口 {port} 连接成功")
                return True
            else:
                print(f"❌ 串口 {port} 无法打开")
                return False
    except serial.SerialException as e:
        print(f"❌ 串口 {port} 连接失败: {e}")
        return False

if not test_serial_connection(SERIAL_PORT):
    sys.exit(1) 

led = LEDController(serial_port)


led.clear_all()
for i in range(0,60):
    led.set_led(i, 255)

    


