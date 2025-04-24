# song_manager.py
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')) 
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')) 

import json
from songs import get_song

class SongManager:
    def __init__(self, song_name, note_index_file, note_sounds_file):
        # 加载曲目各段（每段是 [(note, duration), ...]）
        self.song_sections = get_song(song_name)
        self.num_sections = len(self.song_sections)
        # 当前处于第几个段落,段落内第几个音符
        self.current_section = 0
        self.current_index = 0

        # 加载 note -> LED 索引映射
        with open(note_index_file, "r") as f:
            tmp = json.load(f)
        self.note_to_index = {int(k): v for k, v in tmp.items()}

        # 加载 note -> 音频文件 映射
        with open(note_sounds_file, "r") as f:
            tmp = json.load(f)
        self.note_sounds = {int(k): v for k, v in tmp.items()}

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
        self.current_index = 0

    def next_section(self):
        self.current_section = (self.current_section + 1) % self.num_sections
        self.current_index = 0

    def advance_note(self):
        sec = self.song_sections[self.current_section]
        self.current_index = (self.current_index + 1) % len(sec)

    def reset(self):
        """重置回当前段落的第一个音符"""
        self.current_index = 0
