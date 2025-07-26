# trainer/training_loop.py

import time
import pygame

class TrainingLoop:
    def __init__(self, env):
        self.env = env
        self.running = True
        self.records = []  # For logging MIDI input
        self.note_start_times = {}
        pygame.mixer.init()

    def run(self):
        clock = pygame.time.Clock()

        while self.running:
            # ---- Handle Inputs ----
            self.running, new_input1 = self.env.input_handler.handle_pygame_events()
            new_input2 = self.env.input_handler.handle_midi_events()
            new_input = new_input1 or new_input2

            # ---- State Management ----
            current_time = time.time()
            self.env.state_manager.update(current_time)
            self.env.state_manager.handle_finish_alert(new_input)

            # ---- UI Rendering ----
            self.env.ui.render()
            clock.tick(30)

        return self.records  # Return records for saving after loop exits
