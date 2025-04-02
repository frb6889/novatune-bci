#NEO:获取trigger box
""" from device.trigger_box import TriggerNeuracle """
import mido
import pygame
import pygame.freetype
import sys
import json
from song_loader import load_song


# NEO:trigger box端口号
""" trigger = TriggerNeuracle(port='COM6')   """

# 加载歌曲
song_name = "dongfanghong"
song_sections = load_song(song_name)
if song_sections:
    print(f"已加载曲子 '{song_name}': {song_sections}")
else:
    print(f"加载曲子 '{song_name}' 失败")


# -------------------------
# 初始化 pygame 与界面
# -------------------------
pygame.init()
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MIDI 练习界面")

# TODO:字体正确性
font = pygame.freetype.SysFont(None, 24)
clock = pygame.time.Clock()

# 加载背景图片（键盘图像）
try:
    keyboard_img = pygame.image.load("pygame_img/keys.png").convert_alpha()

    img_width, img_height = keyboard_img.get_size()
    scale = min(WIDTH / img_width, HEIGHT / img_height)
    keyboard_img = pygame.transform.scale(keyboard_img, (img_width * scale, img_height * scale))

    # 计算居中位置
    x_offset = (WIDTH - img_width * scale) // 2
    y_offset = (HEIGHT - img_height * scale) // 2
except Exception as e:
    print(f"加载背景图片失败: {e}")
    sys.exit()

# 初始化声音模块
pygame.mixer.init()

# -------------------------
# 定义 MIDI 与声音数据
# -------------------------
MIDI_DEVICE_NAME = "Vboard 49"

# 用来映射琴键位置的json
with open("data/note_to_index.json", "r") as f:
    note_to_index = json.load(f)
note_to_index = {int(k): v for k, v in note_to_index.items()}

# 琴键对应的音频文件
with open("data/note_sounds.json", "r") as f:
    NOTE_SOUNDS = json.load(f)
NOTE_SOUNDS = {int(k): v for k, v in NOTE_SOUNDS.items()}


# trigger 对应字典
TRIGGER_MAPPING = {
    48: 0x01,
    50: 0x02,
    52: 0x03,
    53: 0x04,
    55: 0x05,
    57: 0x06,
    59: 0x07,
    60: 0x08,
    62: 0x09,
    64: 0x0A,
    65: 0x0B,
    67: 0x0C,
    69: 0x0D,
    71: 0x0E,
    72: 0x0F,
    74: 0x10,
    76: 0x11,
    77: 0x12,
    79: 0x13,
}



# 当前段落和音符索引
current_section = 0
current_index = 0
song_notes = song_sections[current_section]

# 界面显示变量：当前期待的音符、按下的音符、判断结果
display_expected = song_notes[current_index]
display_pressed = None
display_result = None

# -------------------------
# 打开 MIDI 设备
# -------------------------
input_names = mido.get_input_names()
target_device = next((name for name in input_names if MIDI_DEVICE_NAME in name), None)
if not target_device:
    print(f"未找到设备: {MIDI_DEVICE_NAME}")
    sys.exit()

inport = mido.open_input(target_device)
print(f"监听 MIDI 设备: {target_device}")

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)

# 构建钢琴键列表（按 NOTE_SOUNDS 的 key 排序）
piano_keys = sorted(NOTE_SOUNDS.keys())
num_keys = len(piano_keys)

key_width = WIDTH / 21
key_height = 650
piano_y = HEIGHT - key_height

# -------------------------
# 主循环：监听 MIDI 并更新界面
# -------------------------
running = True
while running:
    # 处理 pygame 事件（关闭窗口）
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 清除屏幕
    screen.fill(WHITE)

    # 检查是否有 MIDI 事件
    msg = inport.poll()
    if msg is not None:
        # 控制指令：note 36 切换上一段，84 切换下一段
        if msg.type == 'note_on' and msg.note in (36, 84):
            if msg.note == 36:
                current_section = (current_section - 1) % len(song_sections)
                print(f"切换到上一段: 第 {current_section + 1} 段")
            elif msg.note == 84:
                current_section = (current_section + 1) % len(song_sections)
                print(f"切换到下一段: 第 {current_section + 1} 段")
            song_notes = song_sections[current_section]
            current_index = 0
            display_expected = song_notes[current_index]
            display_pressed = None
            display_result = None
        # MIDI按键处理
        elif msg.type == 'note_on':
            note = msg.note
            # 播放对应声音
            if note in NOTE_SOUNDS:
                try:
                    pygame.mixer.Sound(NOTE_SOUNDS[note]).play()
                except Exception as e:
                    print(f"播放声音错误: {e}")
            # NEO:每次琴键输入时，发送对应的 trigger
            """ if note in TRIGGER_MAPPING:
                    trigger_value = TRIGGER_MAPPING[note]
                    trigger.send_trigger(trigger_value)
                    print(f"发送 trigger: {hex(trigger_value)} 对应音符: {note}") """

            # 更新显示按键与结果
            display_pressed = note
            expected_note = song_notes[current_index]
            is_correct = (note == expected_note)
            display_result = is_correct
            # 如果按对了，切换到下一个期望按键
            if is_correct:
                current_index = (current_index + 1) % len(song_notes)
                display_expected = song_notes[current_index]
            else:
                display_expected = expected_note

    # -------------------------
    # 绘制界面
    # -------------------------
    # 背景键盘图像
    screen.blit(keyboard_img, (x_offset, y_offset))

    # 文本信息
    section_text, _ = font.render(f"current section: {current_section + 1}", BLACK)
    screen.blit(section_text, (50, 20))
    expected_text, _ = font.render(f"expect: {display_expected}", BLACK)
    screen.blit(expected_text, (50, 60))
    pressed_str = str(display_pressed) if display_pressed is not None else "-"
    color = GREEN if display_result else RED if display_result is not None else BLACK
    pressed_text, _ = font.render(f"pressed: {pressed_str}", color)
    screen.blit(pressed_text, (50, 100))
    if display_result is None:
        result_str = "waiting for input..."
    else:
        result_str = "Correct!" if display_result else "False.."
    result_color = GREEN if display_result else RED if display_result is not None else BLACK
    result_text, _ = font.render(f"result: {result_str}", result_color)
    screen.blit(result_text, (50, 140))

    # 绘制expect指示标记
    try:
        if display_expected in piano_keys:
            key_index = note_to_index[display_expected]
            x = key_index * key_width
            y = 550

            # 计算三角形顶点（向下的小三角形）
            triangle_size = 30
            triangle_top = (int(x + key_width / 2), int(y - triangle_size))
            triangle_left = (int(x + key_width / 4), int(y - 5))
            triangle_right = (int(x + 3 * key_width / 4), int(y - 5)) 

            pygame.draw.polygon(screen, BLUE, [triangle_top, triangle_left, triangle_right])

    except Exception as e:
        print(f"绘制指示标记错误: {e}")

    # 绘制按键标记：正确绿圆圈，错误红圆圈
    try:
        if display_pressed in piano_keys:
            key_index = note_to_index[display_pressed]
            x = key_index * key_width
            y = piano_y

            marker_color = GREEN if display_result else RED
            marker_radius = int(key_width / 4)
            marker_center = (int(x + key_width / 2), int(y + key_height / 2))

            pygame.draw.circle(screen, marker_color, marker_center, marker_radius, 4)

    except Exception as e:
        print(f"绘制按键标记错误: {e}")

    # 更新屏幕显示
    pygame.display.flip()
    clock.tick(30)

inport.close()
pygame.quit()
