import mido
import pygame
import pygame.freetype
import sys
import json
import time
import serial 
from song_loader import load_song

# NEO:获取trigger box
# from device.trigger_box import TriggerNeuracle
# trigger = TriggerNeuracle(port='COM6')


# *** MIDI和钢琴相关初始化 ***
pygame.mixer.init()
ser = serial.Serial('/dev/cu.usbmodem141401', 9600, timeout=0.1)


MIDI_DEVICE_NAME = mido.get_input_names()[0]


# 谱子与时值，后者默认为1
song_sections = [
    [(67, 1), (67, 0.5), (69, 0.5), (62, 2), (60, 1), (60, 0.5), (57, 0.5), (62, 2)],
    [(67, 1), (67, 1), (69, 0.5), (72, 0.5), (69, 0.5), (67, 0.5), (60, 1), (60, 0.5), (57, 0.5), (62, 2)],
    [(67, 1), (62, 1), (60, 1), (59, 0.5), (57, 0.5), (55, 1), (67, 1), (62, 1)],
    [(64, 0.5), (62, 0.5), (60, 1), (60, 0.5), (57, 0.5), (62, 0.5), (64, 0.5), (62, 0.5),
     (60, 0.5), (62, 0.5), (60, 0.5), (59, 0.5), (57, 0.5), (55, 2)],
    [(67, 1), (62, 1), (60, 1), (59, 0.5), (57, 0.5), (55, 1), (67, 1), (62, 1)],
    [(64, 0.5), (62, 0.5), (60, 1), (60, 0.5), (57, 0.5), (62, 0.5), (64, 0.5), (62, 0.5),
     (60, 0.5), (74, 0.5), (72, 0.5), (71, 0.5), (69, 0.5), (67, 2)],
    [
        (67, 1), (67, 0.5), (69, 0.5), (62, 2), (60, 1), (60, 0.5), (57, 0.5), (62, 2),
        (67, 1), (67, 1), (69, 0.5), (72, 0.5), (69, 0.5), (67, 0.5), (60, 1), (60, 0.5), (57, 0.5), (62, 2),
        (67, 1), (62, 1), (60, 1), (59, 0.5), (57, 0.5), (55, 1), (67, 1), (62, 1),
        (64, 0.5), (62, 0.5), (60, 1), (60, 0.5), (57, 0.5), (62, 0.5), (64, 0.5), (62, 0.5),
        (60, 0.5), (62, 0.5), (60, 0.5), (59, 0.5), (57, 0.5), (55, 2),
        (67, 1), (62, 1), (60, 1), (59, 0.5), (57, 0.5), (55, 1), (67, 1), (62, 1),
        (64, 0.5), (62, 0.5), (60, 1), (60, 0.5), (57, 0.5), (62, 0.5), (64, 0.5), (62, 0.5),
        (60, 0.5), (74, 0.5), (72, 0.5), (71, 0.5), (69, 0.5), (67, 2),
    ]
]

# 原本的 load_song 函数：
# song_name = "dongfanghong"
# song_sections = load_song(song_name)
# if song_sections:
#     print(f"已加载曲子 '{song_name}': {song_sections}")
# else:
#     print(f"加载曲子 '{song_name}' 失败")
#     sys.exit()


with open("data/note_to_index.json", "r") as f:
    note_to_index = json.load(f)
note_to_index = {int(k): v for k, v in note_to_index.items()}

# --- LED 控制函数 ---
def set_led(idx, brightness):
    """发送 idx,brightness 到 Arduino，点亮/调暗一颗 LED"""
    cmd = f"{idx},{brightness}\n"
    ser.write(cmd.encode())

def clear_leds():
    """全灭所有 LED"""
    for i in range(60):
        set_led(i, 0)

# 琴键对应的音频文件
with open("data/note_sounds.json", "r") as f:
    NOTE_SOUNDS = json.load(f)
NOTE_SOUNDS = {int(k): v for k, v in NOTE_SOUNDS.items()}

