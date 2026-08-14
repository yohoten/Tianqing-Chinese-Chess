"""中国象棋棋子逻辑模块（不依赖 pygame，可单元测试）。

设计说明
--------
- 棋盘坐标：x ∈ [0, 8] 列，y ∈ [0, 9] 行；红方在下（y 大），黑方在上（y 小）。
- 局面用 Board 类表示：color[x][y] 存玩家（0/1/2），kind[x][y] 存棋子类型。
- 走法规则以模块级函数实现（rook_moves 等），棋子对象与 AI 共用同一套规则，
  避免规则重复、保证行为一致。
"""
from typing import List, Optional, Tuple

from .constants import (
    BOARD_COLS,
    BOARD_ROWS,
    EMPTY,
    RED_PLAYER,
    BLACK_PLAYER,
)

Pos = Tuple[int, int]           # (x, y)
Move = Tuple[int, int, int, int]  # (from_x, from_y, to_x, to_y)


def opponent(player: int) -> int:
    """返回对方玩家标识。"""
    return BLACK_PLAYER if player == RED_PLAYER else RED_PLAYER


def _in_board(x: int, y: int) -> bool:
    return 0 <= x < BOARD_COLS and 0 <= y < BOARD_ROWS


# ---------------------------------------------------------------------------
# 走法生成（每种棋子的规则函数）
# board 为 9x10 的颜色数组（color[x][y]）。
# 返回可达目标位置列表（不含“走后是否送将”校验，该校验由上层完成）。
# ---------------------------------------------------------------------------

def rook_moves(x: int, y: int, player: int, board) -> List[Pos]:
    """车：横竖直线移动，路径不能有子，可吃对方棋子。"""
    moves: List[Pos] = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        while _in_board(nx, ny):
            cell = board[nx][ny]
            if cell == EMPTY:
                moves.append((nx, ny))
            elif cell != player:
                moves.append((nx, ny))
                break
            else:
                break
            nx += dx
            ny += dy
    return moves


def cannon_moves(x: int, y: int, player: int, board) -> List[Pos]:
    """炮：平移时不能吃子且不能越子；吃子时必须且只能隔一个棋子（炮架）。"""
    moves: List[Pos] = []

    def scan(dx, dy):
        nx, ny = x + dx, y + dy
        screen = False  # 是否已越过一个炮架
        while _in_board(nx, ny):
            cell = board[nx][ny]
            if cell == EMPTY:
                if not screen:
                    moves.append((nx, ny))  # 平移只走空格
            else:
                if not screen:
                    screen = True           # 找到炮架
                else:
                    if cell != player:      # 越过炮架后第一个子可吃
                        moves.append((nx, ny))
                    break
            nx += dx
            ny += dy

    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        scan(dx, dy)
    return moves


