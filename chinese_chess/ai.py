"""电脑 AI：局面评估 + Alpha-Beta 剪枝搜索（不依赖 pygame，可单元测试）。

- 搜索使用 negamax + Alpha-Beta 剪枝，默认深度 3（可配置）。
- 走法生成基于 pieces.all_legal_moves（已过滤“走后送将”）。
- 局面评估：子力价值 + 兵过河加成 + 位置微调 + 被将军罚分。
- 游戏结束：将死（无合法走法且被将军）判负，困毙（无合法走法未被将军）判和。
"""
import time
from typing import List, Optional

from .constants import RED_PLAYER, BLACK_PLAYER
from .pieces import (
    Board,
    Move,
    EMPTY,
    all_legal_moves,
    is_in_check,
    opponent,
)

INF = float("inf")
MATE_SCORE = 1_000_000   # 将死分数

# 默认思考时间预算（秒）：迭代加深，到点即停，保证响应
DEFAULT_TIME_BUDGET = 2.0

# 搜索时间控制（全局，单线程搜索使用）
_search_budget: Optional[float] = None
_search_start: float = 0.0
_search_nodes = 0


class _SearchTimeOut(Exception):
    """搜索超过时间预算，中止当前层并返回已有最佳走法。"""


def _set_search_budget(max_time: float):
    global _search_budget, _search_start, _search_nodes
    _search_budget = max_time
    _search_start = time.time()
    _search_nodes = 0
    _history_table.clear()   # 每次搜索（迭代加深外层）重置历史启发
    _t_table.clear()         # 置换表按“一步搜索”粒度复用


def _check_search_time():
    global _search_nodes
    _search_nodes += 1
    if (_search_nodes & 1023) == 0:
        # 主动让出 GIL，保证渲染线程在 AI 思考期间仍能刷新界面
        time.sleep(0)
        if _search_budget is not None and time.time() - _search_start > _search_budget:
            raise _SearchTimeOut()

# 子力价值（以“车”为 9 的常见设定）
PIECE_VALUE = {
    "rook": 9.0,
    "cannon": 4.5,
    "knight": 4.0,
    "elephant": 2.0,
    "mandarin": 2.0,
    "pawn": 1.0,
    "king": 10000.0,
}

# 位置价值表（9 列 x 10 行，红方视角，红方在下方 y=9）
# 简化版：兵过河加成；马/炮中心区域微调
PAWN_POSITION = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0.3, 0.4, 0.5, 0.6, 0.7, 0.6, 0.5, 0.4, 0.3],   # 刚过河
    [0.6, 0.8, 0.9, 1.0, 1.1, 1.0, 0.9, 0.8, 0.6],   # 深入敌阵
    [0.6, 0.8, 0.9, 1.0, 1.1, 1.0, 0.9, 0.8, 0.6],
    [0.3, 0.4, 0.5, 0.6, 0.7, 0.6, 0.5, 0.4, 0.3],   # 刚过河
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]