# trigger 对应字典
TRIGGER_MAPPING = {
    48: 0x01, 50: 0x02, 52: 0x03, 53: 0x04, 55: 0x05,
    57: 0x06, 59: 0x07, 60: 0x08, 62: 0x09, 64: 0x0A,
    65: 0x0B, 67: 0x0C, 69: 0x0D, 71: 0x0E, 72: 0x0F,
    74: 0x10, 76: 0x11, 77: 0x12, 79: 0x13,
}

# 打开 MIDI 设备
input_names = mido.get_input_names()
target_device = next((name for name in input_names if MIDI_DEVICE_NAME in name), None)
if not target_device:
    print(f"未找到设备: {MIDI_DEVICE_NAME}")
    sys.exit()
inport = mido.open_input(target_device)
print(f"监听 MIDI 设备: {target_device}")

# *** pygame 初始化 ***
pygame.init()
WIDTH, HEIGHT = 1300, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MIDI 练习界面")
font = pygame.freetype.SysFont(None, 24)
clock = pygame.time.Clock()

# *** 加载图片 ***
try:
    keyboard_img = pygame.image.load("pygame_img/keys.png").convert_alpha()
    img_w, img_h = keyboard_img.get_size()
    scale = min(WIDTH/img_w, HEIGHT/img_h)
    keyboard_img = pygame.transform.scale(keyboard_img, (int(img_w*scale), int(img_h*scale)))
    x_offset = (WIDTH - int(img_w*scale)) // 2
    y_offset = (HEIGHT - int(img_h*scale)) // 2 + 50
except Exception as e:
    print(f"加载背景图片失败: {e}")
    sys.exit()

try:
    finish_alert = pygame.image.load("pygame_img/finish_alert.png").convert_alpha()
    fw, fh = finish_alert.get_size()
    finish_alert = pygame.transform.scale(finish_alert, (int(fw*0.4), int(fh*0.4)))
except Exception:
    finish_alert = None

scale = 0.6
section_images = []
num_sections = len(song_sections)
for i in range(num_sections):
    path = f"pygame_img/section_{i+1}.png"
    try:
        img = pygame.image.load(path).convert_alpha()
        w,h = img.get_size()
        section_images.append(pygame.transform.scale(img, (int(w*scale), int(h*scale))))
    except:
        section_images.append(None)

jianpu_images = []
for i in range(num_sections):
    path = f"pygame_img/jianpu/dongfanghong_{i+1}.png"
    try:
        img = pygame.image.load(path).convert_alpha()
        w,h = img.get_size()
        jianpu_images.append(pygame.transform.scale(img, (int(w*scale), int(h*scale))))
    except:
        jianpu_images.append(None)

# *** 当前段落和音符索引 ***
current_section = 0
current_index   = 0
song_notes      = song_sections[current_section]
expected_note, expected_duration = song_notes[current_index]

# 界面显示变量
display_pressed = None
display_result  = None

# --- LED初始: 点亮第一颗expect灯
clear_leds()
set_led(note_to_index[expected_note]*2+14, 255)

# --- LED: 计时控制
timing_active = False
timer_start   = 0

# 完成提示控制
section_complete     = False
finish_alert_active  = False
finish_alert_start   = 0
finish_alert_cancelable = False

# 颜色定义
MAIN_COLOR = (99, 76, 255)
WHITE      = (255,255,255)
BLACK      = (0,0,0)
GREEN      = (0,255,0)
RED        = (255,0,0)

# 钢琴键索引
piano_keys = sorted(NOTE_SOUNDS.keys())
key_width  = WIDTH / 21
key_height = y_offset
piano_y    = y_offset

