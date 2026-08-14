"""走法规则单元测试（不依赖 pygame）。"""
import unittest

from chinese_chess.constants import RED_PLAYER, BLACK_PLAYER
from chinese_chess.pieces import (
    Board,
    Rook,
    Cannon,
    Knight,
    Elephant,
    Mandarin,
    King,
    Pawn,
    legal_moves_with_check,
    all_legal_moves,
    is_in_check,
    PIECE_MOVE_FUNCS,
)


def moves_of(kind, x, y, player, board):
    return set(PIECE_MOVE_FUNCS[kind](x, y, player, board.color))


class TestRook(unittest.TestCase):
    def test_empty_board_straight_lines(self):
        board = Board()
        board.place(RED_PLAYER, "rook", 0, 0)
        moves = moves_of("rook", 0, 0, RED_PLAYER, board)
        # 右 8 + 下 9 = 17
        self.assertEqual(len(moves), 17)
        self.assertIn((8, 0), moves)
        self.assertIn((0, 9), moves)

    def test_blocked_by_own_piece(self):
        board = Board()
        board.place(RED_PLAYER, "rook", 0, 0)
        board.place(RED_PLAYER, "pawn", 0, 3)
        moves = moves_of("rook", 0, 0, RED_PLAYER, board)
        self.assertIn((0, 2), moves)
        self.assertNotIn((0, 3), moves)   # 自己子不可吃
        self.assertNotIn((0, 4), moves)   # 不可越子

    def test_capture_opponent(self):
        board = Board()
        board.place(RED_PLAYER, "rook", 0, 0)
        board.place(BLACK_PLAYER, "pawn", 0, 3)
        moves = moves_of("rook", 0, 0, RED_PLAYER, board)
        self.assertIn((0, 3), moves)      # 可吃对方
        self.assertNotIn((0, 4), moves)   # 吃后不能再越


class TestCannon(unittest.TestCase):
    def test_empty_board_cannot_capture(self):
        board = Board()
        board.place(RED_PLAYER, "cannon", 0, 0)
        moves = moves_of("cannon", 0, 0, RED_PLAYER, board)
        self.assertEqual(len(moves), 17)  # 无炮架只能平移

    def test_capture_with_screen(self):
        board = Board()
        board.place(RED_PLAYER, "cannon", 0, 0)
        board.place(BLACK_PLAYER, "pawn", 0, 3)    # 炮架
        board.place(BLACK_PLAYER, "rook", 0, 5)    # 被吃的子
        moves = moves_of("cannon", 0, 0, RED_PLAYER, board)
        self.assertIn((0, 1), moves)     # 平移空格
        self.assertIn((0, 2), moves)
        self.assertNotIn((0, 3), moves)  # 炮架不能落子
        self.assertIn((0, 5), moves)     # 隔一子吃
        self.assertNotIn((0, 6), moves)  # 隔两子不能吃

    def test_cannot_capture_own_piece(self):
        board = Board()
        board.place(RED_PLAYER, "cannon", 0, 0)
        board.place(RED_PLAYER, "pawn", 0, 3)
        board.place(RED_PLAYER, "rook", 0, 5)
        moves = moves_of("cannon", 0, 0, RED_PLAYER, board)
        self.assertNotIn((0, 5), moves)  # 隔炮架后是自己子不可吃


class TestKnight(unittest.TestCase):
    def test_empty_board_corner(self):
        board = Board()
        board.place(RED_PLAYER, "knight", 0, 0)
        moves = moves_of("knight", 0, 0, RED_PLAYER, board)
        self.assertEqual(moves, {(1, 2), (2, 1)})

    def test_blocked_leg(self):
        board = Board()
        board.place(RED_PLAYER, "knight", 0, 0)
        board.place(RED_PLAYER, "pawn", 1, 0)   # 挡住 (2,1) 的腿
        moves = moves_of("knight", 0, 0, RED_PLAYER, board)
        self.assertNotIn((2, 1), moves)
        self.assertIn((1, 2), moves)


class TestElephant(unittest.TestCase):
    def test_cannot_cross_river(self):
        board = Board()
        board.place(RED_PLAYER, "elephant", 2, 9)
        moves = moves_of("elephant", 2, 9, RED_PLAYER, board)
        self.assertEqual(moves, {(0, 7), (4, 7)})

    def test_blocked_eye(self):
        board = Board()
        board.place(RED_PLAYER, "elephant", 2, 9)
        board.place(RED_PLAYER, "pawn", 3, 8)   # 塞象眼
        moves = moves_of("elephant", 2, 9, RED_PLAYER, board)
        self.assertNotIn((4, 7), moves)
        self.assertIn((0, 7), moves)

    def test_black_elephant_side(self):
        board = Board()
        board.place(BLACK_PLAYER, "elephant", 2, 0)
        moves = moves_of("elephant", 2, 0, BLACK_PLAYER, board)
        self.assertEqual(moves, {(0, 2), (4, 2)})


