#### 前端
```bash
cd frontend
npm install
npm start
```


#### 后端
python版本：3.8.10

1.进入backend
```bash
cd backend
```
2.如不知道midi ports名称，终端运行
```bash
python midi_test.py
```
获取midi ports
输出形如：
```
Available MIDI input ports:
['MPK mini 3']
```
将输出的port名称替换进midi_server.py第17行即可
```python
7 # 配置
8 MIDI_DEVICE_NAME = "MPK mini 3"  # 改为midi设备名称
9 WEBSOCKET_PORT = 8765
```
3.进入arduino IDE运行backend/arduino_led/arduino_led.ino,获取串口名称后替换换进midi_server.py第12行即可
如"/dev/cu.usbmodem14401"：
```cpp
12 SERIAL_PORT = "/dev/cu.usbmodem14401"  # Windows: "COM3", macOS: "/dev/cu.usbmodemXXX"
13 BAUD_RATE = 9600
```

4.运行后端
```bash
python midi_server.py
```
