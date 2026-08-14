"""中文字体管理。

pygame 的 SysFont/match_font 依赖系统字体枚举，在无头环境或字体配置
不完整的系统上可能失败并导致中文显示为方框。本模块按顺序尝试：

1. 常见中文字体名（match_font，需系统枚举正常）
2. 常见中文字体文件路径（直接加载，不依赖枚举，最可靠）
3. pygame 默认字体（最终兜底）

所有字体对象按字号缓存，避免每帧重复创建。
"""
import pygame

# 候选系统字体名（按优先级）
FONT_NAME_CANDIDATES = (
    "kaiti", "KaiTi", "simkai", "STKaiti", "STKAITI",
    "microsoftyahei", "Microsoft YaHei", "msyh",
    "simhei", "SimHei", "simsun", "SimSun",
    "dengxian", "notosanscjksc", "wqyzenhei",
)

# 常见字体文件路径兜底（Windows / Linux）
FONT_FILE_FALLBACKS = (
    "C:/Windows/Fonts/simkai.ttf",     # 楷体（中国象棋风格）
    "C:/Windows/Fonts/STKAITI.TTF",    # 华文楷体
    "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",     # 黑体
    "C:/Windows/Fonts/simsun.ttc",     # 宋体
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)

_cache = {}


def get_font(size: int = 18):
    """返回可渲染中文的字体对象（带缓存）。"""
    if size not in _cache:
        _cache[size] = _make_font(size)
    return _cache[size]


def _make_font(size: int):
    pygame.font.init()

    # 1) 系统字体名（真实窗口环境下通常可命中）
    for name in FONT_NAME_CANDIDATES:
        try:
            path = pygame.font.match_font(name)
            if path:
                return pygame.font.Font(path, size)
        except Exception:
            continue

    # 2) 字体文件路径兜底
    for path in FONT_FILE_FALLBACKS:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            continue

    # 3) 最终兜底（可能无法显示中文，但保证不崩溃）
    return pygame.font.Font(None, size)
