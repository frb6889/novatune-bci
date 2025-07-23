# ---- 重要！！预设置 ---- 

play_indicate_note = True # True 为播放指示声音，False 为不播放指示声音
has_servo = False # 是否连接 Servo 进行测试
has_trigger_box = False # 是否连接trigger box进行测试

# -----------------
# python midi_glove_1.py

import os
import sys
import csv
import mido
import pygame
import time
import serial
import random

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
if has_trigger_box:
    from device.trigger_box import TriggerNeuracle
    trigger = TriggerNeuracle(port='COM5')

TRIGGER_MAPPING = {
    62: 0x01, 64:0x02, 65:0x03,67:0x04
}
LED_MAPPING = {
    62: 0x05, 64:0x06, 65:0x07,67:0x08
}

pygame.mixer.init()

led_port = LED_PORT
servo_port = SERVO_PORT

led = LEDController(led_port)
LED_RANDOM_TIME = 0.5

if has_servo:
    servo = ServoController(servo_port)

MIDI_DEVICE_NAME = mido.get_input_names()[0]
song = SongManager("remifaso", NOTE_TO_INDEX_FILE, NOTE_SOUNDS_FILE)
sound_player = SoundPlayer(song.note_sounds)

ui = UIRenderer(song)
midi = MIDIHandler()

state = "playing_note"
state_start_time = time.time()
note_display_start_time = time.time()

led.clear_all()
current_time = time.time()

last_green_update = 0.0

running = True
timing_active = False
timer_start = 0
finish_alert_active = False
finish_alert_cancelable = False

note_start_times = {}

records = []

# ----------- 运行主进程 -------------
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

    #状态1 灯和琴键声指示
    if state == "playing_note" and current_time - state_start_time >= 3.0:

        # 发送开始变黄的trigger
        if has_trigger_box:
            trigger.send_trigger(LED_MAPPING[note])
        led.to_yellow(song.note_to_index[song.expected_note]*2+14)
        
        if play_indicate_note:
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
    if state == "waiting_servo":
        
        # 舵机
        if current_time - state_start_time >= 3.0:

            # 发送开始变绿的trigger
            if has_trigger_box:
                trigger.send_trigger(TRIGGER_MAPPING[song.expected_note])
            led.to_green(song.note_to_index[song.expected_note]*2 + 14)
            if has_servo:
                servo.set_servo(song.expected_note)

            note_display_start_time = current_time
            state = "waiting_input"
            last_green_update = 0

    #状态3 等待键盘输入
    elif state == "waiting_input" and current_time - state_start_time >= 3.0:
        led.clear_all()
        if timing_active and current_time - timer_start >= song.expected_duration + 4.0:
            state = "playing_note"
        elif not timing_active and current_time - note_display_start_time >= 3.0: # 不接受键盘输入
            state = "playing_note"
            print(song.current_index," ",
            song.expected_note," ",
            len(song.song_sections[song.current_section]))

            song.advance_note()
            # 打乱顺序
            if song.current_index == 0:
                song.section_shuffle()
                print("----------")


    if finish_alert_active:
        if pygame.time.get_ticks() - ui.finish_alert_start >= 500:
            finish_alert_cancelable = True
        if finish_alert_cancelable and new_input:
            finish_alert_active = False

    ui.render(finish_alert_active)
    pygame.time.Clock().tick(30)


# ----------- 记录回放数据 -------------
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