# -------------------------
# 主循环：监听 MIDI 并更新界面
# -------------------------
running = True
while running:
    new_input = False
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False
        elif evt.type == pygame.KEYDOWN:
            new_input = True

    msg = inport.poll()


    if msg:

        new_input = True
        if msg.type == 'note_on' and msg.note in (36, 84):
            # 切换段落
            if msg.note == 36:
                current_section = (current_section - 1) % len(song_sections)
            else:
                current_section = (current_section + 1) % len(song_sections)
            song_notes = song_sections[current_section]
            current_index = 0
            expected_note, expected_duration = song_notes[current_index]
            display_pressed = None
            display_result  = None
            timing_active   = False
            # 重点亮新段第一灯
            clear_leds()
            set_led(note_to_index[expected_note]*2+14, 255)
            finish_alert_active = False
            finish_alert_cancelable = False

        elif msg.type == 'note_on':
            note = msg.note
            if note in NOTE_SOUNDS:
                try:
                    pygame.mixer.Sound(NOTE_SOUNDS[note]).play()
                    # NEO:每次琴键输入时，发送对应的 trigger
                    """ if note in TRIGGER_MAPPING:
                        trig = TRIGGER_MAPPING[note]
                        trigger.send_trigger(trig)
                    """
                except:
                    pass

            display_pressed = note
            if not timing_active and note == expected_note:
                # 按对，开始计时
                display_result = True
                timing_active  = True
                timer_start    = time.time()
            else:
                display_result = False

    # 计时完成后切换到下一个
    if timing_active:
        if time.time() - timer_start >= expected_duration:
            clear_leds()
            current_index = (current_index + 1) % len(song_notes)
            expected_note, expected_duration = song_notes[current_index]
            set_led(note_to_index[expected_note]*2+14, 255)
            timing_active    = False
            display_pressed  = None
            display_result   = None
            if current_index == 0:
                finish_alert_active = True
                finish_alert_start  = pygame.time.get_ticks()
                finish_alert_cancelable = False

    # 处理完成提示
    if finish_alert_active and finish_alert:
        if pygame.time.get_ticks() - finish_alert_start >= 500:
            finish_alert_cancelable = True
        if finish_alert_cancelable and new_input:
            finish_alert_active = False

    # 渲染界面
    screen.fill(WHITE)
    screen.blit(keyboard_img, (x_offset, y_offset))
    if 0 <= current_section < len(jianpu_images) and jianpu_images[current_section]:
        screen.blit(jianpu_images[current_section], (WIDTH/2-250, 100))
    if 0 <= current_section < len(section_images) and section_images[current_section]:
        screen.blit(section_images[current_section], (WIDTH/2-120, 50))

    exp_surf, _ = font.render(f"expect: {expected_note} (note duration: {expected_duration})", BLACK)
    screen.blit(exp_surf, (50, 60))
    pres_surf, _ = font.render(f"pressed: {display_pressed or '-'}", GREEN if display_result else RED if display_result is not None else BLACK)
    screen.blit(pres_surf, (50, 100))
    res = "Correct!" if display_result else "False.." if display_result is not None else "waiting for input..."
    res_surf, _ = font.render(f"result: {res}", GREEN if display_result else RED if display_result is not None else BLACK)
    screen.blit(res_surf, (50, 140))

    # expect 指示三角
    try:
        if expected_note in piano_keys:
            kidx = note_to_index[expected_note]
            x = kidx * key_width
            y = piano_y + 270
            ts = 40
            pts = [(x+key_width/2, y-ts), (x+key_width/4-10, y-5), (x+3*key_width/4+10, y-5)]
            pygame.draw.polygon(screen, MAIN_COLOR, [(int(px),int(py)) for px,py in pts])
    except Exception as e:
        print(f"绘制指示标记错误: {e}")

    # 按键圆圈标记
    try:
        if display_pressed in piano_keys:
            kidx = note_to_index[display_pressed]
            x = kidx * key_width
            y = piano_y
            color = GREEN if display_result else RED
            center = (int(x+key_width/2), int(y + key_height / 2))
            pygame.draw.circle(screen, color, center, int(key_width/4), 4)
    except Exception as e:
        print(f"绘制按键标记错误: {e}")

    # 完成弹窗
    if finish_alert_active and finish_alert:
        ax = (WIDTH - finish_alert.get_width())//2
        ay = 100
        screen.blit(finish_alert, (ax, ay))

    pygame.display.flip()
    clock.tick(30)

inport.close()
pygame.quit()
ser.close()
