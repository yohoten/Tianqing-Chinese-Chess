"""棋盘与棋子渲染模块（依赖 pygame）。

只负责把局面画到屏幕上，不包含游戏逻辑。
"""
import pygame

from . import constants as C
from .fonts import get_font


def draw_chessboard(screen: pygame.Surface) -> None:
    """绘制 9x10 中国象棋棋盘。"""
    start_x, start_y = C.START_X, C.START_Y
    span = C.LINE_SPAN
    max_x = start_x + 8 * span
    max_y = start_y + 9 * span
    mid_end_y = start_y + 4 * span      # 楚河汉界上沿
    min_start_y = start_y + 5 * span    # 楚河汉界下沿

    # 竖线：两侧为整线，中间被河界断开
    for i in range(9):
        x = start_x + i * span
        if i in (0, 8):
            pygame.draw.line(screen, C.LINE_COLOR,
                             (x, start_y), (x, max_y), 2)
        else:
            pygame.draw.line(screen, C.LINE_COLOR,
                             (x, start_y), (x, mid_end_y), 2)
            pygame.draw.line(screen, C.LINE_COLOR,
                             (x, min_start_y), (x, max_y), 2)

    # 横线
    for i in range(10):
        y = start_y + i * span
        pygame.draw.line(screen, C.LINE_COLOR,
                         (start_x, y), (max_x, y), 2)

    # 两侧九宫斜线
    palace_x1 = start_x + 3 * span
    palace_x2 = start_x + 5 * span
    pygame.draw.line(screen, C.LINE_COLOR,
                     (palace_x1, start_y), (palace_x2, start_y + 2 * span), 2)
    pygame.draw.line(screen, C.LINE_COLOR,
                     (palace_x1, start_y + 2 * span), (palace_x2, start_y), 2)
    pygame.draw.line(screen, C.LINE_COLOR,
                     (palace_x1, min_start_y), (palace_x2, max_y), 2)
    pygame.draw.line(screen, C.LINE_COLOR,
                     (palace_x1, max_y), (palace_x2, min_start_y), 2)

    # 河界文字
    draw_text(screen, "楚  河", start_x + 2 * span, start_y + 4 * span + 10,
              size=22, color=(120, 60, 30))
    draw_text(screen, "汉  界", start_x + 5 * span, start_y + 4 * span + 10,
              size=22, color=(120, 60, 30))


def board_pos_to_pixel(x: int, y: int):
    """棋子坐标 -> 屏幕中心像素坐标。"""
    px = C.START_X + x * C.LINE_SPAN
    py = C.START_Y + y * C.LINE_SPAN
    return px, py


def draw_highlight(screen: pygame.Surface, x: int, y: int) -> None:
    """绘制选中棋子的高亮框。"""
    px, py = board_pos_to_pixel(x, y)
    radius = C.LINE_SPAN // 2 - 4
    pygame.draw.circle(screen, C.HIGHLIGHT_COLOR, (px, py), radius, 3)


def draw_hint(screen: pygame.Surface, x: int, y: int) -> None:
    """绘制可走位置的提示点。"""
    px, py = board_pos_to_pixel(x, y)
    pygame.draw.circle(screen, C.HINT_COLOR, (px, py), 6)


def draw_piece(screen: pygame.Surface, image: pygame.Surface, x: int, y: int) -> None:
    """在指定棋盘格绘制棋子图片（居中）。"""
    px, py = board_pos_to_pixel(x, y)
    rect = image.get_rect(center=(px, py))
    screen.blit(image, rect)


def draw_text(screen: pygame.Surface, text: str, x: int, y: int,
              size: int = 18, color=C.TEXT_COLOR) -> None:
    """在屏幕 (x, y) 处绘制文字。"""
    font = get_font(size)
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))
