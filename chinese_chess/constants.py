"""全局常量与资源管理。

逻辑模块（pieces/ai）不依赖 pygame，图片只在渲染模块中按需加载。
"""
from pathlib import Path

# ---------------- 屏幕与棋盘 ----------------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 650

START_X = 50
START_Y = 50
LINE_SPAN = 60

BOARD_COLS = 9   # 棋盘列数（x 方向 0..8）
BOARD_ROWS = 10  # 棋盘行数（y 方向 0..9，红方在下）

# 棋盘有效区域（用于鼠标点击判定）
BOARD_MIN_X = START_X - LINE_SPAN / 2
BOARD_MAX_X = START_X + 8 * LINE_SPAN + LINE_SPAN / 2
BOARD_MIN_Y = START_Y - LINE_SPAN / 2
BOARD_MAX_Y = START_Y + 9 * LINE_SPAN + LINE_SPAN / 2

# ---------------- 玩家 ----------------
EMPTY = 0          # 空格
RED_PLAYER = 1     # 红方（玩家，位于下方）
BLACK_PLAYER = 2   # 黑方（电脑，位于上方）

# ---------------- 颜色（RGB 元组） ----------------
BG_COLOR = (200, 200, 200)
LINE_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 0, 0)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# 渲染辅助色
HIGHLIGHT_COLOR = (255, 215, 0)   # 选中棋子金色高亮
HINT_COLOR = (80, 160, 80)        # 可走位置提示
FONT_NAME = "kaiti"

# ---------------- 资源路径 ----------------
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "s2"

# 棋子类型标识
PIECE_KINDS = ("rook", "knight", "elephant", "mandarin", "king", "cannon", "pawn")

# 中文字名（用于界面提示）
PIECE_NAMES = {
    "rook": "车", "knight": "马", "elephant": "象", "mandarin": "士",
    "king": "将", "cannon": "炮", "pawn": "兵",
}


def piece_image_key(side: str, kind: str) -> str:
    """棋子图片键，如 r_rook / b_pawn。side: r=红 b=黑。"""
    return f"{side}_{kind}"


def load_piece_images():
    """加载全部棋子图片，返回 {image_key: pygame.Surface}。

    仅在需要渲染时调用（需要 pygame 环境）。
    """
    import pygame

    images = {}
    for side in ("r", "b"):
        for kind in PIECE_KINDS:
            key = piece_image_key(side, kind)
            path = ASSETS_DIR / f"{side}_{kind}.gif"
            images[key] = pygame.image.load(str(path))
    return images
