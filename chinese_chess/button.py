"""按钮控件（三态：hover / pressed / disabled）。

修复自原 botton.py；支持悬停高亮、按下凹陷、禁用置灰三种状态。
"""
import pygame

from .fonts import get_font


class Button:
    """文字按钮。is_clicked 接收事件时的鼠标位置，避免误触。"""

    def __init__(self, screen, msg, left, top, width=150, height=50,
                 disabled=False, color=(72, 61, 139)):
        self.screen = screen
        self.msg = msg
        self.left = left
        self.top = top
        self.width = width
        self.height = height

        self.button_color = color            # 正常（深蓝）
        self.text_color = (255, 255, 255)    # 白色
        self.hover_color = self._mix(color, (255, 255, 255), 0.22)
        self.pressed_color = self._mix(color, (0, 0, 0), 0.25)
        self.disabled = disabled

        pygame.font.init()
        self.font = get_font(20)
        self.rect = pygame.Rect(left, top, width, height)
        self._render()

    @staticmethod
    def _mix(c, target, ratio):
        """颜色向 target 方向插值 ratio。"""
        return tuple(int(a + (b - a) * ratio) for a, b in zip(c, target))

    def _render(self):
        self.msg_img = self.font.render(self.msg, True, self.text_color)
        self.msg_img_rect = self.msg_img.get_rect(center=self.rect.center)

    def is_clicked(self, pos) -> bool:
        """点在按钮内且未禁用时返回 True。"""
        return (not self.disabled) and self.rect.collidepoint(pos)

    def draw(self):
        if self.disabled:
            # 禁用态：置灰 + 半透明文字，无交互反馈
            pygame.draw.rect(self.screen, (170, 170, 170), self.rect, border_radius=6)
            pygame.draw.rect(self.screen, (130, 130, 130), self.rect, 2, border_radius=6)
            text = self.font.render(self.msg, True, (225, 225, 225))
            self.screen.blit(text, text.get_rect(center=self.rect.center))
            return

        mouse_pos = pygame.mouse.get_pos()
        hovered = self.rect.collidepoint(mouse_pos)
        pressed = hovered and pygame.mouse.get_pressed()[0]

        if pressed:
            color, border_w, offset = self.pressed_color, 3, 1
        elif hovered:
            color, border_w, offset = self.hover_color, 2, 0
        else:
            color, border_w, offset = self.button_color, 2, 0

        rect = self.rect.move(0, offset)
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        pygame.draw.rect(self.screen, self.text_color, rect, border_w, border_radius=6)
        self.screen.blit(self.msg_img, self.msg_img_rect.move(0, offset))