def knight_moves(x: int, y: int, player: int, board) -> List[Pos]:
    """马：日字走法，蹩马腿。"""
    moves: List[Pos] = []
    for dx, dy in ((1, 2), (2, 1), (2, -1), (1, -2),
                   (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        tx, ty = x + dx, y + dy
        if not _in_board(tx, ty) or board[tx][ty] == player:
            continue
        # 蹩腿点：x 方向走 2 时腿在 (x+sign(dx), y)；y 方向走 2 时腿在 (x, y+sign(dy))
        if abs(dx) == 2:
            leg_x, leg_y = x + (1 if dx > 0 else -1), y
        else:
            leg_x, leg_y = x, y + (1 if dy > 0 else -1)
        if board[leg_x][leg_y] == EMPTY:
            moves.append((tx, ty))
    return moves


def elephant_moves(x: int, y: int, player: int, board) -> List[Pos]:
    """象：田字走法，不能过河，塞象眼。"""
    moves: List[Pos] = []
    for dx, dy in ((2, 2), (2, -2), (-2, 2), (-2, -2)):
        tx, ty = x + dx, y + dy
        if not _in_board(tx, ty) or board[tx][ty] == player:
            continue
        # 不能过河：红象 y>=5，黑象 y<=4
        if player == RED_PLAYER and ty < 5:
            continue
        if player == BLACK_PLAYER and ty > 4:
            continue
        eye_x, eye_y = x + (1 if dx > 0 else -1), y + (1 if dy > 0 else -1)
        if board[eye_x][eye_y] == EMPTY:
            moves.append((tx, ty))
    return moves


def mandarin_moves(x: int, y: int, player: int, board) -> List[Pos]:
    """士：九宫内斜走一步。红方九宫 y∈[7,9]，黑方 y∈[0,2]。"""
    moves: List[Pos] = []
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        tx, ty = x + dx, y + dy
        if not _in_board(tx, ty) or board[tx][ty] == player:
            continue
        if not (3 <= tx <= 5):
            continue
        if player == RED_PLAYER:
            if not (7 <= ty <= 9):
                continue
        else:
            if not (0 <= ty <= 2):
                continue
        moves.append((tx, ty))
    return moves


def king_moves(x: int, y: int, player: int, board) -> List[Pos]:
    """将/帅：九宫内直走一步。飞将规则由 is_in_check 统一处理。"""
    moves: List[Pos] = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        tx, ty = x + dx, y + dy
        if not _in_board(tx, ty) or board[tx][ty] == player:
            continue
        if not (3 <= tx <= 5):
            continue
        if player == RED_PLAYER:
            if not (7 <= ty <= 9):
                continue
        else:
            if not (0 <= ty <= 2):
                continue
        moves.append((tx, ty))
    return moves


def pawn_moves(x: int, y: int, player: int, board) -> List[Pos]:
    """兵/卒：未过河只能前进，过河后可横走，永不后退。"""
    moves: List[Pos] = []
    if player == RED_PLAYER:
        forward_y = y - 1
        crossed = y <= 4   # 红兵过河后位于对方半场 y<=4
    else:
        forward_y = y + 1
        crossed = y >= 5   # 黑卒过河后位于对方半场 y>=5

    if _in_board(x, forward_y) and board[x][forward_y] != player:
        moves.append((x, forward_y))
    if crossed:
        for nx in (x - 1, x + 1):
            if _in_board(nx, y) and board[nx][y] != player:
                moves.append((nx, y))
    return moves


PIECE_MOVE_FUNCS = {
    "rook": rook_moves,
    "cannon": cannon_moves,
    "knight": knight_moves,
    "elephant": elephant_moves,
    "mandarin": mandarin_moves,
    "king": king_moves,
    "pawn": pawn_moves,
}


# ---------------------------------------------------------------------------
# 局面 Board
# ---------------------------------------------------------------------------

class Board:
    """9x10 棋盘局面：color[x][y] 与 kind[x][y] 双矩阵。"""

    def __init__(self, pieces: Optional[List["Pieces"]] = None):
        self.color = [[EMPTY] * BOARD_ROWS for _ in range(BOARD_COLS)]
        self.kind = [[""] * BOARD_ROWS for _ in range(BOARD_COLS)]
        if pieces:
            for p in pieces:
                self.place(p.player, p.kind, p.x, p.y)

    def place(self, player: int, kind: str, x: int, y: int) -> None:
        self.color[x][y] = player
        self.kind[x][y] = kind

    def remove(self, x: int, y: int) -> None:
        self.color[x][y] = EMPTY
        self.kind[x][y] = ""

    def move(self, fx: int, fy: int, tx: int, ty: int):
        """执行走子（直接覆盖，用于游戏层）。

        返回被吃子的 (color, kind)，供搜索层 undo 使用。
        """
        cap_color = self.color[tx][ty]
        cap_kind = self.kind[tx][ty]
        self.color[tx][ty] = self.color[fx][fy]
        self.kind[tx][ty] = self.kind[fx][fy]
        self.color[fx][fy] = EMPTY
        self.kind[fx][fy] = ""
        return cap_color, cap_kind

    def unmove(self, fx: int, fy: int, tx: int, ty: int,
               cap_color: int, cap_kind: str) -> None:
        """撤销 move()，恢复被吃子（搜索层用，避免反复复制棋盘）。"""
        self.color[fx][fy] = self.color[tx][ty]
        self.kind[fx][fy] = self.kind[tx][ty]
        self.color[tx][ty] = cap_color
        self.kind[tx][ty] = cap_kind

    def copy(self) -> "Board":
        new = Board()
        new.color = [row[:] for row in self.color]
        new.kind = [row[:] for row in self.kind]
        return new

    def find_king(self, player: int) -> Optional[Pos]:
        for x in range(BOARD_COLS):
            for y in range(BOARD_ROWS):
                if self.color[x][y] == player and self.kind[x][y] == "king":
                    return x, y
        return None

    def to_pieces(self) -> List["Pieces"]:
        """转换为棋子对象列表（供渲染 / 回写游戏层使用）。"""
        pieces = []
        factory = {
            "rook": Rook, "cannon": Cannon, "knight": Knight,
            "elephant": Elephant, "mandarin": Mandarin,
            "king": King, "pawn": Pawn,
        }
        for x in range(BOARD_COLS):
            for y in range(BOARD_ROWS):
                kind = self.kind[x][y]
                if kind:
                    pieces.append(factory[kind](self.color[x][y], x, y))
        return pieces


# ---------------------------------------------------------------------------
# 棋子对象
# ---------------------------------------------------------------------------

class Pieces:
    """棋子基类：坐标 + 类型，走法委托给模块级规则函数。"""

    kind = "piece"
    name = "子"
    value = 0.0

    def __init__(self, player: int, x: int, y: int):
        self.player = player
        self.x = x
        self.y = y

    @property
    def image_key(self) -> str:
        side = "r" if self.player == RED_PLAYER else "b"
        return f"{side}_{self.kind}"

    def legal_moves(self, board) -> List[Pos]:
        """候选走法（不含不送将校验）。"""
        return PIECE_MOVE_FUNCS[self.kind](self.x, self.y, self.player, board)

    def canmove(self, board, to_x: int, to_y: int) -> bool:
        return (to_x, to_y) in self.legal_moves(board)

    def evaluate(self) -> float:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.player}, {self.x}, {self.y})"


