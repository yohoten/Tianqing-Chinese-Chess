"""chessai-python 桥接层。

功能
----
- 自研 Board ↔ chessai board_array 双向转换
- 生成 FEN（复用 chessai 的转换逻辑）
- 用 chessai SimpleEngine 做规则交叉校验（走法 / 将军 / 将死 / 飞将）

坐标约定
--------
- 本项目：Board.color[x][y]，x=列(0-8)，y=行(0-9)，红方在下
- chessai：board_array[row][col]，row=行(0-9)，col=列(0-8)，棋子串如 "rk"/"bn"

容错
----
所有函数在 chessai 未安装或异常时返回 None / False，绝不影响主游戏运行。
"""
from typing import List, Optional

from .constants import RED_PLAYER, BLACK_PLAYER
from .pieces import Board

# 本项目棋子类型 -> chessai 单字母码（r/n/b/a/k/c/p）
CHESSAI_TYPE_CODE = {
    "rook": "r",
    "knight": "n",
    "elephant": "b",    # bishop（象）
    "mandarin": "a",    # advisor（士）
    "king": "k",
    "cannon": "c",
    "pawn": "p",
}
OUR_KIND_BY_CODE = {v: k for k, v in CHESSAI_TYPE_CODE.items()}


def to_chessai_board(board: Board) -> List[List[str]]:
    """自研 Board -> chessai board_array（10 行 x 9 列，行主序，棋子串 rk/bn...）。"""
    arr = [[""] * 9 for _ in range(10)]
    for x in range(9):
        for y in range(10):
            cell = board.color[x][y]
            if cell:
                side = "r" if cell == RED_PLAYER else "b"
                arr[y][x] = side + CHESSAI_TYPE_CODE.get(board.kind[x][y], "p")
    return arr


def from_chessai_board(board_array: List[List[str]]) -> Optional[Board]:
    """chessai board_array -> 自研 Board；输入非法时返回 None。"""
    try:
        board = Board()
        for row in range(10):
            for col in range(9):
                piece = board_array[row][col]
                if not piece:
                    continue
                side = piece[0]
                kind = OUR_KIND_BY_CODE.get(piece[1])
                if kind is None or side not in ("r", "b"):
                    return None
                player = RED_PLAYER if side == "r" else BLACK_PLAYER
                board.place(player, kind, col, row)
        return board
    except Exception:
        return None


def fen_from_board(board: Board, next_player: int = RED_PLAYER) -> str:
    """生成 FEN（复用 chessai 的转换；失败返回空串）。"""
    try:
        from chessai.game.chess_engine import ChessEngine
        player_str = "r" if next_player == RED_PLAYER else "b"
        return ChessEngine.board_array_to_fen(to_chessai_board(board), player_str)
    except Exception:
        return ""


def _make_simple_engine(board: Board, player: int):
    """创建 chessai SimpleEngine（未安装/异常返回 None）。"""
    try:
        from chessai.game.simple_engine.simple_engine import SimpleEngine
        side = "r" if player == RED_PLAYER else "b"
        return SimpleEngine(to_chessai_board(board), side)
    except Exception:
        return None


def chessai_validate_move(board: Board, player: int, fx: int, fy: int,
                          tx: int, ty: int) -> Optional[bool]:
    """用 chessai 校验一步走法是否合法。

    返回 True/False；chessai 不可用时返回 None。
    """
    engine = _make_simple_engine(board, player)
    if engine is None:
        return None
    try:
        # chessai 坐标为 (row, col) = (y, x)
        return bool(engine.check_move((fy, fx), (ty, tx)))
    except Exception:
        return None


def chessai_status(board: Board, player: int) -> Optional[dict]:
    """chessai 局面状态：将军 / 将死 / 飞将。

    返回 {"in_check": bool, "checkmate": bool, "kings_face": bool}；
    chessai 不可用时返回 None。
    """
    engine = _make_simple_engine(board, player)
    if engine is None:
        return None
    try:
        side = "r" if player == RED_PLAYER else "b"
        return {
            "in_check": bool(engine.is_in_check(side)),
            "checkmate": bool(engine.is_checkmate()),
            "kings_face": bool(engine.king_face_each_other()),
        }
    except Exception:
        return None
