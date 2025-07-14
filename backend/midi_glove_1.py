# 版本1:只键盘输入时才切换音符
# ---- mode切换 ----

MODE = "mode1"

# -----------------

import os
import sys
import csv
import mido
import pygame
import time
import serial

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')) 
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')) 

from datetime import datetime

from config import *
from MIDI_handler import MIDIHandler
from LED_controller import LEDController
from servo_controller import ServoController
from song_manager import SongManager
from ui_renderer import UIRenderer
from sound_player import SoundPlayer

# -- NEO -- 获取trigger box
# from device.trigger_box import TriggerNeuracle
# trigger = TriggerNeuracle(port='COM6')

TRIGGER_MAPPING = {
    48: 0x01, 50: 0x02, 52: 0x03, 53: 0x04, 55: 0x05,
    57: 0x06, 59: 0x07, 60: 0x08, 62: 0x09, 64: 0x0A,
    65: 0x0B, 67: 0x0C, 69: 0x0D, 71: 0x0E, 72: 0x0F,
    74: 0x10, 76: 0x11, 77: 0x12, 79: 0x13
}

pygame.mixer.init()

led_port = LED_PORT
servo_port = SERVO_PORT

led = LEDController(led_port)
servo = ServoController(servo_port)

MIDI_DEVICE_NAME = mido.get_input_names()[0]
song = SongManager("doremifa", NOTE_TO_INDEX_FILE, NOTE_SOUNDS_FILE)
ui = UIRenderer(song)
midi = MIDIHandler()
sound_player = SoundPlayer(song.note_sounds)

state = "playing_note"
state_start_time = time.time()
note_display_start_time = time.time()



led.clear_all()

current_time = time.time()

if state == "playing_note":
    led.set_led(song.note_to_index[song.expected_note]*2+14, -1)
    if(MODE == "mode1"):
        sound_player.play(song.expected_note)
    state = "waiting_servo"
    state_start_time = current_time

#状态2 控制舵机
elif state == "waiting_servo" and current_time - state_start_time >= 3.0:
    led.clear_all()
    servo.set_servo(song.expected_note)
    note_display_start_time = current_time
    state = "waiting_input"

    #状态3 等待键盘输入
elif state == "waiting_input":
    led.clear_all()
    if timing_active and current_time - timer_start >= song.expected_duration:
        state = "playing_note"
    elif not timing_active and current_time - note_display_start_time >= 3.0:
        state = "playing_note"




print(song.note_to_index[song.expected_note]*2+14)

running = True
timing_active = False
timer_start = 0
finish_alert_active = False
finish_alert_cancelable = False

note_start_times = {}
records = []

while running:
    new_input = False
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False
        elif evt.type == pygame.KEYDOWN:
            new_input = True

    for msg in midi.poll_all():
        new_input = True
        current_time = time.time()

        if msg.type == 'note_on' and msg.note in (36, 84):
            if msg.note == 36:
                song.prev_section()
            else:
                song.next_section()
            song.reset()
            state = "playing_note"
            continue

        elif msg.type == 'note_on' and msg.velocity > 0:
            note = msg.note
            velocity = msg.velocity
            note_start_times[note] = current_time
            timestamp = time.time()

            if note in song.note_sounds:
                sound_player.play(note)
                # if note in TRIGGER_MAPPING:
                #     trigger.send_trigger(TRIGGER_MAPPING[note])

            ui.display_pressed = note
            if not timing_active and note == song.expected_note:
                ui.display_result = True
                timing_active = True
                timer_start = timestamp
            else:
                ui.display_result = False

        elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
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

    # ----------- 状态切换控制（非阻塞） -------------
    current_time = time.time()

    # 状态1 等待键盘输入
    if state == "playing_note" and current_time - state_start_time >= 3.0:
        led.clear_all()
        song.advance_note()
        led.set_led(song.note_to_index[song.expected_note]*2+14, -1)
        if MODE == "mode1":
            sound_player.play(song.expected_note)
        state = "waiting_servo"
        state_start_time = current_time

        ui.display_pressed = None
        ui.display_result = None
        timing_active = False

        if song.current_index == 0:
            finish_alert_active = True
            ui.finish_alert_start = pygame.time.get_ticks()
            finish_alert_cancelable = False

    #状态2 控制舵机
    elif state == "waiting_servo" and current_time - state_start_time >= 5.0:
        led.clear_all()
        servo.set_servo(song.expected_note)
        note_display_start_time = current_time
        state = "waiting_input"

    #状态3 等待键盘输入
    elif state == "waiting_input" and current_time - state_start_time >= 3.0:
        led.clear_all()
        if timing_active and current_time - timer_start >= song.expected_duration + 4.0:
            state = "playing_note"
        elif not timing_active and current_time - note_display_start_time >= 5.0:
            state = "playing_note"

    if finish_alert_active:
        if pygame.time.get_ticks() - ui.finish_alert_start >= 500:
            finish_alert_cancelable = True
        if finish_alert_cancelable and new_input:
            finish_alert_active = False

    ui.render(finish_alert_active)
    pygame.time.Clock().tick(30)

# 记得不要用键盘interrupt，而是关闭窗口！！！
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
