import time
import pygame

class InputHandler:
    def __init__(self, midi, ui, song, sound_player, state_manager):
        self.midi = midi
        self.ui = ui
        self.song = song
        self.sound_player = sound_player
        self.state_manager = state_manager
        self.note_start_times = {}
        self.records = []

    def handle_pygame_events(self):
        running = True
        new_input = False

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
            elif evt.type == pygame.KEYDOWN:
                new_input = True

        return running, new_input

    def handle_midi_events(self):
        new_input = False
        current_time = time.time()

        for msg in self.midi.poll_all():
            new_input = True
            timestamp = current_time

            if msg.type == 'note_on' and msg.note in (36, 84):
                if msg.note == 36:
                    self.song.prev_section()
                else:
                    self.song.next_section()
                self.song.reset()
                self.state_manager.set_state("playing_note")
                continue

            elif msg.type == 'note_on' and msg.velocity > 0:
                note = msg.note
                self.note_start_times[note] = timestamp

                if note in self.song.note_sounds:
                    self.sound_player.play(note)

                self.ui.display_pressed = note

                if not self.state_manager.timing_active and note == self.song.expected_note:
                    self.state_manager.notify_correct_input()
                else:
                    self.ui.display_result = False

            elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
                note = msg.note
                if note in self.note_start_times:
                    start_time = self.note_start_times.pop(note)
                    duration = timestamp - start_time
                    self.records.append({
                        'note': note,
                        'start_time': start_time,
                        'end_time': timestamp,
                        'duration': duration,
                        'velocity': msg.velocity
                    })

        return new_input

    def get_records(self):
        return self.records
