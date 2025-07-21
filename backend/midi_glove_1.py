# ---- mode切换 ---- 

MODE = "mode1" # mode1 为播放指示声音，mode2 为不播放指示声音

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
from sound_player_old import SoundPlayer

# -- NEO -- 获取trigger box
# from device.trigger_box import TriggerNeuracle
# trigger = TriggerNeuracle(port='COM6')

TRIGGER_MAPPING = {
    60: 0x01, 62:0x02, 64:0x03,65:0x04
}
LED_MAPPING = {
    60: 0x05, 62:0x06, 64:0x07,65:0x08
}

pygame.mixer.init()

led_port = LED_PORT
servo_port = SERVO_PORT

led = LEDController(led_port)
LED_RANDOM_TIME = 0.5



servo = ServoController(servo_port)

MIDI_DEVICE_NAME = mido.get_input_names()[0]
song = SongManager("remifaso", NOTE_TO_INDEX_FILE, NOTE_SOUNDS_FILE)
ui = UIRenderer(song)
midi = MIDIHandler()
sound_player = SoundPlayer(song.note_sounds)

state = "playing_note"
state_start_time = time.time()
note_display_start_time = time.time()

led.clear_all()
current_time = time.time()

last_green_update = 0.0

# ----------- 第一个键 -------------
#状态1 灯和琴键声指示
if state == "playing_note":
    led.set_led(song.note_to_index[song.expected_note]*2+14, -1,0,0,0,100,255,0)
    if(MODE == "mode1"):
        sound_player.play(song.expected_note)
    state = "waiting_servo"
    state_start_time = current_time




running = True
timing_active = False
timer_start = 0
finish_alert_active = False
finish_alert_cancelable = False

note_start_times = {}
records = []

section_end = 1
old_r = 100
old_g = 255
old_b = 0


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
        # led.clear_all()
        song.advance_note()
        section_end+=1
        # trigger.send_trigger(LED_MAPPING[note])
        led.set_led(song.note_to_index[song.expected_note]*2+14, -1,0,0,0,100,255,0)
        # TODO：解决一旦加上这行 后面的绿色渐变就会被阻塞闪动的问题
        """ old_r = 100
        old_g = 255
        old_b = 0 """
        
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
    """ elif state == "waiting_servo" and current_time - state_start_time >= 5.0:
        led.clear_all()
        servo.set_servo(song.expected_note)
        note_display_start_time = current_time
        state = "waiting_input"
        if current_time - last_green_update >= 0.1:
            brightness = random.randint(100, 255)
            led.set_led(song.note_to_index[song.expected_note]*2+14, 0, brightness, 0)
            last_green_update = current_time """


    if state == "waiting_servo":
        """ if current_time - last_green_update >= LED_RANDOM_TIME:
            brightness_g = random.randint(100, 255)
            led.set_led(song.note_to_index[song.expected_note]*2 + 14,1,old_r, old_g, old_b, 0,brightness_g,0)
            old_r = 0
            old_g = brightness_g
            old_b = 0
            last_green_update = current_time """
        
        # 舵机
        if current_time - state_start_time >= 3.0:
            #trigger.send_trigger(TRIGGER_MAPPING[song.expected_note])
            led.set_led(song.note_to_index[song.expected_note]*2 + 14,1,100, 255, 0, 0,255,0)
            # led.clear_all()
            servo.set_servo(song.expected_note)
            note_display_start_time = current_time
            state = "waiting_input"
            last_green_update = 0

    #状态3 等待键盘输入
    elif state == "waiting_input" and current_time - state_start_time >= 3.0:
        led.clear_all()
        if(section_end%4==0):
            song.reset()
        
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
