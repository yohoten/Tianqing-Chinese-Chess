"""UI 无头冒烟测试：验证 setup / 渲染 / 布局不崩溃（需要 pygame + dummy 驱动）。

用法：python scripts/smoke_ui.py
覆盖：初始布局、最近一步标记、将军警报、俘虏区（含自动折行）、AI 思考动画、
      分析面板、终局横幅、悔棋禁用态。
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
from chinese_chess import constants as C  # noqa: E402
from chinese_chess.game import (  # noqa: E402
    MainGame,
    STATE_AI_THINKING,
    STATE_GAME_OVER,
)


def main():
    game = MainGame()
    game.setup()

    # 1) 初始布局渲染数帧
    for _ in range(3):
        game._draw()
        pygame.display.flip()

    # 2) 最近一步标记
    game.last_move = (1, 2, 1, 3)
    game._draw()
    pygame.display.flip()

    # 3) 将军警报：将子红环 + 状态栏徽章
    game.check_status = True
    game._draw()
    pygame.display.flip()
    game.check_status = False

    # 4) 俘虏区：模拟吃子（黑 2 + 红 3，验证自动折行与空态）
    game.captured = ([p for p in game.pieces if p.player == C.BLACK_PLAYER][:2]
                     + [p for p in game.pieces if p.player == C.RED_PLAYER][:3])
    game._draw()
    pygame.display.flip()
    game.captured = []          # 空态（显示"无"）
    game._draw()
    pygame.display.flip()

    # 5) AI 思考动画（动态省略号路径）
    game.state = STATE_AI_THINKING
    game._draw()
    pygame.display.flip()

    # 6) 分析面板（直接注入缓存，跳过 AI 搜索以提速）
    game.state = "playing"
    game.show_analysis = True
    game.analysis_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR"
    game.analysis_status = {"in_check": False, "checkmate": False, "kings_face": False}
    game.analysis_hint = (4, 9, 4, 8)
    game._draw()
    pygame.display.flip()

    # 7) 终局横幅
    game.state = STATE_GAME_OVER
    game.result_text = "红方胜！"
    game._draw()
    pygame.display.flip()

    # 8) 悔棋禁用态（无历史）
    game.state = "playing"
    game.history = []
    game.check_status = False
    game._draw()
    pygame.display.flip()

    print("SMOKE OK | 窗口:", C.SCREEN_WIDTH, "x", C.SCREEN_HEIGHT,
          "| 图片:", len(game.images),
          "| 棋子:", len(game.pieces),
          "| 俘虏:", len(game.captured),
          "| 悔棋按钮:", game.button_undo.rect.topleft,
          "| 重开按钮:", game.button_restart.rect.topleft)
    pygame.quit()


if __name__ == "__main__":
    main()
