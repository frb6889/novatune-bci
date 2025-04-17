import mido
import pygame
import pygame.freetype
import sys
import json
from song_loader import load_song

# 准备：获取midi ports名称
print("Available MIDI input ports:")
print(mido.get_input_names())

print("Available MIDI output ports:")
print(mido.get_output_names())

# 
midi_input_name = 'MPK mini 3' # 替换成实际设备名称

pygame.mixer.init()

with open("data/note_sounds.json", "r") as f:
    NOTE_SOUNDS = json.load(f)
NOTE_SOUNDS = {int(k): v for k, v in NOTE_SOUNDS.items()}

with mido.open_input(midi_input_name) as inport:
    print("Listening for MIDI messages...")
    for msg in inport:
        print(msg)  # 打印接收到的 MIDI 消息
        note = msg.note
        if msg.type == 'note_on' and note in NOTE_SOUNDS:
                try:
                    pygame.mixer.Sound(NOTE_SOUNDS[note]).play()
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