"""资源文件一致性测试：确保 assets/s2 包含代码所需全部棋子图片（不依赖 pygame）。"""
import unittest

from chinese_chess.constants import ASSETS_DIR, PIECE_KINDS


class TestAssets(unittest.TestCase):
    def test_all_piece_images_exist(self):
        missing = []
        for side in ("r", "b"):
            for kind in PIECE_KINDS:
                path = ASSETS_DIR / f"{side}_{kind}.gif"
                if not path.exists():
                    missing.append(path.name)
        self.assertEqual(missing, [],
                         "缺少棋子图片: %s（请检查 assets/s2 目录）" % ", ".join(missing))

    def test_no_unexpected_extra(self):
        expected = {f"{side}_{kind}.gif" for side in ("r", "b") for kind in PIECE_KINDS}
        actual = {p.name for p in ASSETS_DIR.glob("*.gif")}
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
