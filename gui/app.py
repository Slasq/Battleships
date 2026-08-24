import pygame

from . import analysis_view, board_view, menu_view, panel_view
from .analysis import Analysis
from .match import MODE_AIVAI, MODE_PVAI, Match
from .menu import Menu
from .panel_view import ATTACKS, ATTACK_RECTS
from .theme import AI_ORIGIN, BEZEL, BEZEL_EDGE, BG, BG_STRIPE, SCREEN_H, SCREEN_W
from .window import Layout

FPS = 60

MENU = "menu"
GAME = "game"
ANALYSIS = "analysis"


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Battleship")

        self.layout = Layout()
        self.screen = pygame.display.set_mode((self.layout.win_w, self.layout.win_h))
        self.clock = pygame.time.Clock()

        self.top_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self.bot_surf = pygame.Surface((SCREEN_W, SCREEN_H))
        self.backdrop = self._build_backdrop()

        self.menu = Menu()
        self.match = Match()
        self.analysis = Analysis()
        self.scene = MENU
        self.analysis_return = MENU
        self.pressed_atk = None
        self.running = True

    def _build_backdrop(self):
        w, h = self.layout.win_w, self.layout.win_h
        surf = pygame.Surface((w, h))
        surf.fill(BG)
        for i in range(-h, w, 16):
            pygame.draw.line(surf, BG_STRIPE, (i, 0), (i + h, h), 2)
        for bezel in (self.layout.top_bezel, self.layout.bot_bezel):
            pygame.draw.rect(surf, BEZEL, bezel, border_radius=8)
            pygame.draw.rect(surf, BEZEL_EDGE, bezel, 2, border_radius=8)
        return surf

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB and self.scene != ANALYSIS:
                self.open_analysis()
            elif self.scene == MENU:
                self._menu_key(event.key)
            elif self.scene == ANALYSIS:
                self._analysis_key(event.key)
            else:
                self._game_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.scene == MENU:
                self._menu_click(event.pos)
            elif self.scene == ANALYSIS:
                self._analysis_click(event.pos)
            else:
                self._game_click(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            if self.scene == MENU:
                self._menu_hover(event.pos)
            elif self.scene == ANALYSIS:
                self._analysis_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed_atk = None

    def open_analysis(self):
        self.analysis_return = self.scene
        self.analysis.load(self.match)
        self.scene = ANALYSIS

    def _close_analysis(self):
        self.scene = self.analysis_return

    def _analysis_key(self, key):
        if key in (pygame.K_ESCAPE, pygame.K_TAB):
            self._close_analysis()
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.analysis.move(-1, 0)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.analysis.move(1, 0)
        elif key in (pygame.K_UP, pygame.K_w):
            self.analysis.move(0, -1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.analysis.move(0, 1)
        elif key == pygame.K_v:
            if self.analysis.has_tabs():
                self.analysis.set_iso(not self.analysis.iso)
        elif key == pygame.K_p:
            self.analysis.playing = not self.analysis.playing
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_k):
            if self.analysis.activate() == "exit":
                self._close_analysis()

    def _analysis_hover(self, pos):
        if self.layout.top_rect.collidepoint(pos):
            local = self.layout.local(pos, self.layout.top_rect)
            if analysis_view.hit_test_tabs(self.analysis, local) is None:
                self.analysis.set_hover(analysis_view.hit_test_view(self.analysis, local))
        elif self.layout.bot_rect.collidepoint(pos):
            local = self.layout.local(pos, self.layout.bot_rect)
            index = analysis_view.hit_test_buttons(local)
            if index is not None:
                self.analysis.selected = index

    def _analysis_click(self, pos):
        if self.layout.top_rect.collidepoint(pos):
            local = self.layout.local(pos, self.layout.top_rect)
            action = analysis_view.hit_test_tabs(self.analysis, local)
            if action is None:
                return
            if action[0] == "iso":
                self.analysis.set_iso(action[1])
            else:
                self.analysis.set_side(action[1])
            return
        if not self.layout.bot_rect.collidepoint(pos):
            return
        local = self.layout.local(pos, self.layout.bot_rect)
        index = analysis_view.hit_test_buttons(local)
        if index is None:
            return
        self.analysis.selected = index
        if self.analysis.activate(index) == "exit":
            self._close_analysis()

    def _menu_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key in (pygame.K_UP, pygame.K_w):
            self.menu.move(-1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu.move(1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_k):
            self._run_action(self.menu.activate())

    def _menu_hover(self, pos):
        if not self.layout.bot_rect.collidepoint(pos):
            return
        index = menu_view.hit_test(self.layout.local(pos, self.layout.bot_rect))
        if index is not None:
            self.menu.select(index)

    def _menu_click(self, pos):
        if self.layout.top_rect.collidepoint(pos):
            self._run_action("play")
            return
        if not self.layout.bot_rect.collidepoint(pos):
            return
        index = menu_view.hit_test(self.layout.local(pos, self.layout.bot_rect))
        if index is not None:
            self.menu.select(index)
            self._run_action(self.menu.activate())

    def _run_action(self, action):
        if action == "quit":
            self.running = False
        elif action == "play":
            self.match.reset(MODE_PVAI)
            self.scene = GAME
        elif action == "ai_vs_ai":
            self.match.reset(MODE_AIVAI)
            self.scene = GAME

    def _game_key(self, key):
        match = self.match
        if key == pygame.K_a and match.over:
            self.open_analysis()
        elif key == pygame.K_ESCAPE:
            self.scene = MENU
        elif key == pygame.K_SPACE:
            match.paused = not match.paused
        elif key == pygame.K_r:
            match.reset()
        elif key == pygame.K_t:
            match.do_train()
        elif key in (pygame.K_e, pygame.K_y, pygame.K_j):
            match.do_epsilon()
        elif key in (pygame.K_UP, pygame.K_w):
            match.move_cursor(0, -1)
        elif key in (pygame.K_DOWN, pygame.K_s):
            match.move_cursor(0, 1)
        elif key in (pygame.K_LEFT, pygame.K_a):
            match.move_cursor(-1, 0)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            match.move_cursor(1, 0)
        elif key in (pygame.K_RETURN, pygame.K_k):
            match.do_env_step()
        elif key in (pygame.K_x, pygame.K_i, pygame.K_h):
            match.do_q_predict()
        elif key in (pygame.K_z, pygame.K_b):
            match.predicted = None

    def _game_click(self, pos):
        if self.layout.top_rect.collidepoint(pos):
            local = self.layout.local(pos, self.layout.top_rect)
            hit = board_view.hit_test(self.match, local, AI_ORIGIN)
            if hit is not None:
                self.match.cursor = hit
                self.match.do_env_step()
            return
        if self.layout.bot_rect.collidepoint(pos):
            local = self.layout.local(pos, self.layout.bot_rect)
            for i, rect in enumerate(ATTACK_RECTS):
                if rect.collidepoint(local):
                    self.pressed_atk = i
                    ATTACKS[i][3](self.match)
                    return

    def draw(self):
        self.screen.blit(self.backdrop, (0, 0))
        if self.scene == MENU:
            menu_view.render_top(self.top_surf)
            menu_view.render_bottom(self.bot_surf, self.menu)
        elif self.scene == ANALYSIS:
            analysis_view.render_top(self.top_surf, self.analysis)
            analysis_view.render_bottom(self.bot_surf, self.analysis)
        else:
            board_view.render(self.top_surf, self.match)
            panel_view.render(self.bot_surf, self.match, self.pressed_atk)
        self.screen.blit(
            pygame.transform.scale(self.top_surf, self.layout.top_rect.size),
            self.layout.top_rect,
        )
        self.screen.blit(
            pygame.transform.scale(self.bot_surf, self.layout.bot_rect.size),
            self.layout.bot_rect,
        )

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                self.handle_event(event)
            if self.scene == GAME:
                self.match.tick(dt)
            elif self.scene == ANALYSIS:
                self.analysis.tick(dt)
            self.draw()
            pygame.display.flip()
        pygame.quit()
