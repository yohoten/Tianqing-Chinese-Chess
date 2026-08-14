"""全局常量与资源管理。

逻辑模块（pieces/ai）不依赖 pygame，图片只在渲染模块中按需加载。
"""
from pathlib import Path

# ---------------- 屏幕与棋盘 ----------------
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 720

START_X = 30
START_Y = 30
LINE_SPAN = 60

BOARD_COLS = 9   # 棋盘列数（x 方向 0..8）
BOARD_ROWS = 10  # 棋盘行数（y 方向 0..9，红方在下）

# 棋盘有效区域（用于鼠标点击判定）
BOARD_MIN_X = START_X - LINE_SPAN / 2
BOARD_MAX_X = START_X + 8 * LINE_SPAN + LINE_SPAN / 2
BOARD_MIN_Y = START_Y - LINE_SPAN / 2
BOARD_MAX_Y = START_Y + 9 * LINE_SPAN + LINE_SPAN / 2

# ---------------- 右侧信息栏（按钮 / 状态 / 分析面板分区） ----------------
# 窗口 900x720：棋盘占 x≈0~540 / y≈0~600，右侧信息栏 x≈560~880
INFO_X = 560          # 信息栏左边界
INFO_WIDTH = 320      # 信息栏宽度
INFO_Y = 40           # 信息栏顶部

# 按钮（信息栏内居中）
BUTTON_WIDTH = 150
BUTTON_HEIGHT = 50
BUTTON_LEFT = INFO_X + (INFO_WIDTH - BUTTON_WIDTH) // 2
BTN_UNDO_Y = 230
BTN_RESTART_Y = 300

# 分析面板（位于按钮下方，避免与按钮重叠）
ANALYSIS_X = INFO_X
ANALYSIS_Y = 390
ANALYSIS_WIDTH = INFO_WIDTH
ANALYSIS_STEP = 24

# 棋子渲染
PIECE_SIZE = 52       # 棋子图片统一缩放到该尺寸（格距 60 内留边）

# ---------------- 玩家 ----------------
EMPTY = 0          # 空格
RED_PLAYER = 1     # 红方（玩家，位于下方）
BLACK_PLAYER = 2   # 黑方（电脑，位于上方）

# ---------------- 颜色（RGB 元组） ----------------
BG_COLOR = (222, 200, 170)        # 窗口背景（暖米色，衬托木纹棋盘）
LINE_COLOR = (101, 67, 33)        # 网格线（深棕，替代纯黑更柔和）
TEXT_COLOR = (255, 0, 0)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# 渲染辅助色
HIGHLIGHT_COLOR = (255, 215, 0)   # 选中棋子金色高亮
HINT_COLOR = (80, 160, 80)        # 可走位置提示
LAST_MOVE_COLOR = (232, 152, 40)  # 最近一步标记（琥珀）
CHECK_RING_COLOR = (220, 30, 30)  # 将军红环 / 警报
# 中文字体统一由 fonts.get_font() 管理（候选字体名 + 文件兜底）

# ---------------- 木纹棋盘色系 ----------------
WOOD_BASE = (218, 180, 132)       # 棋盘底板木色
WOOD_GRAIN = (200, 162, 116)      # 木纹条纹
WOOD_RIVER = (120, 60, 30)        # 河界文字（暖棕）
BOARD_FRAME = (90, 60, 30)        # 棋盘外框

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
    """加载全部棋子图片并统一缩放到 PIECE_SIZE。

    返回 {image_key: pygame.Surface}；仅在需要渲染时调用（需要 pygame 环境）。
    """
    import pygame

    images = {}
    for side in ("r", "b"):
        for kind in PIECE_KINDS:
            key = piece_image_key(side, kind)
            path = ASSETS_DIR / f"{side}_{kind}.gif"
            img = pygame.image.load(str(path))
            # GIF 可能是 8-bit 索引色，先转 32-bit 以便 smoothscale
            try:
                if img.get_alpha() is not None:
                    img = img.convert_alpha()
                else:
                    img = img.convert()
            except pygame.error:
                pass
            # 等比缩放适配格子；smoothscale 不支持时降级 scale
            w, h = img.get_size()
            scale = PIECE_SIZE / max(w, h)
            nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
            try:
                img = pygame.transform.smoothscale(img, (nw, nh))
            except pygame.error:
                img = pygame.transform.scale(img, (nw, nh))
            images[key] = img
    return images
