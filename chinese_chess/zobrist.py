"""Zobrist 哈希：为棋盘局面生成 64 位键，供 AI 置换表使用。

每个 (x, y, 玩家, 棋子类型) 分配一个固定随机数；局面哈希 = 所有棋子随机数异或。
走子时增量更新（Board.move/unmove 维护 Board.zhash），O(1)。
固定种子保证跨进程、跨运行结果一致（可复现）。
"""
import random

from .constants import BOARD_COLS, BOARD_ROWS, RED_PLAYER, BLACK_PLAYER

PIECE_KINDS = ("rook", "knight", "elephant", "mandarin", "king", "cannon", "pawn")
_KIND_INDEX = {k: i for i, k in enumerate(PIECE_KINDS)}

# table[x][y][player_idx(0=红,1=黑)][kind_idx]
_table = None


def _build_table():
    rng = random.Random(0xC0FFEE)
    return [
        [
            [
                [rng.getrandbits(64) for _ in PIECE_KINDS]
                for _ in (0, 1)   # 红/黑
            ]
            for _ in range(BOARD_ROWS)
        ]
        for _ in range(BOARD_COLS)
    ]


def zobrist_key(x: int, y: int, player: int, kind: str) -> int:
    """指定格子的哈希值；空格或未知类型返回 0。"""
    global _table
    if _table is None:
        _table = _build_table()
    if player not in (RED_PLAYER, BLACK_PLAYER):
        return 0
    idx = _KIND_INDEX.get(kind)
    if idx is None:
        return 0
    p = 0 if player == RED_PLAYER else 1
    return _table[x][y][p][idx]
