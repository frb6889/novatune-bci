import os
import sys
import csv
import mido
import pygame
import time
import serial
import random

class StateManager:

    def __init__(self, song, servo, led, ui, sound_player, trigger, play_indicate_note):

        self.song = song
        self.servo = servo
        self.led = led
        self.ui = ui
        self.sound_player = sound_player
        self.trigger = trigger
        self.play_indicate_note = play_indicate_note

        self.state = "playing_note"
        self.state_start_time = time.time()
        self.note_display_start_time = time.time()

        self.last_green_update = 0.0

        self.running = True
        self.timing_active = False
        self.timer_start = 0
        self.finish_alert_active = False
        self.finish_alert_cancelable = False

        self.TRIGGER_MAPPING = {
            62: 0x01, 64:0x02, 65:0x03,67:0x04
        }
        self.LED_MAPPING = {
            62: 0x05, 64:0x06, 65:0x07,67:0x08
        }

        
    def update(self,current_time):
        if self.state == "playing_note":
            self._update_playing_note(current_time)
        elif self.state == "waiting_servo":
            self._update_waiting_servo(current_time)
        elif self.state == "waiting_input":
            self._update_waiting_input(current_time)

    def _update_playing_note(self, current_time):
        if current_time - self.state_start_time < 3.0:
            print("   first time into _update_playing_note <3.0!")
            return

        # 发送开始变黄的trigger
        if self.trigger:
            self.trigger.send_trigger(self.LED_MAPPING[self.song.expected_note])
        
        self.led.to_yellow(self.song.note_to_index[self.song.expected_note] * 2 + 14)

        if self.play_indicate_note:
            self.sound_player.play(self.song.expected_note)

        print(f"[INFO] Playing note {self.song.expected_note}  ",
        f"Servo num = {self.TRIGGER_MAPPING[self.song.expected_note]}  ",
        f"Keyboard num = {self.TRIGGER_MAPPING[self.song.expected_note]+1}",
        )
        
        self.state = "waiting_servo"
        self.state_start_time = current_time

        # self.ui.display_pressed = None
        # self.ui.display_result = None
        self.timing_active = False

        if self.song.current_index == 0:
            self.finish_alert_active = True
            self.ui.finish_alert_start = pygame.time.get_ticks()
            self.finish_alert_cancelable = False


    def _update_waiting_servo(self, current_time):
        if current_time - self.state_start_time < 3.0:
            # print("   _update_waiting_servo <3.0!")
            return

        # 发送开始变绿的trigger
        if self.trigger:
            self.trigger.send_trigger(self.TRIGGER_MAPPING[self.song.expected_note])
        self.led.to_green(self.song.note_to_index[self.song.expected_note] * 2 + 14)

        if self.servo:
            self.servo.set_servo(self.song.expected_note)

        self.note_display_start_time = current_time
        self.state = "waiting_input"

    def _update_waiting_input(self, current_time):
        if current_time - self.note_display_start_time < 3.0:
            # print("   _update_waiting_input <3.0!")
            return

        self.led.clear_all()

        """ if self.timing_active and current_time - self.timer_start >= self.song.expected_duration + 4.0:
            self.state = "playing_note" 
        elif not self.timing_active and current_time - self.note_display_start_time >= 6.0: """

        if current_time - self.note_display_start_time >= 6.0:
            print("   _update_waiting_input >= 3.0!")
            if self.servo:
                self.servo.set_servo(5)
            print("-")

            self.song.advance_note()
                # 打乱顺序
            if self.song.current_index == 0:
                self.song.section_shuffle()
                print("shuffled!")
                
            self.state = "playing_note"

    def handle_finish_alert(self, new_input):
        if self.finish_alert_active:
            if pygame.time.get_ticks() - self.ui.finish_alert_start >= 500:
                self.finish_alert_cancelable = True
            if self.finish_alert_cancelable and new_input:
                self.finish_alert_active = False

    def notify_correct_input(self):
        self.timing_active = True
        self.timer_start = time.time()
        self.ui.display_result = True

    def reset_timer(self):
        self.timing_active = False