class TestMandarin(unittest.TestCase):
    def test_red_palace_diagonal(self):
        board = Board()
        board.place(RED_PLAYER, "mandarin", 3, 9)
        moves = moves_of("mandarin", 3, 9, RED_PLAYER, board)
        # 红士在九宫左下角，只有 (4,8) 一个斜点仍在九宫内（x 3-5）
        self.assertEqual(moves, {(4, 8)})

    def test_red_palace_center(self):
        board = Board()
        board.place(RED_PLAYER, "mandarin", 4, 8)
        moves = moves_of("mandarin", 4, 8, RED_PLAYER, board)
        self.assertEqual(moves, {(3, 9), (5, 9), (3, 7), (5, 7)})

    def test_black_palace(self):
        board = Board()
        board.place(BLACK_PLAYER, "mandarin", 3, 0)
        moves = moves_of("mandarin", 3, 0, BLACK_PLAYER, board)
        self.assertEqual(moves, {(4, 1)})


class TestKing(unittest.TestCase):
    def test_palace_straight(self):
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        moves = moves_of("king", 4, 9, RED_PLAYER, board)
        self.assertEqual(moves, {(3, 9), (5, 9), (4, 8)})

    def test_flying_general_check(self):
        # 将帅同列且中间无子 -> 视为被将军（飞将）
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(BLACK_PLAYER, "king", 4, 0)
        self.assertTrue(is_in_check(board, RED_PLAYER))
        self.assertTrue(is_in_check(board, BLACK_PLAYER))

    def test_flying_general_blocked(self):
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(BLACK_PLAYER, "king", 4, 0)
        board.place(RED_PLAYER, "pawn", 4, 5)   # 中间有子遮挡
        self.assertFalse(is_in_check(board, RED_PLAYER))


class TestPawn(unittest.TestCase):
    def test_red_before_river_forward_only(self):
        board = Board()
        board.place(RED_PLAYER, "pawn", 4, 6)
        moves = moves_of("pawn", 4, 6, RED_PLAYER, board)
        self.assertEqual(moves, {(4, 5)})

    def test_red_after_river_can_side(self):
        board = Board()
        board.place(RED_PLAYER, "pawn", 4, 4)
        moves = moves_of("pawn", 4, 4, RED_PLAYER, board)
        self.assertEqual(moves, {(4, 3), (3, 4), (5, 4)})

    def test_black_before_river(self):
        board = Board()
        board.place(BLACK_PLAYER, "pawn", 4, 3)
        moves = moves_of("pawn", 4, 3, BLACK_PLAYER, board)
        self.assertEqual(moves, {(4, 4)})

    def test_black_after_river(self):
        board = Board()
        board.place(BLACK_PLAYER, "pawn", 4, 5)
        moves = moves_of("pawn", 4, 5, BLACK_PLAYER, board)
        self.assertEqual(moves, {(4, 6), (3, 5), (5, 5)})


class TestNoSelfCheck(unittest.TestCase):
    def test_king_cannot_move_into_attack(self):
        # 黑车 (4,0) 控制整列，红王 (4,9) 被将军，只能横移到两侧
        board = Board()
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(BLACK_PLAYER, "rook", 4, 0)
        legal = set(legal_moves_with_check(board, RED_PLAYER, 4, 9))
        self.assertEqual(legal, {(3, 9), (5, 9)})

    def test_pawn_blocked_king_escape(self):
        # 黑王被红车将军，王走 (3,0)/(4,1) 都仍在攻击线，只有 (5,0) 合法
        board = Board()
        board.place(BLACK_PLAYER, "king", 4, 0)
        board.place(RED_PLAYER, "king", 4, 9)
        board.place(RED_PLAYER, "rook", 3, 1)
        legal = set(legal_moves_with_check(board, BLACK_PLAYER, 4, 0))
        self.assertEqual(legal, {(5, 0)})


class TestOpening(unittest.TestCase):
    def test_opening_red_has_moves(self):
        pieces = [Rook(RED_PLAYER, 0, 9), Rook(RED_PLAYER, 8, 9),
                  Knight(RED_PLAYER, 1, 9), Knight(RED_PLAYER, 7, 9),
                  Elephant(RED_PLAYER, 2, 9), Elephant(RED_PLAYER, 6, 9),
                  Mandarin(RED_PLAYER, 3, 9), Mandarin(RED_PLAYER, 5, 9),
                  King(RED_PLAYER, 4, 9),
                  Cannon(RED_PLAYER, 1, 7), Cannon(RED_PLAYER, 7, 7),
                  Pawn(RED_PLAYER, 0, 6), Pawn(RED_PLAYER, 2, 6),
                  Pawn(RED_PLAYER, 4, 6), Pawn(RED_PLAYER, 6, 6),
                  Pawn(RED_PLAYER, 8, 6)]
        board = Board(pieces)
        moves = all_legal_moves(board, RED_PLAYER)
        self.assertGreaterEqual(len(moves), 40)
        # 所有走法执行后己方将不被将军（不送将）
        for fx, fy, tx, ty in moves:
            sim = board.copy()
            sim.move(fx, fy, tx, ty)
            self.assertFalse(is_in_check(sim, RED_PLAYER))


if __name__ == "__main__":
    unittest.main()
