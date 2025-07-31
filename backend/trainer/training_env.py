# training_env.py

from config import *
from state_manager import StateManager
from MIDI_handler import MIDIHandler
from LED_controller import LEDController
from servo_controller import ServoController
from song_manager import SongManager
from ui_renderer import UIRenderer
from sound_player_old import SoundPlayer
from input_handler import InputHandler
from logger import save_midi_log
from device.trigger_box import TriggerNeuracle

class TrainingEnv:
    def __init__(self, training_config):
        self.led = LEDController(LED_PORT)
        self.servo = ServoController(SERVO_PORT) if training_config.has_servo else None
        self.trigger = TriggerNeuracle(port = TRIGGER_PORT) if training_config.has_trigger_box else None
        self.song = SongManager(CURRENT_SONG, NOTE_TO_INDEX_FILE, NOTE_SOUNDS_FILE)
        self.sound_player = SoundPlayer(self.song.note_sounds)
        self.ui = UIRenderer(self.song)
        self.midi = MIDIHandler()
        self.state_manager = StateManager(
            self.song, self.servo, self.led, self.ui,
            self.sound_player, self.trigger, training_config.play_indicate_note
        )
        self.input_handler = InputHandler(
            self.midi, self.ui, self.song, self.sound_player, self.state_manager
        )
