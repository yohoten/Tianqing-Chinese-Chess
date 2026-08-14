"""游戏主循环：窗口、事件、渲染（依赖 pygame）。

玩家执红（下方），电脑执黑（上方），黑方由 Alpha-Beta AI 控制。
AI 在独立线程中思考，避免思考期间界面冻结。

状态机：PLAYING（玩家回合）→ AI_THINKING（电脑思考）→ 循环 / GAME_OVER（终局）。
"""
import threading

import pygame

from . import constants as C
from . import board as board_render
from .ai import DEFAULT_TIME_BUDGET, game_result
from .button import Button
from .fonts import get_font
from .chessai_bridge import (
    chessai_status,
    chessai_validate_move,
    fen_from_board,
)
from .engine import AlphaBetaEngine
from .pieces import (
    Board,
    Cannon,
    Elephant,
    King,
    Knight,
    Mandarin,
    Pawn,
    Rook,
    EMPTY,
    legal_moves_with_check,
    is_in_check,
)

# 游戏状态
STATE_PLAYING = "playing"            # 轮到玩家（红）
STATE_AI_THINKING = "ai_thinking"    # 电脑思考中（黑）
STATE_GAME_OVER = "game_over"        # 终局


class MainGame:
    """象棋主游戏。"""

    def __init__(self):
        self.window = None
        self.images = {}
        self.engine = AlphaBetaEngine()   # 走子引擎（可替换）
        self.pieces = []
        self.board = None
        self.selected = None          # 当前选中的棋子对象
        self.selected_moves = []      # 选中棋子的合法走法缓存（渲染用）
        self.current_player = C.RED_PLAYER
        self.state = STATE_PLAYING
        self.result_text = ""
        self.button_restart = None
        self.button_undo = None
        self.running = False
        self.ai_move = None           # AI 线程完成后的结果
        self.ai_thread = None
        self.epoch = 0                # 局面代次：丢弃过期 AI 线程的结果
        self.check_status = False     # 当前行动方是否被将军（渲染用缓存）
        self.history = []             # 走法历史 [(fx, fy, tx, ty, mover, victim)]
        self.last_move = None         # 最近一步 (fx, fy, tx, ty)，用于渲染标记
        self.captured = []            # 被吃棋子对象列表（悔棋时恢复）
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
        # 俘虏区小图缓存（避免每帧缩放）
        self.small_images = {
            key: pygame.transform.smoothscale(img, (C.CAPTIVE_ICON, C.CAPTIVE_ICON))
            for key, img in self.images.items()
        }
        self.button_undo = Button(self.window, "悔棋",
                                  C.BUTTON_LEFT, C.BTN_UNDO_Y)
        self.button_restart = Button(self.window, "重新开始",
                                     C.BUTTON_LEFT, C.BTN_RESTART_Y)
        self.reset_game()

    def reset_game(self):
        self.epoch += 1               # 新对局代次，旧 AI 线程结果作废
        self.pieces = self._init_pieces()
        self.board = Board(self.pieces)
        self.selected = None
        self.selected_moves = []
        self.current_player = C.RED_PLAYER
        self.state = STATE_PLAYING
        self.result_text = ""
        self.ai_move = None
        self.ai_thread = None
        self.check_status = False
        self.history = []
        self.last_move = None
        self.captured = []
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
        # 电脑思考状态：后台线程搜索，主线程继续渲染（界面不冻结）
        if self.state == STATE_AI_THINKING:
            if self.ai_thread is None and self.ai_move is None:
                self.ai_thread = threading.Thread(target=self._ai_work, daemon=True)
                self.ai_thread.start()
            elif self.ai_move is not None:
                move = self.ai_move
                self.ai_move = None
                self.ai_thread = None
                if move:
                    self._do_move(move)
                self._finish_turn()

    def _ai_work(self):
        """后台线程：执行 AI 搜索（只读 self.pieces，安全）。

        通过 epoch 校验丢弃过期结果：若线程期间用户点了“重新开始”或“悔棋”，
        结果不应用到新对局。
        """
        epoch = self.epoch
        try:
            move = self.engine.get_best_move(
                self.pieces, max_time=DEFAULT_TIME_BUDGET,
                player=C.BLACK_PLAYER,
            )
        except Exception as exc:
            print("AI 搜索异常：", exc)
            move = None
        if epoch == self.epoch:
            self.ai_move = move

    def _finish_turn(self):
        """切换行动方、检查终局并推进状态机。"""
        self.current_player = (
            C.BLACK_PLAYER if self.current_player == C.RED_PLAYER
            else C.RED_PLAYER
        )
        result = game_result(self.board, self.current_player)
        if result is not None:
            self.state = STATE_GAME_OVER
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
            self.state = (STATE_AI_THINKING
                          if self.current_player == C.BLACK_PLAYER
                          else STATE_PLAYING)
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
            self.analysis_hint = self.engine.get_best_move(
                self.pieces, max_time=0.5, player=self.current_player)
        except Exception:
            self.analysis_hint = None

    # ------------------------------------------------------------------
    # 走子与悔棋
    # ------------------------------------------------------------------

    def _do_move(self, move):
        fx, fy, tx, ty = move
        victim = self._piece_at(tx, ty)
        if victim is not None:
            self.pieces.remove(victim)
            self.captured.append(victim)
        self.board.move(fx, fy, tx, ty)
        piece = self._piece_at(fx, fy)
        piece.x, piece.y = tx, ty
        self.history.append((fx, fy, tx, ty, self.current_player, victim))
        self.last_move = (fx, fy, tx, ty)

    def undo_move(self):
        """悔棋：撤销最近一个完整回合，回到玩家上次决策前。

        玩家刚走完（电脑思考中）时撤销一步；玩家回合时撤销电脑+玩家两步。
        同时作废正在运行的 AI 线程结果（epoch 递增）。
        """
        if not self.history:
            return

        # 作废在跑的 AI 线程
        self.epoch += 1
        self.ai_move = None
        self.ai_thread = None

        def pop_one():
            fx, fy, tx, ty, _mover, victim = self.history.pop()
            piece = self._piece_at(tx, ty)
            # 被吃子信息来自 victim 对象；无吃子时目标格应恢复为空
            cap_color = victim.player if victim is not None else EMPTY
            cap_kind = victim.kind if victim is not None else ""
            self.board.unmove(fx, fy, tx, ty, cap_color, cap_kind)
            piece.x, piece.y = fx, fy
            if victim is not None:
                self.pieces.append(victim)
                if victim in self.captured:
                    self.captured.remove(victim)

        pop_one()
        # 若撤销后最后一步是红方（玩家）走的，继续撤销（完整回合 = 黑+红）
        if self.history and self.history[-1][4] == C.RED_PLAYER:
            pop_one()

        self.current_player = C.RED_PLAYER
        self.selected = None
        self.selected_moves = []
        self.state = STATE_PLAYING
        self.check_status = is_in_check(self.board, self.current_player)
        # 更新最近一步标记：若有剩余历史取最后一条，否则清空
        self.last_move = self.history[-1][:4] if self.history else None
        if self.show_analysis:
            self._refresh_analysis()

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
                # U 键悔棋
                elif event.key == pygame.K_u:
                    self.undo_move()

    def _on_click(self, pos):
        # 按钮始终可用（含终局/思考中）
        if self.button_restart.is_clicked(pos):
            self.reset_game()
            return
        if self.button_undo.is_clicked(pos):
            self.undo_move()
            return

        # 棋盘操作仅限玩家回合
        if self.state != STATE_PLAYING:
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

    def _find_king(self, player):
        """返回某方将/帅棋子（用于将军红环渲染）。"""
        for p in self.pieces:
            if p.player == player and p.kind == "king":
                return p
        return None

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------

    def _draw(self):
        self.window.fill(C.BG_COLOR)
        board_render.draw_chessboard(self.window)

        # 最近一步标记（起点实心点 + 终点圆环）
        if self.last_move is not None:
            board_render.draw_last_move(self.window, *self.last_move)

        # 选中高亮 + 可走提示（用缓存，避免每帧重算）
        if self.selected is not None and self.state != STATE_GAME_OVER:
            board_render.draw_highlight(self.window, self.selected.x, self.selected.y)
            for tx, ty in self.selected_moves:
                board_render.draw_hint(self.window, tx, ty)

        # 将军警报：被将军方的将/帅外圈红环
        if self.check_status and self.state != STATE_GAME_OVER:
            king = self._find_king(self.current_player)
            if king is not None:
                board_render.draw_check_ring(self.window, king.x, king.y)

        # 棋子
        for p in self.pieces:
            image = self.images[p.image_key]
            board_render.draw_piece(self.window, image, p.x, p.y)

        # 按钮状态：悔棋在无历史时禁用
        self.button_undo.disabled = not self.history
        self.button_undo.draw()
        self.button_restart.draw()
        self._draw_status()
        if self.show_analysis:
            self._draw_analysis()
        if self.state == STATE_GAME_OVER:
            self._draw_end_banner()

    def _draw_analysis(self):
        """绘制棋局分析面板（chessai 集成）。信息栏按钮下方分区。"""
        x = C.ANALYSIS_X
        y = C.ANALYSIS_Y
        step = C.ANALYSIS_STEP

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
        x = C.INFO_X
        y = C.INFO_Y

        # 信息栏标题
        board_render.draw_text(self.window, "天青 · 中国象棋", x + 10, y,
                               size=24, color=(90, 60, 30))

        if self.state == STATE_GAME_OVER:
            board_render.draw_text(self.window, self.result_text, x + 10, y + 55,
                                   size=22, color=C.TEXT_COLOR)
            return

        # 轮到谁（AI 思考时动态省略号）
        if self.state == STATE_AI_THINKING:
            dots = "." * ((pygame.time.get_ticks() // 500) % 4)
            turn_text = f"轮到：黑方（电脑思考中{dots}）"
        else:
            turn_text = "轮到：红方（你）"
        board_render.draw_text(self.window, turn_text, x + 10, y + 45,
                               size=18, color=C.BLACK)

        # 回合数
        round_no = len(self.history) // 2 + 1
        board_render.draw_text(self.window, f"第 {round_no} 回合", x + 10, y + 72,
                               size=16, color=(70, 70, 70))

        # 将军徽章（红底白字，用缓存状态）
        if self.check_status:
            badge = pygame.Rect(x + 10, y + 96, 96, 30)
            pygame.draw.rect(self.window, C.CHECK_RING_COLOR, badge, border_radius=6)
            board_render.draw_text(self.window, "将军！", x + 22, y + 102,
                                   size=20, color=C.WHITE)

        board_render.draw_text(self.window, "H 分析 / U 悔棋", x + 10, y + 140,
                               size=14, color=(120, 90, 60))

        # 俘虏区（双方被吃棋子小图）
        self._draw_captives(x + 10, C.CAPTIVE_Y, C.INFO_WIDTH - 20)

    def _draw_captives(self, x, y, max_width):
        """绘制双方俘虏小图（自动折行）。红方俘虏 = 被红方吃掉的子（黑子）。"""
        icon = C.CAPTIVE_ICON
        gap = 4
        row_h = icon + 6
        red_cap = [p for p in self.captured if p.player == C.BLACK_PLAYER]
        black_cap = [p for p in self.captured if p.player == C.RED_PLAYER]

        cy = y
        for label, group in (("红方俘虏:", red_cap), ("黑方俘虏:", black_cap)):
            board_render.draw_text(self.window, label, x, cy, size=14, color=(60, 60, 60))
            cy += 20
            cx = x
            if not group:
                board_render.draw_text(self.window, "（无）", x, cy,
                                       size=13, color=(150, 150, 150))
                cy += row_h
                continue
            for p in group:
                self.window.blit(self.small_images[p.image_key], (cx, cy))
                cx += icon + gap
                if cx + icon > x + max_width:
                    cx = x
                    cy += row_h
            cy += row_h

    def _draw_end_banner(self):
        """终局横幅：居中半透明底 + 大字结果。"""
        text = self.result_text or "对局结束"
        w, h = 440, 150
        bx = (C.SCREEN_WIDTH - w) // 2
        by = (C.SCREEN_HEIGHT - h) // 2 - 30
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((25, 25, 25, 185))
        self.window.blit(overlay, (bx, by))
        pygame.draw.rect(self.window, C.BOARD_FRAME, (bx, by, w, h), 4, border_radius=14)

        font = get_font(46)
        surf = font.render(text, True, C.WHITE)
        self.window.blit(surf, surf.get_rect(center=(C.SCREEN_WIDTH // 2, by + 58)))

        font2 = get_font(18)
        sub = font2.render("点击「重新开始」再来一局", True, (215, 215, 215))
        self.window.blit(sub, sub.get_rect(center=(C.SCREEN_WIDTH // 2, by + 116)))

def main():
    game = MainGame()
    game.setup()
    game.run()