CENTER_POSITION = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0],
    [0, 0.2, 0.3, 0.4, 0.4, 0.4, 0.3, 0.2, 0],
    [0, 0.2, 0.4, 0.5, 0.5, 0.5, 0.4, 0.2, 0],
    [0, 0.2, 0.4, 0.5, 0.5, 0.5, 0.4, 0.2, 0],
    [0, 0.2, 0.4, 0.5, 0.5, 0.5, 0.4, 0.2, 0],
    [0, 0.2, 0.4, 0.5, 0.5, 0.5, 0.4, 0.2, 0],
    [0, 0.2, 0.3, 0.4, 0.4, 0.4, 0.3, 0.2, 0],
    [0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def _position_bonus(kind: str, x: int, y: int, player: int) -> float:
    """位置加成。PAWN_POSITION / CENTER_POSITION 为红方视角，黑方上下镜像。"""
    if kind == "pawn":
        row = y if player == RED_PLAYER else 9 - y
        return PAWN_POSITION[row][x]
    if kind in ("knight", "cannon"):
        row = y if player == RED_PLAYER else 9 - y
        return CENTER_POSITION[row][x]
    return 0.0


def evaluate(board: Board, player: int) -> float:
    """从 player 视角的静态局面评估（正数利于 player）。"""
    score = 0.0
    for x in range(9):
        for y in range(10):
            cell = board.color[x][y]
            if cell == EMPTY:
                continue
            kind = board.kind[x][y]
            base = PIECE_VALUE[kind] + _position_bonus(kind, x, y, cell)
            if cell == player:
                score += base
            else:
                score -= base

    # 被将军罚分（促使防守与避免送将）
    if is_in_check(board, player):
        score -= 40
    if is_in_check(board, opponent(player)):
        score += 40
    return score


def _move_order(move: Move, board: Board) -> float:
    """吃子走法的 MVV-LVA 排序分（吃大子优先；用小兵吃大子更好）。"""
    fx, fy, tx, ty = move
    victim = board.color[tx][ty]
    if victim != EMPTY:
        victim_kind = board.kind[tx][ty]
        attacker_kind = board.kind[fx][fy]
        return PIECE_VALUE.get(victim_kind, 0) * 10 - PIECE_VALUE.get(attacker_kind, 0) * 0.1
    return 0.0


# 历史启发表：记录剪枝走法的“业绩”，用于后续走法排序
_history_table = {}

# 置换表（Transposition Table）：{zhash: (depth, flag, score, best_move)}
# flag: TT_EXACT（精确值）| TT_LOWER（>= score）| TT_UPPER（<= score）
TT_EXACT, TT_LOWER, TT_UPPER = 0, 1, 2
_t_table = {}


def _order_moves(moves, board, tt_move=None):
    """走法排序：置换表最佳走法优先，其次吃子（MVV-LVA），再按历史启发。

    相比对全部走法 sorted()，这里只对数量较少的吃子走法排序，
    普通走法用 dict 查询历史分排序，整体开销更小。
    """
    if tt_move is not None:
        rest = [m for m in moves if m != tt_move]
        return [tt_move] + _order_moves(rest, board)
    caps = []
    quiets = []
    for m in moves:
        if board.color[m[2]][m[3]] != EMPTY:
            caps.append(m)
        else:
            quiets.append(m)
    caps.sort(key=lambda m: _move_order(m, board), reverse=True)
    quiets.sort(key=lambda m: _history_table.get(m, 0), reverse=True)
    return caps + quiets


def _record_history(move: Move, depth: int) -> None:
    """剪枝命中时给该走法记功，提升后续排序优先级。"""
    _history_table[move] = _history_table.get(move, 0) + depth * depth


def negamax(board: Board, depth: int, alpha: float, beta: float, player: int) -> float:
    """negamax + Alpha-Beta 剪枝 + 置换表，从 player 视角返回局面价值。

    使用 make/unmake 走子，不复制棋盘。
    """
    moves = all_legal_moves(board, player)

    if not moves:
        # 无合法走法：被将军=将死，否则=困毙
        if is_in_check(board, player):
            return -MATE_SCORE - depth   # 越快被杀越差
        return 0.0                       # 困毙，和棋

    if depth == 0:
        return evaluate(board, player)

    # 置换表探测
    key = board.zhash
    entry = _t_table.get(key)
    tt_move = None
    if entry is not None and entry[0] >= depth:
        e_depth, e_flag, e_score, e_move = entry
        if e_flag == TT_EXACT:
            return e_score
        if e_flag == TT_LOWER and e_score >= beta:
            return e_score
        if e_flag == TT_UPPER and e_score <= alpha:
            return e_score
        tt_move = e_move

    best = -INF
    best_move = None
    orig_alpha = alpha
    ordered = _order_moves(moves, board, tt_move)
    for fx, fy, tx, ty in ordered:
        cap_color, cap_kind = board.move(fx, fy, tx, ty)
        value = -negamax(board, depth - 1, -beta, -alpha, opponent(player))
        board.unmove(fx, fy, tx, ty, cap_color, cap_kind)
        if value > best:
            best = value
            best_move = (fx, fy, tx, ty)
        if best > alpha:
            alpha = best
        if alpha >= beta:
            _record_history((fx, fy, tx, ty), depth)
            break
        _check_search_time()

    # 存储置换表（跳过将死距离相关的强制分数，避免 mate-distance 干扰）
    if abs(best) < MATE_SCORE - 100:
        if best > orig_alpha and best < beta:
            flag = TT_EXACT
        elif best >= beta:
            flag = TT_LOWER
        else:
            flag = TT_UPPER
        _t_table[key] = (depth, flag, best, best_move)
    return best


def _best_at_depth(board: Board, player: int, depth: int) -> Optional[Move]:
    """在指定深度返回最佳走法（供迭代加深使用）。"""
    moves = all_legal_moves(board, player)
    if not moves:
        return None
    alpha, beta = -INF, INF
    best_move: Optional[Move] = None
    best_score = -INF

    entry = _t_table.get(board.zhash)
    tt_move = entry[3] if entry is not None else None
    ordered = _order_moves(moves, board, tt_move)
    for fx, fy, tx, ty in ordered:
        cap_color, cap_kind = board.move(fx, fy, tx, ty)
        value = -negamax(board, depth - 1, -beta, -alpha, opponent(player))
        board.unmove(fx, fy, tx, ty, cap_color, cap_kind)
        if value > best_score:
            best_score = value
            best_move = (fx, fy, tx, ty)
        if best_score > alpha:
            alpha = best_score
        _check_search_time()
    return best_move


def get_best_move(pieces_list, depth: int = 4, max_time: float = DEFAULT_TIME_BUDGET,
                  player: int = BLACK_PLAYER) -> Optional[Move]:
    """给定局面（棋子对象列表），返回 AI 的最佳走法 (fx, fy, tx, ty)。

    采用迭代加深：从浅层逐步加深搜索，用满时间预算即返回当前最佳，
    既能保证响应速度，又能让中后期用上更深搜索。

    pieces_list: Pieces 对象列表（游戏层持有）。
    depth: 最大搜索深度。
    max_time: 思考时间预算（秒）。
    player: AI 执子方，默认黑方。
    """
    board = Board(pieces_list)
    moves = all_legal_moves(board, player)
    if not moves:
        return None

    best: Move = moves[0]
    _set_search_budget(max_time)
    start = time.time()
    try:
        for d in range(1, depth + 1):
            move = _best_at_depth(board, player, d)
            if move is not None:
                best = move
            # 一层已完成；剩余时间不足以再做一层则提前结束
            if time.time() - start + 0.1 > max_time:
                break
    except _SearchTimeOut:
        pass   # 超时：使用已完成的最近一层结果
    finally:
        _search_budget = None
    return best


def game_result(board: Board, player_to_move: int) -> Optional[int]:
    """判断当前局面是否终局。

    返回 None（对局继续）| 胜方玩家（将死，对方无棋可走）| 0（困毙和棋）。
    """
    moves = all_legal_moves(board, player_to_move)
    if moves:
        return None
    if is_in_check(board, player_to_move):
        return opponent(player_to_move)   # 将死，对方获胜
    return 0                              # 困毙，和棋
