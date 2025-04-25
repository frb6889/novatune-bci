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

midi = MIDIHandler()

sound_player = SoundPlayer(song.note_sounds)

running = True
timing_active = False
timer_start = 0
finish_alert_active = False
finish_alert_cancelable = False

while running:
    new_input = False
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False
        elif evt.type == pygame.KEYDOWN:
            new_input = True

    for msg in midi.poll_all():
        new_input = True
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

        elif msg.type == 'note_on':
            note = msg.note
            if note in song.note_sounds:
                try:
                    sound_player.play(note)
                    # -- NEO -- 发trigger
                    # if note in TRIGGER_MAPPING:
                    #     trig = TRIGGER_MAPPING[note]
                    #     trigger.send_trigger(trig)
                except:
                    pass

            ui.display_pressed = note
            if not timing_active and note == song.expected_note:
                ui.display_result = True
                timing_active = True
                timer_start = time.time()
            else:
                ui.display_result = False

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

midi.close()
pygame.quit()

