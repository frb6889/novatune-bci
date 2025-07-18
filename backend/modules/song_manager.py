import os
import sys
import json
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')) 
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')) 

from songs import get_song

class SongManager:
    def __init__(self, song_name, note_index_file, note_sounds_file):
        self.song_name = song_name  # 保存歌曲名
        self.original_sections = get_song(song_name)
        self.num_sections = len(self.original_sections)
        self.current_section = 0
        self.current_index = 0

        # 是否打乱顺序，仅对 doremifa 启用
        self.shuffle_enabled = (song_name == "remifaso" or song_name =="doremifa")

        # 创建副本用于打乱播放（不影响原始曲目）
        self.song_sections = [section[:] for section in self.original_sections]

        # 加载 note -> LED 索引映射
        with open(note_index_file, "r") as f:
            tmp = json.load(f)
        self.note_to_index = {int(k): v for k, v in tmp.items()}

        # 加载 note -> 音频文件映射
        with open(note_sounds_file, "r") as f:
            tmp = json.load(f)
        self.note_sounds = {int(k): v for k, v in tmp.items()}

        # 初始就打乱一次
        self.reset()

    @property
    def expected_note(self):
        note, _ = self.song_sections[self.current_section][self.current_index]
        return note

    @property
    def expected_duration(self):
        _, dur = self.song_sections[self.current_section][self.current_index]
        return dur

    def prev_section(self):
        self.current_section = (self.current_section - 1) % self.num_sections
        self.reset()

    def next_section(self):
        self.current_section = (self.current_section + 1) % self.num_sections
        self.reset()

    def advance_note(self):
        sec = self.song_sections[self.current_section]
        self.current_index = (self.current_index + 1) % len(sec)

    def reset(self):
        self.current_index = 0
        if self.shuffle_enabled:
            self.song_sections[self.current_section] = self.original_sections[self.current_section][:]
            random.shuffle(self.song_sections[self.current_section])
        else:
            self.song_sections[self.current_section] = self.original_sections[self.current_section][:]
