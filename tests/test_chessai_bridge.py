"""chessai 桥接层单元测试。

兼容两种环境：
- 已安装 chessai-python：断言具体转换/校验结果
- 未安装：断言优雅降级（None / 空串），游戏仍可用
"""
import unittest

from chinese_chess.constants import RED_PLAYER, BLACK_PLAYER
from chinese_chess.pieces import (
    Board, Rook, Knight, Elephant, Mandarin, King, Cannon, Pawn,
)
from chinese_chess.chessai_bridge import (
    CHESSAI_TYPE_CODE,
    to_chessai_board,
    from_chessai_board,
    fen_from_board,
    chessai_validate_move,
    chessai_status,
)


def opening_board() -> Board:
    b, r = BLACK_PLAYER, RED_PLAYER
    pieces = [Rook(b, 0, 0), Rook(b, 8, 0), Knight(b, 1, 0), Knight(b, 7, 0),
              Elephant(b, 2, 0), Elephant(b, 6, 0), Mandarin(b, 3, 0), Mandarin(b, 5, 0),
              King(b, 4, 0), Cannon(b, 1, 2), Cannon(b, 7, 2),
              Pawn(b, 0, 3), Pawn(b, 2, 3), Pawn(b, 4, 3), Pawn(b, 6, 3), Pawn(b, 8, 3),
              Rook(r, 0, 9), Rook(r, 8, 9), Knight(r, 1, 9), Knight(r, 7, 9),
              Elephant(r, 2, 9), Elephant(r, 6, 9), Mandarin(r, 3, 9), Mandarin(r, 5, 9),
              King(r, 4, 9), Cannon(r, 1, 7), Cannon(r, 7, 7),
              Pawn(r, 0, 6), Pawn(r, 2, 6), Pawn(r, 4, 6), Pawn(r, 6, 6), Pawn(r, 8, 6)]
    return Board(pieces)


def chessai_available() -> bool:
    try:
        import chessai  # noqa: F401
        return True
    except Exception:
        return False


class TestConversion(unittest.TestCase):
    """转换与往返（不依赖 chessai，纯自研逻辑）。"""

    def test_to_chessai_board_counts(self):
        arr = to_chessai_board(opening_board())
        self.assertEqual(len(arr), 10)
        self.assertEqual(len(arr[0]), 9)
        n = sum(1 for row in arr for c in row if c)
        self.assertEqual(n, 32)

    def test_roundtrip(self):
        board = opening_board()
        arr = to_chessai_board(board)
        back = from_chessai_board(arr)
        self.assertIsNotNone(back)
        for x in range(9):
            for y in range(10):
                self.assertEqual(board.color[x][y], back.color[x][y])
                self.assertEqual(board.kind[x][y], back.kind[x][y])

    def test_type_code_mapping_complete(self):
        self.assertEqual(sorted(CHESSAI_TYPE_CODE), sorted(
            ["rook", "knight", "elephant", "mandarin", "king", "cannon", "pawn"]))


@unittest.skipUnless(chessai_available(), "chessai-python 未安装")
class TestChessaiValidate(unittest.TestCase):
    """chessai 交叉校验（需要 chessai-python）。"""

    def test_legal_move_accepted(self):
        board = opening_board()
        # 红马 (1,9)->(2,7) 日字合法
        self.assertTrue(chessai_validate_move(board, RED_PLAYER, 1, 9, 2, 7))

    def test_illegal_move_rejected(self):
        board = opening_board()
        # 红车 (0,9)->(0,5) 越过己方兵，非法
        self.assertFalse(chessai_validate_move(board, RED_PLAYER, 0, 9, 0, 5))

    def test_status_opening(self):
        board = opening_board()
        st = chessai_status(board, RED_PLAYER)
        self.assertEqual(st, {"in_check": False, "checkmate": False, "kings_face": False})

    def test_fen_generation(self):
        fen = fen_from_board(opening_board(), RED_PLAYER)
        self.assertTrue(fen.startswith("rnbakabnr/"))


@unittest.skipUnless(not chessai_available(), "此环境已安装 chessai")
class TestGracefulDegrade(unittest.TestCase):
    """无 chessai 环境的优雅降级。"""

    def test_validate_returns_none(self):
        self.assertIsNone(chessai_validate_move(opening_board(), RED_PLAYER, 1, 9, 2, 7))

    def test_status_returns_none(self):
        self.assertIsNone(chessai_status(opening_board(), RED_PLAYER))

    def test_fen_empty(self):
        self.assertEqual(fen_from_board(opening_board(), RED_PLAYER), "")


if __name__ == "__main__":
    unittest.main()
