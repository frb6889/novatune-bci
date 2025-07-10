import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')) 
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')) 

from config import *
from MIDI_handler import MIDIHandler
from LED_controller import LEDController
from song_manager import SongManager
from ui_renderer import UIRenderer
from sound_player import SoundPlayer

import os
import csv
from datetime import datetime
import mido
import pygame
import time
import serial

# -- NEO -- 获取trigger box
# from device.trigger_box import TriggerNeuracle
# trigger = TriggerNeuracle(port='COM6')

TRIGGER_MAPPING = {
    48: 0x01, 50: 0x02, 52: 0x03, 53: 0x04, 55: 0x05,
    57: 0x06, 59: 0x07, 60: 0x08, 62: 0x09, 64: 0x0A,
    65: 0x0B, 67: 0x0C, 69: 0x0D, 71: 0x0E, 72: 0x0F,
    74: 0x10, 76: 0x11, 77: 0x12, 79: 0x13
}

serial_port = SERIAL_PORT
led = LEDController(serial_port)
MIDI_DEVICE_NAME = mido.get_input_names()[0]
pygame.mixer.init()

song = SongManager(CURRENT_SONG, NOTE_TO_INDEX_FILE, NOTE_SOUNDS_FILE)
ui = UIRenderer(song)

led.clear_all()
led.set_led(song.note_to_index[song.expected_note]*2+14, 255)
print(song.note_to_index[song.expected_note]*2+14)

midi = MIDIHandler()

sound_player = SoundPlayer(song.note_sounds)

running = True
timing_active = False
timer_start = 0
finish_alert_active = False
finish_alert_cancelable = False


# record记录
note_start_times = {}
records = []

while running:
    new_input = False
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False
        elif evt.type == pygame.KEYDOWN:
            new_input = True

    notes_this_frame = []
    for msg in midi.poll_all():

        new_input = True
        current_time = time.time()

        if msg.type == 'note_on' and msg.note in (36, 84):
            if msg.note == 36:
                song.prev_section()
            else:
                song.next_section()
            song.reset()
            led.clear_all()
            led.set_led(song.note_to_index[song.expected_note]*2+14, 255)
            finish_alert_active = False
            finish_alert_cancelable = False

        elif msg.type == 'note_on' and msg.velocity > 0:
            note = msg.note
            velocity = msg.velocity
            note_start_times[note] = current_time
            timestamp = time.time()

            if note in song.note_sounds:
                notes_this_frame.append((note, timestamp))  # 收集
                # # NEO:每次琴键输入时，发送对应的 trigger
                # if note in TRIGGER_MAPPING:
                #     trig = TRIGGER_MAPPING[note]
                #     trigger.send_trigger(trig)

        

            ui.display_pressed = note
            if not timing_active and note == song.expected_note:
                ui.display_result = True
                timing_active = True
                timer_start = timestamp
            else:
                ui.display_result = False

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

    # === 音符聚类播放 ===
    notes_this_frame.sort(key=lambda x: x[1])
    grouped = []
    last_time = None

    for note, ts in notes_this_frame:
        if last_time is None or ts - last_time <= NOTE_THRESHOLD:
            grouped.append((note, ts))
        else:
            sound_player.play_chord([n for n, _ in grouped])
            grouped = [(note, ts)]
        last_time = ts

    if grouped:
        sound_player.play_chord([n for n, _ in grouped])

    if timing_active and time.time() - timer_start >= song.expected_duration:
        led.clear_all()
        song.advance_note()
        led.set_led(song.note_to_index[song.expected_note]*2+14, 255)
        timing_active = False
        ui.display_pressed = None
        ui.display_result = None
        if song.current_index == 0:
            finish_alert_active = True
            ui.finish_alert_start = pygame.time.get_ticks()
            finish_alert_cancelable = False

    if finish_alert_active:
        if pygame.time.get_ticks() - ui.finish_alert_start >= 500:
            finish_alert_cancelable = True
        if finish_alert_cancelable and new_input:
            finish_alert_active = False

    ui.render(finish_alert_active)

    pygame.time.Clock().tick(30)



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
midi.close()
pygame.quit()

