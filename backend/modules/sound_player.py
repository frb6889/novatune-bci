# sound_player.py (FluidSynth版)

import fluidsynth
import os

class SoundPlayer:
    def __init__(self, note_sounds=None, max_channels=16):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        sf2_path = os.path.join(base_dir, 'assets', 'FluidR3_GM.sf2')

        self.fs = fluidsynth.Synth()
        self.fs.start(driver="coreaudio")

        self.sfid = self.fs.sfload(sf2_path)
        self.fs.program_select(0, self.sfid, 0, 0)

    def play(self, note):
        self.fs.noteon(0, note, 127)

    def play_chord(self, notes):
        for note in notes:
            self.fs.noteon(0, note, 127)

    def stop(self, note):
        self.fs.noteoff(0, note)

    def stop_all(self):
        self.fs.system_reset()

    def __del__(self):
        self.fs.delete()