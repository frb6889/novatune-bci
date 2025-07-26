import logging

import serial
from serial.tools.list_ports import comports


logger = logging.getLogger(__name__)


def get_serial_ports():
    """获取可选端口"""
    ports = list(comports(include_links=False))
    available_ports_list = [port.device for port in ports]
    return available_ports_list


class FingerController:
    def __init__(self, mode='step', init_params=dict()):
        self.hand = FuboPneumaticFingerClient(init_params)
        self.current_state = 'rest'
        if mode not in ['edge', 'step']:
            raise ValueError('mode must be in \{"edge", "step"\}')
        self.mode = mode

    def move(self, action='flex'):
        if self.mode == 'edge':
            self._edge(action)
        elif self.mode == 'step':
            self._step(action)
    
    def _step(self, action='flex'):
        if action == 'rest':
            self.hand.start('extend')
        else:
            self.hand.start(action)
        self.current_state = action

    def _edge(self, action='flex'):
        if action == 'rest':
            return 
        if self.current_state == 'extend':
            self.hand.start(action)
            self.current_state = action
        elif self.current_state == action:
            self.hand.start('extend')
            self.current_state = 'extend'
        else:  # rest or any other
            self.hand.start(action)
            self.current_state = action


class FuboPneumaticFingerClient:
    """富伯客户端"""
    
    COMMAND_TABLE = {
        'rest': b"R",
        'cylinder': b"C",
        'ball': b"B",
        'flex': b"F",
        'double': b"D",
        'treble': b"T",
        'extend': b"E",
    }
    def __init__(self, init_params=None):
        self.baud_rate = 9600
        self.data_bite = 8
        self.timeout = 1
        self.stop_bit = serial.STOPBITS_ONE  # 停止位
        self.parity_bit = serial.PARITY_NONE  # 校验位
        self.is_connected = False
        self.ser = None  # 连接对象
        self.port = "COM 4"
        if init_params:
            self.port = init_params["port"]
        
        self.connect()

    def __del__(self):
        self.ser.close()

    def connect(self):
        try:
            self.ser = serial.Serial(port=self.port,
                                     baudrate=self.baud_rate,
                                     parity=self.parity_bit,
                                     stopbits=self.stop_bit,
                                     timeout=self.timeout)
            if self.ser.is_open:
                self.is_connected = True
                logger.info("connect")
                return 1
            else:
                self.is_connected = False
                logger.warning("open failed")
                return 0
        except OSError as e:
            warning_info = f"pneumatic finger connect failed: {e}"
            logger.warning(warning_info)
            return 0
    
    def start(self, command):
        self.ser.write(self.COMMAND_TABLE[command])

    def status(self):
        status = {"is_connected": self.is_connected}
        return status

    def close(self):
        if self.ser:
            self.ser.close()
            self.is_connected = False
        return {"is_connected": self.is_connected}
class FuboSingleFinger:
    """富伯客户端"""
    
    COMMAND_TABLE = {
        'flex':b"DATA:0:80:0:80:0:80:0:80:0:80\r",
        'ring_and_little':b"DATA:0:0:0:0:0:0:0:80:0:80\r",
        'thumb':b"DATA:0:0:0:80:0:80:0:80:0:80\r",
        'middle':b"DATA:0:80:0:80:0:0:0:80:0:80\r",
        'ring':b"DATA:0:80:0:80:0:80:0:0:0:80\r",
        'little':b"DATA:0:80:0:80:0:80:0:80:0:0\r",
        'extend':b"DATA:0:0:0:0:0:0:0:0:0:0\r",
        'index': b"DATA:0:80:0:0:0:80:0:80:0:80\r",
        'six':b"DATA:0:0:0:80:0:80:0:80:0:0\r",
        'pinch':b"DATA:0:80:0:80:0:0:0:0:0:0\r",
        'tripod':b"DATA:0:80:0:80:0:80:0:0:0:0\r",
        'rest':b"DATA:0:0:0:0:0:0:0:0:0:0\r",
        'thumbflex':b"DATA:0:80:0:0:0:0:0:0:0:0\r",
        'indexflex':b"DATA:0:0:0:80:0:0:0:0:0:0\r",
        'middleflex':b"DATA:0:0:0:0:0:80:0:0:0:0\r",
        'ringflex':b"DATA:0:0:0:0:0:0:0:80:0:0\r",
        'littleflex':b"DATA:0:0:0:0:0:0:0:0:0:80\r",

        
    }
    def __init__(self, init_params=None):
        self.baud_rate = 57600
        self.data_bite = 8
        self.timeout = 1
        self.stop_bit = serial.STOPBITS_ONE  # 停止位
        self.parity_bit = serial.PARITY_NONE  # 校验位
        self.is_connected = False
        self.ser = None  # 连接对象
        self.port = "COM4"
        if init_params:
            self.port = init_params["port"]
        
        self.connect()

    def __del__(self):
        self.ser.close()

    def connect(self):
        try:
            self.ser = serial.Serial(port=self.port,
                                     baudrate=self.baud_rate,
                                     parity=self.parity_bit,
                                     stopbits=self.stop_bit,
                                     timeout=self.timeout)
            if self.ser.is_open:
                self.is_connected = True
                searching = self.ser.readline().decode('ASCII').strip()
                if searching == "device":
                    print("adding:\n", searching)
                    reply_msg = "RMTC_GLOVE\r"
                    self.ser.write(reply_msg.encode('ASCII'))
                    print("reply:\n", reply_msg)
                    response = self.ser.readline().decode('ASCII').strip()
                    print("response:\n",response)
                return 1
            else:
                self.is_connected = False
                logger.warning("open failed")
                return 0
        except OSError as e:
            warning_info = f"pneumatic finger connect failed: {e}"
            logger.warning(warning_info)
            return 0
    def start(self, command):
        self.ser.write(self.COMMAND_TABLE[command])

    def status(self):
        status = {"is_connected": self.is_connected}
        return status

    def close(self):
        if self.ser:
            self.ser.close()
            self.is_connected = False
        return {"is_connected": self.is_connected}