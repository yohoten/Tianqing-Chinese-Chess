"""游戏主循环：窗口、事件、渲染（依赖 pygame）。

玩家执红（下方），电脑执黑（上方），黑方由 Alpha-Beta AI 控制。
AI 在独立线程中思考，避免思考期间界面冻结。
"""
import threading

import pygame

from . import constants as C
from . import board as board_render
from .ai import DEFAULT_TIME_BUDGET, get_best_move, game_result
from .button import Button
from .chessai_bridge import (
    chessai_status,
    chessai_validate_move,
    fen_from_board,
)
from .pieces import (
    Board,
    Cannon,
    Elephant,
    King,
    Knight,
    Mandarin,
    Pawn,
    Rook,
    legal_moves_with_check,
    is_in_check,
)


class MainGame:
    """象棋主游戏。"""

    def __init__(self):
        self.window = None
        self.images = {}
        self.pieces = []
        self.board = None
        self.selected = None          # 当前选中的棋子对象
        self.selected_moves = []      # 选中棋子的合法走法缓存（渲染用）
        self.current_player = C.RED_PLAYER
        self.game_over = False
        self.result_text = ""
        self.button_restart = None
        self.running = False
        self.ai_thinking = False      # 是否有 AI 线程在思考
        self.ai_move = None           # AI 线程完成后的结果
        self.ai_thread = None
        self.epoch = 0                # 局面代次：丢弃过期 AI 线程的结果
        self.check_status = False     # 当前行动方是否被将军（渲染用缓存）
        # 棋局分析面板（chessai 集成）
        self.show_analysis = False
        self.analysis_fen = ""
        self.analysis_status = None   # chessai_status 返回 dict / None
        self.analysis_hint = None     # 自研 AI 推荐走法

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def setup(self):
        pygame.init()
        self.window = pygame.display.set_mode([C.SCREEN_WIDTH, C.SCREEN_HEIGHT])
        pygame.display.set_caption("天青-中国象棋")
        self.images = C.load_piece_images()
        self.button_restart = Button(self.window, "重新开始",
                                     C.SCREEN_WIDTH - 160, 300)
        self.reset_game()

    def reset_game(self):
        self.epoch += 1               # 新对局代次，旧 AI 线程结果作废
        self.pieces = self._init_pieces()
        self.board = Board(self.pieces)
        self.selected = None
        self.selected_moves = []
        self.current_player = C.RED_PLAYER
        self.game_over = False
        self.result_text = ""
        self.ai_thinking = False
        self.ai_move = None
        self.ai_thread = None
        self.check_status = False
        self.show_analysis = False
        self.analysis_fen = ""
        self.analysis_status = None
        self.analysis_hint = None

    @staticmethod
    def _init_pieces():
        """按标准开局摆放全部 32 枚棋子。"""
        pieces = []
        black = C.BLACK_PLAYER
        red = C.RED_PLAYER

        # 黑方（上方 y=0..3）
        pieces += [
            Rook(black, 0, 0), Rook(black, 8, 0),
            Knight(black, 1, 0), Knight(black, 7, 0),
            Elephant(black, 2, 0), Elephant(black, 6, 0),
            Mandarin(black, 3, 0), Mandarin(black, 5, 0),
            King(black, 4, 0),
            Cannon(black, 1, 2), Cannon(black, 7, 2),
            Pawn(black, 0, 3), Pawn(black, 2, 3), Pawn(black, 4, 3),
            Pawn(black, 6, 3), Pawn(black, 8, 3),
        ]
        # 红方（下方 y=6..9）
        pieces += [
            Rook(red, 0, 9), Rook(red, 8, 9),
            Knight(red, 1, 9), Knight(red, 7, 9),
            Elephant(red, 2, 9), Elephant(red, 6, 9),
            Mandarin(red, 3, 9), Mandarin(red, 5, 9),
            King(red, 4, 9),
            Cannon(red, 1, 7), Cannon(red, 7, 7),
            Pawn(red, 0, 6), Pawn(red, 2, 6), Pawn(red, 4, 6),
            Pawn(red, 6, 6), Pawn(red, 8, 6),
        ]
        return pieces

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------

    def run(self):
        self.running = True
        clock = pygame.time.Clock()
        while self.running:
            self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()
            clock.tick(10)   # 10 FPS 足够棋类游戏
        pygame.quit()

    def _update(self):
        # 轮到电脑时在后台线程思考，主线程继续渲染（界面不冻结）
        if not self.game_over and self.current_player == C.BLACK_PLAYER:
            if self.ai_thread is None and self.ai_move is None:
                self.ai_thinking = True
                self.ai_thread = threading.Thread(target=self._ai_work, daemon=True)
                self.ai_thread.start()
            elif self.ai_move is not None:
                move = self.ai_move
                self.ai_move = None
                self.ai_thread = None
                self.ai_thinking = False
                if move:
                    self._do_move(move)
                self._finish_turn()

    def _ai_work(self):
        """后台线程：执行 AI 搜索（只读 self.pieces，安全）。

        通过 epoch 校验丢弃过期结果：若线程期间用户点了“重新开始”，
        结果不应用到新对局。
        """
        epoch = self.epoch
        try:
            move = get_best_move(
                self.pieces, depth=4, max_time=DEFAULT_TIME_BUDGET,
                player=C.BLACK_PLAYER,
            )
        except Exception as exc:
            print("AI 搜索异常：", exc)
            move = None
        if epoch == self.epoch:
            self.ai_move = move

    def _finish_turn(self):
        """切换行动方并检查终局。"""
        self.current_player = (
            C.BLACK_PLAYER if self.current_player == C.RED_PLAYER
            else C.RED_PLAYER
        )
        result = game_result(self.board, self.current_player)
        if result is not None:
            self.game_over = True
            self.check_status = False
            if result == 0:
                self.result_text = "困毙，和棋"
            elif result == C.RED_PLAYER:
                self.result_text = "红方胜！"
            else:
                self.result_text = "黑方胜！"
        else:
            # 缓存将军状态供渲染，避免每帧全盘扫描
            self.check_status = is_in_check(self.board, self.current_player)
        if self.show_analysis:
            self._refresh_analysis()

    def _refresh_analysis(self):
        """刷新分析面板缓存（chessai 状态 + 自研 AI 推荐走法）。"""
        try:
            self.analysis_fen = fen_from_board(self.board, self.current_player)
        except Exception:
            self.analysis_fen = ""
        try:
            self.analysis_status = chessai_status(self.board, self.current_player)
        except Exception:
            self.analysis_status = None
        # 自研 AI 浅层快速推荐（预算 0.5s，实际通常远小于此）
        try:
            self.analysis_hint = get_best_move(
                self.pieces, depth=2, max_time=0.5, player=self.current_player)
        except Exception:
            self.analysis_hint = None

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._on_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                # H / F1 切换棋局分析面板（chessai 集成）
                if event.key in (pygame.K_h, pygame.K_F1):
                    self.show_analysis = not self.show_analysis
                    if self.show_analysis:
                        self._refresh_analysis()

    def _on_click(self, pos):
        # 重新开始按钮始终可用
        if self.button_restart.is_clicked(pos):
            self.reset_game()
            return

        if self.game_over or self.current_player != C.RED_PLAYER:
            return

        xy = self._pixel_to_board(pos)
        if xy is None:
            return
        self._handle_board_click(*xy)

    def _handle_board_click(self, x, y):
        piece = self._piece_at(x, y)

        # 点中自己的棋子 -> 选中并缓存可走位置
        if piece is not None and piece.player == self.current_player:
            self.selected = piece
            self.selected_moves = legal_moves_with_check(
                self.board, self.current_player, piece.x, piece.y)
            return

        # 已有选中且目标可走（已过滤送将）-> 走子
        if self.selected is not None:
            fx, fy = self.selected.x, self.selected.y
            if (x, y) in self.selected_moves:
                self._do_move((fx, fy, x, y))
                self.selected = None
                self.selected_moves = []
                self._finish_turn()

    def _pixel_to_board(self, pos):
        """屏幕像素 -> 棋盘格子 (x, y)；棋盘外返回 None。"""
        mx, my = pos
        if not (C.BOARD_MIN_X <= mx <= C.BOARD_MAX_X and
                C.BOARD_MIN_Y <= my <= C.BOARD_MAX_Y):
            return None
        x = round((mx - C.START_X) / C.LINE_SPAN)
        y = round((my - C.START_Y) / C.LINE_SPAN)
        if 0 <= x < C.BOARD_COLS and 0 <= y < C.BOARD_ROWS:
            return x, y
        return None

    def _piece_at(self, x, y):
        for p in self.pieces:
            if p.x == x and p.y == y:
                return p
        return None

    def _do_move(self, move):
        fx, fy, tx, ty = move
        victim = self._piece_at(tx, ty)
        if victim is not None:
            self.pieces.remove(victim)
        self.board.move(fx, fy, tx, ty)
        piece = self._piece_at(fx, fy)
        piece.x, piece.y = tx, ty

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------

    def _draw(self):
        self.window.fill(C.BG_COLOR)
        board_render.draw_chessboard(self.window)

        # 选中高亮 + 可走提示（用缓存，避免每帧重算）
        if self.selected is not None and not self.game_over:
            board_render.draw_highlight(self.window, self.selected.x, self.selected.y)
            for tx, ty in self.selected_moves:
                board_render.draw_hint(self.window, tx, ty)

        # 棋子
        for p in self.pieces:
            image = self.images[p.image_key]
            board_render.draw_piece(self.window, image, p.x, p.y)

        self.button_restart.draw()
        self._draw_status()
        if self.show_analysis:
            self._draw_analysis()

    def _draw_analysis(self):
        """绘制棋局分析面板（chessai 集成）。右侧按钮上方区域。"""
        x = C.SCREEN_WIDTH - 320
        y = C.START_Y
        step = 24

        board_render.draw_text(self.window, "== 棋局分析 (chessai) ==",
                               x, y, size=18, color=C.BLUE)
        y += step

        side = "红(r)" if self.current_player == C.RED_PLAYER else "黑(b)"
        board_render.draw_text(self.window, f"轮到: {side}", x, y, size=16, color=C.BLACK)
        y += step

        # FEN（chessai 生成；未安装时为空）
        board_render.draw_text(self.window, "FEN:", x, y, size=16, color=C.BLACK)
        y += step
        if self.analysis_fen:
            fen = self.analysis_fen
            half = len(fen) // 2
            board_render.draw_text(self.window, fen[:half], x, y, size=14, color=C.BLACK)
            y += step
            board_render.draw_text(self.window, fen[half:], x, y, size=14, color=C.BLACK)
        else:
            board_render.draw_text(self.window, "(chessai 未安装)", x, y, size=14, color=(120, 120, 120))
        y += step

        # chessai 局面状态
        if self.analysis_status is not None:
            st = self.analysis_status
            text = "将军" if st["in_check"] else "未将军"
            if st["checkmate"]:
                text += " | 将死"
            if st["kings_face"]:
                text += " | 飞将"
            board_render.draw_text(self.window, "chessai: " + text, x, y,
                                   size=16, color=C.TEXT_COLOR if st["in_check"] else C.BLACK)
        else:
            board_render.draw_text(self.window, "chessai: 不可用", x, y,
                                   size=16, color=(120, 120, 120))
        y += step

        # 自研 AI 推荐走法 + chessai 交叉校验
        if self.analysis_hint is not None:
            fx, fy, tx, ty = self.analysis_hint
            hint = f"AI推荐: ({fx},{fy})->({tx},{ty})"
            board_render.draw_text(self.window, hint, x, y, size=16, color=C.GREEN)
            y += step
            ok = chessai_validate_move(self.board, self.current_player, fx, fy, tx, ty)
            if ok is None:
                mark = "chessai: N/A"
            elif ok:
                mark = "chessai: 校验通过 ✓"
            else:
                mark = "chessai: 校验不一致 ✗"
            board_render.draw_text(self.window, mark, x, y, size=14, color=C.BLACK)
        else:
            board_render.draw_text(self.window, "AI推荐: (计算中...)", x, y,
                                   size=16, color=(120, 120, 120))
        y += step + 6

        board_render.draw_text(self.window, "按 H/F1 关闭分析", x, y,
                               size=14, color=(120, 120, 120))

    def _draw_status(self):
        x = C.SCREEN_WIDTH - 160
        y = C.START_Y

        if self.game_over:
            board_render.draw_text(self.window, self.result_text, x, y + 40,
                                   size=22, color=C.TEXT_COLOR)
            return

        # 轮到谁
        if self.current_player == C.RED_PLAYER:
            turn_text = "轮到：红方（你）"
        else:
            turn_text = "轮到：黑方（电脑思考中...）"
        board_render.draw_text(self.window, turn_text, x, y, size=18,
                               color=C.TEXT_COLOR)

        # 将军提示（用缓存）
        if self.check_status:
            board_render.draw_text(self.window, "将军！", x, y + 30,
                                   size=22, color=C.TEXT_COLOR)
        board_render.draw_text(self.window, "按 H 查看棋局分析", x, y + 60,
                               size=14, color=(120, 120, 120))


def main():
    game = MainGame()
    game.setup()
    game.run()
