"""棋盘与棋子渲染模块（依赖 pygame）。

只负责把局面画到屏幕上，不包含游戏逻辑。
"""
import pygame

from . import constants as C
from .fonts import get_font


def draw_chessboard(screen: pygame.Surface) -> None:
    """绘制 9x10 中国象棋棋盘（木纹底板 + 深棕网格线）。"""
    start_x, start_y = C.START_X, C.START_Y
    span = C.LINE_SPAN
    max_x = start_x + 8 * span
    max_y = start_y + 9 * span
    mid_end_y = start_y + 4 * span      # 楚河汉界上沿
    min_start_y = start_y + 5 * span    # 楚河汉界下沿

    # 木纹底板 + 外框
    pad = 14
    board_rect = pygame.Rect(start_x - pad, start_y - pad,
                             (max_x - start_x) + 2 * pad,
                             (max_y - start_y) + 2 * pad)
    _draw_wood(screen, board_rect)

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

    # 河界文字（描边艺术字）
    _draw_river_text(screen, "楚  河", start_x + 2 * span, start_y + 4 * span + 12)
    _draw_river_text(screen, "汉  界", start_x + 5 * span, start_y + 4 * span + 12)


def _draw_wood(screen, rect: pygame.Rect) -> None:
    """木纹底板：木色底 + 深色木纹条纹 + 深棕外框。"""
    pygame.draw.rect(screen, C.WOOD_BASE, rect, border_radius=8)
    for y in range(rect.top + 4, rect.bottom, 10):
        pygame.draw.line(screen, C.WOOD_GRAIN,
                         (rect.left + 4, y), (rect.right - 4, y), 1)
    pygame.draw.rect(screen, C.BOARD_FRAME, rect, 3, border_radius=8)


def _draw_river_text(screen, text: str, x: int, y: int,
                     size: int = 24, color=C.WOOD_RIVER) -> None:
    """河界文字：深棕描边 + 暖棕主体（四向错位模拟描边）。"""
    font = get_font(size)
    main = font.render(text, True, color)
    shadow = font.render(text, True, C.BOARD_FRAME)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        screen.blit(shadow, (x + dx, y + dy))
    screen.blit(main, (x, y))


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
    """在指定棋盘格绘制棋子图片（居中，附细描边圆环）。"""
    px, py = board_pos_to_pixel(x, y)
    radius = C.PIECE_SIZE // 2 + 2
    pygame.draw.circle(screen, C.BOARD_FRAME, (px, py), radius, 2)
    rect = image.get_rect(center=(px, py))
    screen.blit(image, rect)


def draw_last_move(screen: pygame.Surface, fx, fy, tx, ty) -> None:
    """标记最近一步：起点实心点 + 终点圆环（琥珀色）。"""
    if fx is None:
        return
    sfx, sfy = board_pos_to_pixel(fx, fy)
    stx, sty = board_pos_to_pixel(tx, ty)
    pygame.draw.circle(screen, C.LAST_MOVE_COLOR, (sfx, sfy), 5)
    pygame.draw.circle(screen, C.LAST_MOVE_COLOR, (stx, sty), C.LINE_SPAN // 2 - 4, 3)


def draw_check_ring(screen: pygame.Surface, x: int, y: int) -> None:
    """被将军方的将/帅外圈红色警报环。"""
    px, py = board_pos_to_pixel(x, y)
    radius = C.PIECE_SIZE // 2 + 6
    pygame.draw.circle(screen, C.CHECK_RING_COLOR, (px, py), radius, 4)


def draw_text(screen: pygame.Surface, text: str, x: int, y: int,
              size: int = 18, color=C.TEXT_COLOR) -> None:
    """在屏幕 (x, y) 处绘制文字。"""
    font = get_font(size)
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))
