import mido
import asyncio
import websockets
import json

MIDI_DEVICE_NAME = "MPK mini 3"
WEBSOCKET_PORT = 8765

# python midi_server.py

# 《玛丽有只小羊羔》音符序列（MIDI 编号）
song_notes = [64, 62, 60, 62, 64, 64, 64, 62, 62, 62, 64, 67, 67]
current_index = 0  # 追踪当前目标音符

async def midi_to_websocket(websocket, path):
    global current_index
    input_names = mido.get_input_names()
    target_device = next((name for name in input_names if MIDI_DEVICE_NAME in name), None)

    if not target_device:
        print(f"未找到设备: {MIDI_DEVICE_NAME}")
        return

    with mido.open_input(target_device) as inport:
        print(f"监听 MIDI 设备: {target_device}")
        while True:
            msg = inport.receive()
            if msg.type == 'note_on':
                expected_note = song_notes[current_index]
                print(msg.note)
                result = True if msg.note == expected_note else False

                if msg.note == expected_note:
                    current_index = (current_index + 1) % len(song_notes)  # 进入下一个音符

                data = {
                    "type": msg.type,
                    "note": msg.note,
                    "expected": song_notes[current_index],  # 发送下一个该弹的音符
                    "result": result
                }
                print(result)
                await websocket.send(json.dumps(data))

start_server = websockets.serve(midi_to_websocket, "localhost", WEBSOCKET_PORT)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