class Rook(Pieces):
    kind = "rook"
    name = "车"
    value = 9.0


class Cannon(Pieces):
    kind = "cannon"
    name = "炮"
    value = 4.5


class Knight(Pieces):
    kind = "knight"
    name = "马"
    value = 4.0


class Elephant(Pieces):
    kind = "elephant"
    name = "象"
    value = 2.0


class Mandarin(Pieces):
    kind = "mandarin"
    name = "士"
    value = 2.0


class King(Pieces):
    kind = "king"
    name = "将"
    value = 10000.0


class Pawn(Pieces):
    kind = "pawn"
    name = "兵"
    value = 1.0


# ---------------------------------------------------------------------------
# 局面工具：将军检测、合法走法（含不送将校验）
# ---------------------------------------------------------------------------

def list_to_board(pieces_list: List[Pieces]) -> Board:
    """棋子对象列表 -> Board。"""
    return Board(pieces_list)


def is_in_check(board: Board, player: int) -> bool:
    """player 的将是否正被攻击（含“将帅对脸”规则）。

    快速版：从将的位置反向检查潜在攻击者，避免全盘扫描。
    """
    king_pos = board.find_king(player)
    if king_pos is None:
        return True  # 无将视为被将（游戏结束由上层判断）
    kx, ky = king_pos
    foe = opponent(player)
    color = board.color
    kind = board.kind

    # 1) 直线方向：车 / 炮 / 飞将
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = kx + dx, ky + dy
        first_met = False
        while _in_board(x, y):
            cell = color[x][y]
            if cell != EMPTY:
                if not first_met:
                    first_met = True
                    if cell == foe:
                        k = kind[x][y]
                        if k == "rook" or k == "king":
                            return True   # 车将军 / 飞将
                    # 第一个子是炮架（无论敌我），继续找第二个
                else:
                    if cell == foe and kind[x][y] == "cannon":
                        return True       # 隔一子炮将军
                    break                 # 第二个子不是敌炮，停止
            x += dx
            y += dy

    # 2) 马：8 个日字位，检查蹩腿
    for dx, dy in ((1, 2), (2, 1), (2, -1), (1, -2),
                   (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        tx, ty = kx + dx, ky + dy
        if not _in_board(tx, ty) or color[tx][ty] != foe or kind[tx][ty] != "knight":
            continue
        if abs(dx) == 2:
            leg_x, leg_y = kx + (1 if dx > 0 else -1), ky
        else:
            leg_x, leg_y = kx, ky + (1 if dy > 0 else -1)
        if color[leg_x][leg_y] == EMPTY:
            return True

    # 3) 兵 / 卒：王邻近的敌兵
    if foe == RED_PLAYER:
        # 红兵在正下方（前进攻击），或在同一行且已过河（横走攻击）
        for x, y in ((kx, ky + 1), (kx + 1, ky), (kx - 1, ky)):
            if _in_board(x, y) and color[x][y] == foe and kind[x][y] == "pawn":
                if y == ky + 1 or ky <= 4:
                    return True
    else:
        # 黑卒在正上方（前进攻击），或在同一行且已过河（横走攻击）
        for x, y in ((kx, ky - 1), (kx + 1, ky), (kx - 1, ky)):
            if _in_board(x, y) and color[x][y] == foe and kind[x][y] == "pawn":
                if y == ky - 1 or ky >= 5:
                    return True

    return False


def legal_moves_with_check(board: Board, player: int, fx: int, fy: int) -> List[Pos]:
    """(fx, fy) 处棋子的全部合法走法（过滤掉走后自己被将军的走法）。

    用 make/unmake 代替复制棋盘，搜索时显著减少内存分配。
    """
    kind = board.kind[fx][fy]
    if not kind:
        return []
    results: List[Pos] = []
    for tx, ty in PIECE_MOVE_FUNCS[kind](fx, fy, player, board.color):
        cap_color, cap_kind = board.move(fx, fy, tx, ty)
        if not is_in_check(board, player):
            results.append((tx, ty))
        board.unmove(fx, fy, tx, ty, cap_color, cap_kind)
    return results


def all_legal_moves(board: Board, player: int) -> List[Move]:
    """player 的全部合法走法。"""
    moves: List[Move] = []
    for x in range(BOARD_COLS):
        for y in range(BOARD_ROWS):
            if board.color[x][y] == player:
                for tx, ty in legal_moves_with_check(board, player, x, y):
                    moves.append((x, y, tx, ty))
    return moves
