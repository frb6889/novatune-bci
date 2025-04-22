import csv
import json
import time
import pygame
import argparse

# #NEO:获取trigger box
# from device.trigger_box import TriggerNeuracle
# trigger = TriggerNeuracle(port='COM6')

# #trigger 对应字典
# TRIGGER_MAPPING = {
#     48: 0x01, 50: 0x02, 52: 0x03, 53: 0x04, 55: 0x05,
#     57: 0x06, 59: 0x07, 60: 0x08, 62: 0x09, 64: 0x0A,
#     65: 0x0B, 67: 0x0C, 69: 0x0D, 71: 0x0E, 72: 0x0F,
#     74: 0x10, 76: 0x11, 77: 0x12, 79: 0x13,
# }

# 解析命令行参数
parser = argparse.ArgumentParser(description="播放 MIDI 回放音符")
parser.add_argument('--log_file', type=str, required=True, help="读取的 MIDI 键盘日志 CSV 文件路径")
args = parser.parse_args()

# 读取音符声音文件映射
with open("data/note_sounds.json", "r") as f:
    NOTE_SOUNDS = json.load(f)
NOTE_SOUNDS = {int(k): v for k, v in NOTE_SOUNDS.items()}

# 初始化声音系统
pygame.mixer.init()

# 读取记录的按键信息
log_file = args.log_file
with open(log_file, "r") as f:
    reader = csv.DictReader(f)
    notes = list(reader)

# 转换字段为正确格式
for note in notes:
    note['note'] = int(note['note'])
    note['start_time'] = float(note['start_time'])
    note['end_time'] = float(note['end_time'])
    note['duration'] = float(note['duration'])
    note['velocity'] = int(note['velocity'])

# 排序事件（按起始时间）
notes.sort(key=lambda x: x['start_time'])

print("🎵 开始回放 MIDI 演奏...")

# 基准时间
start_reference = notes[0]['start_time']
playback_start = time.time()

# 播放每个音符
for note_event in notes:
    delay = note_event['start_time'] - start_reference
    current_time = time.time()
    wait_time = (playback_start + delay) - current_time
    if wait_time > 0:
        time.sleep(wait_time)

    note = note_event['note']
    duration = note_event['duration']
    if note in NOTE_SOUNDS:
        try:
            sound = pygame.mixer.Sound(NOTE_SOUNDS[note])
            # # NEO:每次琴键输入时，发送对应的 trigger
            # if note in TRIGGER_MAPPING:
            #     trig = TRIGGER_MAPPING[note]
            #     trigger.send_trigger(trig)

            channel = sound.play()
            if channel is not None:
                channel.fadeout(int(duration * 1000))  # 以毫秒为单位
        except Exception as e:
            print(f"播放音符 {note} 时出错: {e}")

# 等待最后一个音符播放完成
print("回放结束，等待尾音结束...")

last_note_end = max(note['end_time'] for note in notes)
total_duration = last_note_end - start_reference
elapsed = time.time() - playback_start
remaining = total_duration - elapsed

if remaining > 0:
    time.sleep(remaining + 0.2)  # 加一点缓冲防止截断

print("✅ 所有音符播放完毕！")
