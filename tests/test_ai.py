"""AI 与终局判定单元测试（不依赖 pygame）。"""
import unittest

from chinese_chess.constants import RED_PLAYER, BLACK_PLAYER
from chinese_chess.pieces import (
    Board,
    Rook,
    Knight,
    King,
    Pawn,
    all_legal_moves,
    is_in_check,
    legal_moves_with_check,
)
from chinese_chess.ai import get_best_move, game_result, evaluate


class TestGameResult(unittest.TestCase):
    def test_checkmate(self):
        # 红王 (4,9) 被三车包围（列 3/4/5 全部被控制），无路可走 -> 将死
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(BLACK_PLAYER, "rook", 3, 0)
        board.place(BLACK_PLAYER, "rook", 4, 0)
        board.place(BLACK_PLAYER, "rook", 5, 0)
        self.assertTrue(is_in_check(board, RED_PLAYER))
        self.assertEqual(all_legal_moves(board, RED_PLAYER), [])
        self.assertEqual(game_result(board, RED_PLAYER), BLACK_PLAYER)

    def test_stalemate(self):
        # 红王不被将军，但三个逃点全部被控制 -> 困毙和棋
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(BLACK_PLAYER, "rook", 3, 0)   # 控制 (3,9)
        board.place(BLACK_PLAYER, "rook", 5, 0)   # 控制 (5,9)
        board.place(BLACK_PLAYER, "knight", 2, 7) # 控制 (4,8)
        self.assertFalse(is_in_check(board, RED_PLAYER))
        self.assertEqual(all_legal_moves(board, RED_PLAYER), [])
        self.assertEqual(game_result(board, RED_PLAYER), 0)

    def test_game_continues(self):
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(BLACK_PLAYER, "king", 4, 0)
        self.assertIsNone(game_result(board, RED_PLAYER))


class TestAi(unittest.TestCase):
    def _board(self):
        # 双王放在不同列，避免“飞将”规则干扰吃子测试
        board = Board()
        board.place(BLACK_PLAYER, "king", 3, 0)
        board.place(RED_PLAYER, "king", 4, 9)
        return board

    def test_ai_captures_undefended_piece(self):
        # 黑马可吃红方无保护的车
        board = self._board()
        board.place(BLACK_PLAYER, "knight", 0, 1)
        board.place(RED_PLAYER, "rook", 2, 2)
        move = get_best_move(board.to_pieces(), depth=2, player=BLACK_PLAYER)
        self.assertEqual(move, (0, 1, 2, 2))

    def test_ai_prefers_best_capture(self):
        # 黑马可吃红车（被红车保护，吃后被反吃仍净赚）或吃无保护兵，AI 应选吃车
        board = self._board()
        board.place(BLACK_PLAYER, "knight", 3, 4)
        board.place(RED_PLAYER, "rook", 2, 2)    # 被红车 (1,2) 保护
        board.place(RED_PLAYER, "rook", 1, 2)
        board.place(RED_PLAYER, "pawn", 5, 5)    # 无保护兵
        move = get_best_move(board.to_pieces(), depth=2, player=BLACK_PLAYER)
        self.assertEqual(move, (3, 4, 2, 2))

    def test_ai_avoids_suicide_move(self):
        # 黑马 (4,2) 是红车 (4,5) 与黑王 (4,0) 之间的唯一挡子；
        # 黑马若跳开即“送将”（黑王被将军），AI 只能走王
        board = Board()
        board.place(BLACK_PLAYER, "king", 4, 0)
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(RED_PLAYER, "rook", 4, 5)
        board.place(BLACK_PLAYER, "knight", 4, 2)
        self.assertEqual(legal_moves_with_check(board, BLACK_PLAYER, 4, 2), [])
        move = get_best_move(board.to_pieces(), depth=2, player=BLACK_PLAYER)
        self.assertIsNotNone(move)
        fx, fy, tx, ty = move
        # AI 不能走送将的马，只能走王
        self.assertEqual((fx, fy), (4, 0))
        self.assertIn((tx, ty), [(3, 0), (5, 0), (4, 1)])

    def test_ai_check_king(self):
        # 黑车已经将军红王，AI 应直接吃王获胜
        board = self._board()
        board.place(BLACK_PLAYER, "rook", 4, 1)
        board.place(RED_PLAYER, "rook", 0, 9)
        move = get_best_move(board.to_pieces(), depth=2, player=BLACK_PLAYER)
        self.assertEqual(move, (4, 1, 4, 9))


class TestEvaluate(unittest.TestCase):
    def test_material_advantage(self):
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(BLACK_PLAYER, "king", 4, 0)
        board.place(RED_PLAYER, "rook", 0, 5)   # 红方多一车
        red_view = evaluate(board, RED_PLAYER)
        black_view = evaluate(board, BLACK_PLAYER)
        self.assertGreater(red_view, 0)
        self.assertLess(black_view, 0)
        self.assertAlmostEqual(red_view, -black_view, places=6)


if __name__ == "__main__":
    unittest.main()
