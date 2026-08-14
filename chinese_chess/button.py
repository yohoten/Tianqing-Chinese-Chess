"""按钮控件（修复自原 botton.py）。"""
import pygame

from .fonts import get_font


class Button:
    """简单文字按钮。is_clicked 接收事件时的鼠标位置，避免误触。"""

    def __init__(self, screen, msg, left, top, width=150, height=50):
        self.screen = screen
        self.msg = msg
        self.left = left
        self.top = top
        self.width = width
        self.height = height

        self.button_color = (72, 61, 139)   # 深蓝
        self.text_color = (255, 255, 255)   # 白色
        self.hover_color = (100, 88, 170)

        pygame.font.init()
        self.font = get_font(20)
        self.rect = pygame.Rect(left, top, width, height)
        self._render()

    def _render(self):
        self.msg_img = self.font.render(self.msg, True, self.text_color)
        self.msg_img_rect = self.msg_img.get_rect(center=self.rect.center)

    def is_clicked(self, pos) -> bool:
        """pos 为 pygame.mouse.get_pos() 或事件位置，点在按钮内返回 True。"""
        return self.rect.collidepoint(pos)

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.button_color
        pygame.draw.rect(self.screen, color, self.rect, border_radius=6)
        pygame.draw.rect(self.screen, self.text_color, self.rect, 2, border_radius=6)
        self.screen.blit(self.msg_img, self.msg_img_rect)
