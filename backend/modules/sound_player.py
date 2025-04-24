import pygame
import os

class SoundPlayer:
    def __init__(self, note_sounds, max_channels=16):
        pygame.mixer.set_num_channels(max_channels)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        self.channels = [pygame.mixer.Channel(i) for i in range(max_channels)]
        self.sounds = {
            note: pygame.mixer.Sound(os.path.join(base_dir, path)) for note, path in note_sounds.items()
        }

    def play(self, note):
        sound = self.sounds.get(note)
        if not sound:
            return
        for ch in self.channels:
            if not ch.get_busy():
                ch.play(sound)
                return
        print(f"No available channel for note {note} ㅠㅠ")
