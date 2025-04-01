
#NEO:获取trigger box
""" from device.trigger_box import TriggerNeuracle """
import mido
import asyncio
import websockets
import json
import pygame

# 初始化声音模块
pygame.mixer.init()

# NEO:trigger box端口号
""" trigger = TriggerNeuracle(port='COM6')   """

MIDI_DEVICE_NAME = "Vboard 49"
WEBSOCKET_PORT = 8765

# 琴键对应
NOTE_SOUNDS = {
    # C3 (48) 到 G3 (55)
    48: "sound/C3.wav",
    50: "sound/D3.wav",
    52: "sound/E3.wav",
    53: "sound/F3.wav",
    55: "sound/G3.wav",
    57: "sound/A4.wav",
    59: "sound/B4.wav",
    
    # C4 (60) 到 G4 (67)
    60: "sound/C4.wav",
    62: "sound/D4.wav",
    64: "sound/E4.wav",
    65: "sound/F4.wav",
    67: "sound/G4.wav",
    69: "sound/A5.wav",
    71: "sound/B5.wav",

    # C5 (72) 到 G5 (79)
    72: "sound/C5.wav",
    74: "sound/D5.wav",
    76: "sound/E5.wav",
    77: "sound/F5.wav",
    79: "sound/G5.wav"
}

# 字典
TRIGGER_MAPPING = {
    48: 0x01,
    50: 0x02,
    52: 0x03,
    53: 0x04,
    55: 0x05,
    57: 0x06,
    59: 0x07,
    60: 0x08,
    62: 0x09,
    64: 0x0A,
    65: 0x0B,
    67: 0x0C,
    69: 0x0D,
    71: 0x0E,
    72: 0x0F,
    74: 0x10,
    76: 0x11,
    77: 0x12,
    79: 0x13,
}

# 《东方红》旋律
song_sections = [
    [67, 67, 69, 62, 60, 60, 57, 62],  # 5 5 6 2 - 1 1 _6 2 - 东方红，太阳升，
    [67, 67, 69, 72, 69, 67, 60, 60, 57, 62],  # 5 5 6 ·1 6 5 1 1 _6 2 - 
    [67, 62, 60, 59, 57, 55, 67, 62],  # 5 2 1 _7 _6 _5 5 2  
    [64, 62, 60, 60, 57, 62, 64, 62, 60, 59, 57, 55],    # 3 2 1 1 _6 2 3 2 1 2 1 _7 _6 _5 呼儿嗨呀，他是人民大救星
    [67, 62, 60, 59, 57, 55, 67, 62],   # 5 2 1 _7 _6 _5 5 2,
    [64, 62, 60, 60, 57, 62, 64, 62, 60, 74, 72, 71, 69, 67, 67]   # 3 2 1 1 _6 2 3 2 1 ·2 ·1 7 6 5 - 5 0
]

current_section = 0   # 当前段落索引
current_index = 0     # 当前段落中目标音符的索引
song_notes = song_sections[current_section]  # 当前段落音符

async def midi_to_websocket(websocket, path):
    global current_section, current_index, song_notes

    input_names = mido.get_input_names()
    target_device = next((name for name in input_names if MIDI_DEVICE_NAME in name), None)

    if not target_device:
        print(f"未找到设备: {MIDI_DEVICE_NAME}")
        return

    with mido.open_input(target_device) as inport:
        print(f"监听 MIDI 设备: {target_device}")
        while True:
            msg = inport.receive()

            # 检查是否为特殊控制指令（note 36 = 上一段, note 84 = 下一段）
            if msg.type == 'note_on' and msg.note in (36, 84):
                if msg.note == 36:
                    current_section = (current_section - 1) % len(song_sections)
                    print(f"切换到上一段: 第 {current_section + 1} 段")
                elif msg.note == 84:
                    current_section = (current_section + 1) % len(song_sections)
                    print(f"切换到下一段: 第 {current_section + 1} 段")
                
                song_notes = song_sections[current_section]
                current_index = 0

                update_data = {
                    "type": "section_update",
                    "section": current_section + 1,  # 前端显示从 1 开始
                    "expected": song_notes[current_index]
                }
                try:
                    await websocket.send(json.dumps(update_data))
                except websockets.exceptions.ConnectionClosedError as e:
                    print("WebSocket 连接已关闭:", e)
                    break
                continue

            # 处理 MIDI 音符
            if msg.type == 'note_on':
                expected_note = song_notes[current_index]
                note = msg.note

                # 播放键盘声音
                if note in NOTE_SOUNDS:
                    pygame.mixer.Sound(NOTE_SOUNDS[note]).play()

                # NEO:每次琴键输入时，发送对应的 trigger
                """ if note in TRIGGER_MAPPING:
                    trigger_value = TRIGGER_MAPPING[note]
                    trigger.send_trigger(trigger_value)
                    print(f"发送 trigger: {hex(trigger_value)} 对应音符: {note}") """

                result = (note == expected_note)
                if result:
                    current_index = (current_index + 1) % len(song_notes)

                data = {
                    "type": msg.type,
                    "note": note,
                    "expected": song_notes[current_index],
                    "result": result,
                    "section": current_section + 1
                }
                try:
                    await websocket.send(json.dumps(data))
                except websockets.exceptions.ConnectionClosedError as e:
                    print("WebSocket 连接已关闭:", e)
                    break

            elif msg.type == 'note_off':
                data = {
                    "type": msg.type,
                    "note": msg.note,
                    "expected": song_notes[current_index],
                    "result": None,
                    "section": current_section + 1
                }
                try:
                    await websocket.send(json.dumps(data))
                except websockets.exceptions.ConnectionClosedError as e:
                    print("WebSocket 连接已关闭:", e)
                    break

async def main():
    server = await websockets.serve(midi_to_websocket, "localhost", WEBSOCKET_PORT)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
