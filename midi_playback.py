import mido
import pygame
import pygame.freetype
import sys
import json
import time
import csv
import os
from datetime import datetime
from song_loader import load_song

# #NEO:获取trigger box
# from device.trigger_box import TriggerNeuracle
# trigger = TriggerNeuracle(port='COM6')

# trigger 对应字典
# TRIGGER_MAPPING = {
#     48: 0x01, 50: 0x02, 52: 0x03, 53: 0x04, 55: 0x05,
#     57: 0x06, 59: 0x07, 60: 0x08, 62: 0x09, 64: 0x0A,
#     65: 0x0B, 67: 0x0C, 69: 0x0D, 71: 0x0E, 72: 0x0F,
#     74: 0x10, 76: 0x11, 77: 0x12, 79: 0x13,
# }

print("Available MIDI input ports:")
print(mido.get_input_names())

print("Available MIDI output ports:")
print(mido.get_output_names())

midi_input_name = mido.get_input_names()[0]

pygame.mixer.init()

with open("data/note_sounds.json", "r") as f:
    NOTE_SOUNDS = json.load(f)
NOTE_SOUNDS = {int(k): v for k, v in NOTE_SOUNDS.items()}

note_start_times = {}
records = []

print("Listening for MIDI messages...")

with mido.open_input(midi_input_name) as inport:
    try:
        for msg in inport:
            current_time = time.time()
            print(msg)

            if msg.type == 'note_on' and msg.velocity > 0:
                note = msg.note
                velocity = msg.velocity
                note_start_times[note] = current_time

                if note in NOTE_SOUNDS:
                    try:
                        pygame.mixer.Sound(NOTE_SOUNDS[note]).play()
                        # # NEO:每次琴键输入时，发送对应的 trigger
                        # if note in TRIGGER_MAPPING:
                        #     trig = TRIGGER_MAPPING[note]
                        #     trigger.send_trigger(trig)
                    except Exception as e:
                        print(f"播放声音错误: {e}")

            elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                note = msg.note
                if note in note_start_times:
                    start_time = note_start_times.pop(note)
                    duration = current_time - start_time
                    records.append({
                        'note': note,
                        'start_time': start_time,
                        'end_time': current_time,
                        'duration': duration,
                        'velocity': msg.velocity
                    })
    except KeyboardInterrupt:
        print("\n🔚 停止记录，准备写入日志文件...")

    # 创建日志目录
    log_dir = "./log"
    os.makedirs(log_dir, exist_ok=True)

    # 使用当前时间作为文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"midi_key_log_{timestamp}.csv"
    output_file = os.path.join(log_dir, log_filename)

    # 写入CSV文件
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['note', 'start_time', 'end_time', 'duration', 'velocity'])
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ MIDI 键盘日志已保存至：{output_file}")
