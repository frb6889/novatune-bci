
import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

import mido
import pygame
import json
from modules.sound_player import SoundPlayer


print("Available MIDI input ports:")
print(mido.get_input_names())

print("Available MIDI output ports:")
print(mido.get_output_names())

midi_input_name = mido.get_input_names()[0]

pygame.mixer.init()

with open("../data/note_sounds.json", "r") as f:
    NOTE_SOUNDS = json.load(f)
NOTE_SOUNDS = {int(k): v for k, v in NOTE_SOUNDS.items()}

sound_player = SoundPlayer(NOTE_SOUNDS)

with mido.open_input(midi_input_name) as inport:
    print("Listening for MIDI messages...")
    for msg in inport:

        print(msg)

        note = msg.note
        if msg.type == 'note_on' and note in NOTE_SOUNDS:
                try:
                    sound_player.play(note)
                except Exception as e:
                    print(f"播放声音错误: {e}")
                    
        """  
        消息示例：
        中央C：
        note_on channel=0 note=60 velocity=18 time=0
        note_off channel=0 note=60 velocity=0 time=0
        D：
        note_on channel=0 note=62 velocity=8 time=0
        note_off channel=0 note=62 velocity=0 time=0
        E：
        note_on channel=0 note=64 velocity=8 time=0
        note_off channel=0 note=64 velocity=0 time=0
        """