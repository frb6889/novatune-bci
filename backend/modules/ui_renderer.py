import pygame
import pygame.freetype
import sys

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MAIN_COLOR = (99, 76, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

class UIRenderer:
    def __init__(self, song):
        pygame.freetype.init()
        
        self.song = song
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("MIDI 练习界面")
        self.font = pygame.freetype.SysFont(None, 24)

        self.display_pressed = None
        self.display_result = None
        self.finish_alert_start = 0

        try:
            self.keyboard_img = pygame.image.load("assets/pygame_img/keys.png").convert_alpha()
            img_w, img_h = self.keyboard_img.get_size()
            scale = min(SCREEN_WIDTH/img_w, SCREEN_HEIGHT/img_h)
            self.keyboard_img = pygame.transform.scale(self.keyboard_img, (int(img_w*scale), int(img_h*scale)))
            self.x_offset = (SCREEN_WIDTH - int(img_w*scale)) // 2
            self.y_offset = (SCREEN_HEIGHT - int(img_h*scale)) // 2 + 50
        except Exception as e:
            print(f"加载背景图片失败: {e}")
            sys.exit()

        try:
            self.finish_alert = pygame.image.load("assets/pygame_img/finish_alert.png").convert_alpha()
            fw, fh = self.finish_alert.get_size()
            self.finish_alert = pygame.transform.scale(self.finish_alert, (int(fw*0.4), int(fh*0.4)))
        except:
            self.finish_alert = None

        scale = 0.6
        self.section_images = []
        self.jianpu_images = []
        for i in range(song.num_sections):
            try:
                img = pygame.image.load(f"assets/pygame_img/section_{i+1}.png").convert_alpha()
                w,h = img.get_size()
                self.section_images.append(pygame.transform.scale(img, (int(w*scale), int(h*scale))))
            except:
                self.section_images.append(None)

            try:
                img = pygame.image.load(f"assets/pygame_img/jianpu/dongfanghong_{i+1}.png").convert_alpha()
                w,h = img.get_size()
                self.jianpu_images.append(pygame.transform.scale(img, (int(w*scale), int(h*scale))))
            except:
                self.jianpu_images.append(None)

        self.key_width = SCREEN_WIDTH / 21
        self.key_height = self.y_offset
        self.piano_y = self.y_offset
        self.clock = pygame.time.Clock()

    def render(self, finish_alert_active=False):
        self.screen.fill(WHITE)
        self.screen.blit(self.keyboard_img, (self.x_offset, self.y_offset))

        if self.section_images[self.song.current_section]:
            self.screen.blit(self.section_images[self.song.current_section], (SCREEN_WIDTH/2 - 120, 50))
        if self.jianpu_images[self.song.current_section]:
            self.screen.blit(self.jianpu_images[self.song.current_section], (SCREEN_WIDTH/2 - 250, 100))

        exp_surf, _ = self.font.render(
            f"expect: {self.song.expected_note} (duration: {self.song.expected_duration})",
            BLACK
        )
        self.screen.blit(exp_surf, (50, 60))

        color = GREEN if self.display_result else RED if self.display_result is not None else BLACK
        pres_surf, _ = self.font.render(f"pressed: {self.display_pressed or '-'}", color)
        self.screen.blit(pres_surf, (50, 100))

        res_text = "Correct!" if self.display_result else "False.." if self.display_result is not None else "waiting for input..."
        res_surf, _ = self.font.render(f"result: {res_text}", color)
        self.screen.blit(res_surf, (50, 140))

        try:
            if self.song.expected_note in self.song.note_sounds:
                kidx = self.song.note_to_index[self.song.expected_note]
                x = kidx * self.key_width
                y = self.piano_y + 270
                ts = 40
                pts = [
                    (x + self.key_width/2, y - ts),
                    (x + self.key_width/4 - 10, y - 5),
                    (x + 3*self.key_width/4 + 10, y - 5)
                ]
                pygame.draw.polygon(self.screen, MAIN_COLOR, [(int(px), int(py)) for px, py in pts])
        except Exception as e:
            print(f"绘制指示标记错误: {e}")

        try:
            if self.display_pressed in self.song.note_to_index:
                kidx = self.song.note_to_index[self.display_pressed]
                x = kidx * self.key_width
                y = self.piano_y
                center = (int(x + self.key_width/2), int(y + self.key_height/2))
                pygame.draw.circle(self.screen, color, center, int(self.key_width/4), 4)
        except Exception as e:
            print(f"绘制按键标记错误: {e}")

        if finish_alert_active and self.finish_alert:
            ax = (SCREEN_WIDTH - self.finish_alert.get_width()) // 2
            ay = 100
            self.screen.blit(self.finish_alert, (ax, ay))

        pygame.display.flip()
