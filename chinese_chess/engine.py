"""引擎接口：AI 走子计算抽象。

game.py 只依赖 Engine 协议，不直接调用 ai.get_best_move。
后续接外部 UCI 引擎 / 换更强引擎时，新增实现类并在 game.py 替换即可，
游戏逻辑无需改动。
"""
from typing import Optional, Protocol

from .constants import BLACK_PLAYER
from .pieces import Move
from .ai import get_best_move


class Engine(Protocol):
    """引擎协议：给定局面返回最佳走法 (fx, fy, tx, ty)。"""

    def get_best_move(self, pieces_list, max_time: float,
                      player: int) -> Optional[Move]:
        ...


class AlphaBetaEngine:
    """自研 Alpha-Beta 引擎（negamax + 迭代加深 + 时间预算）。"""

    name = "AlphaBeta"

    def __init__(self, depth: int = 4):
        self.depth = depth

    def get_best_move(self, pieces_list, max_time: float = 2.0,
                      player: int = BLACK_PLAYER) -> Optional[Move]:
        return get_best_move(
            pieces_list, depth=self.depth, max_time=max_time, player=player)
