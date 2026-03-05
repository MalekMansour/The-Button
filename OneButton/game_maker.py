import pygame
import sys
import math
import time
from collections import deque

pygame.init()
pygame.font.init()

# -----------------------------
# WINDOW
# -----------------------------
WIDTH, HEIGHT = 1200, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("THE BUTTON — One-Button Game Maker")
clock = pygame.time.Clock()

# -----------------------------
# COLORS / THEME
# -----------------------------
# Left button panel
PANEL_BG = (245, 245, 248)
BTN_RED = (210, 40, 40)
BTN_HOVER = (240, 70, 70)
BTN_PRESSED = (190, 25, 25)
BTN_SHADOW = (150, 20, 20)
BTN_TEXT = (255, 255, 255)

# Main editor (neon-ish)
BG = (16, 18, 26)
GRID_BG = (30, 34, 48)
GRID_LINE = (25, 28, 42)
TOP_BAR = (25, 28, 40)
TOP_BORDER = (70, 80, 110)
TEXT_MAIN = (240, 240, 255)
TEXT_DIM = (170, 175, 210)

ACCENT = (120, 200, 255)
WALL_COL = (105, 115, 150)
PLAYER_COL = (80, 170, 255)
ENEMY_COL = (255, 90, 90)
EXIT_COL = (90, 255, 140)
ERASE_COL = (150, 150, 160)
CURSOR_COL = (255, 230, 120)

# -----------------------------
# FONTS
# -----------------------------
font_big = pygame.font.SysFont("consolas", 32, bold=True)
font_mid = pygame.font.SysFont("consolas", 22, bold=True)
font_small = pygame.font.SysFont("consolas", 16, bold=False)
font_btn = pygame.font.SysFont("arial", 34, bold=True)

# -----------------------------
# UI LAYOUT
# -----------------------------
LEFT_W = 380
RIGHT_X = LEFT_W
RIGHT_W = WIDTH - LEFT_W

# Grid
CELL = 34
GRID_W = 22
GRID_H = 16

GRID_X = RIGHT_X + 40
GRID_Y = 110
GRID_RECT = pygame.Rect(GRID_X, GRID_Y, GRID_W * CELL, GRID_H * CELL)

# -----------------------------
# BUTTON ANIMATION (your style)
# -----------------------------
BASE_BTN_W, BASE_BTN_H = 260, 120
btn_center = (LEFT_W // 2, 290)

press_amount = 0.0
PRESS_SPEED = 14.0
is_pressing = False
mouse_down_started_on_button = False

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(x, a, b):
    return max(a, min(b, x))

def get_button_rect(press_t: float):
    # Same press feel you had
    scale = lerp(1.0, 0.94, press_t)
    y_offset = lerp(0.0, 10.0, press_t)
    w = int(BASE_BTN_W * scale)
    h = int(BASE_BTN_H * scale)
    rect = pygame.Rect(0, 0, w, h)
    rect.center = (btn_center[0], int(btn_center[1] + y_offset))
    return rect

def draw_button(surf, rect, mouse_pos, press_t, label="PRESS"):
    hovering = rect.collidepoint(mouse_pos)

    if press_t > 0.5:
        color = BTN_PRESSED
    else:
        color = BTN_HOVER if hovering else BTN_RED

    border_radius = 20

    # Shadow
    shadow_offset = int(lerp(8, 4, press_t))
    shadow_rect = rect.copy()
    shadow_rect.y += shadow_offset
    pygame.draw.rect(surf, BTN_SHADOW, shadow_rect, border_radius=border_radius)

    # Button body
    pygame.draw.rect(surf, color, rect, border_radius=border_radius)

    # Gloss highlight
    highlight_alpha = int(lerp(70, 25, press_t))
    highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 3)
    highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
    highlight_surface.fill((255, 255, 255, highlight_alpha))
    surf.blit(highlight_surface, highlight_rect.topleft)

    # Text
    text_surface = font_btn.render(label, True, BTN_TEXT)
    text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery + int(lerp(0, 2, press_t))))
    surf.blit(text_surface, text_rect)

# -----------------------------
# GLOW HELPERS
# -----------------------------
def rounded_rect(surf, rect, color, radius=16, width=0):
    pygame.draw.rect(surf, color, rect, width=width, border_radius=radius)

def soft_glow_circle(surf, pos, base_r, color, layers=6, alpha_start=70):
    for i in range(layers, 0, -1):
        r = base_r + i * 3
        a = int(alpha_start * (i / layers))
        glow = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, a), (r + 1, r + 1), r)
        surf.blit(glow, (pos[0] - r - 1, pos[1] - r - 1))

def soft_glow_rect(surf, rect, color, alpha=70, grow=10, radius=14):
    glow = pygame.Surface((rect.w + grow * 2, rect.h + grow * 2), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*color, alpha), (0, 0, glow.get_width(), glow.get_height()), border_radius=radius)
    surf.blit(glow, (rect.x - grow, rect.y - grow))

# -----------------------------
# GAME DATA
# -----------------------------
EMPTY = 0
WALL = 1
PLAYER = 2
ENEMY = 3
EXIT = 4

TOOLS = [
    (WALL,   "WALL",   WALL_COL),
    (PLAYER, "PLAYER", PLAYER_COL),
    (ENEMY,  "ENEMY",  ENEMY_COL),
    (EXIT,   "EXIT",   EXIT_COL),
    (EMPTY,  "ERASE",  ERASE_COL),
]
tool_index = 0

board = [[EMPTY for _ in range(GRID_W)] for __ in range(GRID_H)]
cursor = [0, 0]  # grid coords

# Modes
MODE_BUILD = 0
MODE_PLAY = 1
mode = MODE_BUILD

# Play runtime
player_pos = None
enemy_positions = []
exit_pos = None
game_state = "READY"  # READY / RUN / WIN / LOSE
sim_accum = 0.0
SIM_STEP = 0.16

def reset_runtime_from_board():
    global player_pos, enemy_positions, exit_pos, game_state, sim_accum
    player_pos = None
    enemy_positions = []
    exit_pos = None
    for y in range(GRID_H):
        for x in range(GRID_W):
            v = board[y][x]
            if v == PLAYER:
                player_pos = (x, y)
            elif v == ENEMY:
                enemy_positions.append((x, y))
            elif v == EXIT:
                exit_pos = (x, y)
    game_state = "READY"
    sim_accum = 0.0

def clear_board():
    global board
    board = [[EMPTY for _ in range(GRID_W)] for __ in range(GRID_H)]
    reset_runtime_from_board()

def place_tool_at_cursor():
    """Place tool with constraints: only 1 player and 1 exit."""
    global board
    tid, _, _ = TOOLS[tool_index]
    x, y = cursor

    if tid == PLAYER:
        for gy in range(GRID_H):
            for gx in range(GRID_W):
                if board[gy][gx] == PLAYER:
                    board[gy][gx] = EMPTY
    if tid == EXIT:
        for gy in range(GRID_H):
            for gx in range(GRID_W):
                if board[gy][gx] == EXIT:
                    board[gy][gx] = EMPTY

    board[y][x] = tid
    reset_runtime_from_board()

def grid_in_bounds(x, y):
    return 0 <= x < GRID_W and 0 <= y < GRID_H

def is_blocked(x, y):
    return (not grid_in_bounds(x, y)) or board[y][x] == WALL

def neighbors4(x, y):
    for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
        nx, ny = x + dx, y + dy
        if grid_in_bounds(nx, ny) and not is_blocked(nx, ny):
            yield (nx, ny)

def bfs_next_step(start, goal):
    """Return next cell from start toward goal. If unreachable, stay."""
    if start is None or goal is None:
        return start
    if start == goal:
        return start

    q = deque([start])
    came = {start: None}

    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nb in neighbors4(cur[0], cur[1]):
            if nb not in came:
                came[nb] = cur
                q.append(nb)

    if goal not in came:
        return start

    cur = goal
    prev = came[cur]
    while prev is not None and prev != start:
        cur = prev
        prev = came[cur]
    return cur

def play_toggle_run():
    global game_state
    if game_state == "READY":
        game_state = "RUN"
    elif game_state == "RUN":
        game_state = "READY"
    else:
        game_state = "READY"

def play_reset():
    reset_runtime_from_board()

def simulate_play_step():
    global player_pos, enemy_positions, game_state
    if player_pos is None or exit_pos is None:
        game_state = "READY"
        return

    # player moves toward exit
    player_pos = bfs_next_step(player_pos, exit_pos)

    # enemies chase player
    enemy_positions = [bfs_next_step(e, player_pos) for e in enemy_positions]

    # lose if touched
    if any(e == player_pos for e in enemy_positions):
        game_state = "LOSE"
        return

    # win if reach exit
    if player_pos == exit_pos:
        game_state = "WIN"
        return

# -----------------------------
# ONE-BUTTON INPUT LANGUAGE
# -----------------------------
DOUBLE_TAP_WINDOW = 0.33
TRIPLE_TAP_WINDOW = 0.75
HOLD_THRESHOLD = 0.38

tap_times = []
pending_single_tap = False
pending_tap_time = 0.0
press_start_time = 0.0

# Hold -> cursor scan
cursor_move_accum = 0.0
CURSOR_STEP_TIME = 0.10  # faster feels better

def register_tap(t):
    tap_times.append(t)
    # keep only taps within triple window
    while tap_times and t - tap_times[0] > TRIPLE_TAP_WINDOW:
        tap_times.pop(0)

def recent_taps(t, window):
    return [x for x in tap_times if t - x <= window]

def move_cursor_scan(dt):
    global cursor_move_accum, cursor
    cursor_move_accum += dt
    while cursor_move_accum >= CURSOR_STEP_TIME:
        cursor_move_accum -= CURSOR_STEP_TIME
        cursor[0] += 1
        if cursor[0] >= GRID_W:
            cursor[0] = 0
            cursor[1] += 1
            if cursor[1] >= GRID_H:
                cursor[1] = 0

def toggle_mode():
    global mode
    mode = MODE_PLAY if mode == MODE_BUILD else MODE_BUILD
    reset_runtime_from_board()

# -----------------------------
# DRAW: LEFT PANEL
# -----------------------------
def draw_left_panel(mouse_pos):
    # panel background
    pygame.draw.rect(screen, PANEL_BG, pygame.Rect(0, 0, LEFT_W, HEIGHT))

    # header
    screen.blit(font_mid.render("THE BUTTON", True, (25, 25, 35)), (26, 18))
    screen.blit(font_small.render("One-button level editor + playtest", True, (90, 90, 105)), (26, 48))

    # mode badge
    badge = pygame.Rect(26, 78, LEFT_W - 52, 46)
    rounded_rect(screen, badge, (235, 235, 242), radius=14)
    rounded_rect(screen, badge, (210, 210, 220), radius=14, width=2)

    mtxt = "BUILD MODE" if mode == MODE_BUILD else "PLAY MODE"
    mcol = (40, 140, 255) if mode == MODE_BUILD else (40, 190, 120)
    screen.blit(font_mid.render(mtxt, True, mcol), (badge.x + 16, badge.y + 10))

    # button
    rect = get_button_rect(press_amount)
    label = "BUILD" if mode == MODE_BUILD else "PLAY"
    draw_button(screen, rect, mouse_pos, press_amount, label=label)

    # controls
    lines = [
        "Tap: cycle tool / start-pause",
        "Double-tap: place / reset",
        "Hold: move cursor (BUILD)",
        "Triple-tap: toggle BUILD/PLAY",
        "",
        "Optional keys:",
        "C = clear level",
        "R = reset play",
    ]
    y = 440
    for ln in lines:
        col = (95, 95, 110) if ln else (95, 95, 110)
        screen.blit(font_small.render(ln, True, col), (26, y))
        y += 20

    return rect

# -----------------------------
# DRAW: RIGHT SIDE (EDITOR)
# -----------------------------
def draw_right_side():
    # background
    screen.fill(BG, rect=pygame.Rect(RIGHT_X, 0, RIGHT_W, HEIGHT))

    # top bar
    top = pygame.Rect(RIGHT_X + 20, 18, RIGHT_W - 40, 56)
    rounded_rect(screen, top, TOP_BAR, radius=18)
    rounded_rect(screen, top, TOP_BORDER, radius=18, width=2)
    screen.blit(font_big.render("ONE-BUTTON GAME MAKER", True, TEXT_MAIN), (RIGHT_X + 40, 30))

    # tool info
    tid, tname, tcol = TOOLS[tool_index]
    tool_box = pygame.Rect(RIGHT_X + 760, 26, RIGHT_W - 820, 40)
    rounded_rect(screen, tool_box, (35, 40, 58), radius=14)
    rounded_rect(screen, tool_box, tcol, radius=14, width=2)
    screen.blit(font_mid.render(f"TOOL: {tname}", True, tcol), (tool_box.x + 14, tool_box.y + 9))

    # grid frame
    frame = GRID_RECT.inflate(24, 24)
    rounded_rect(screen, frame, (22, 25, 36), radius=18)
    rounded_rect(screen, frame, (70, 80, 110), radius=18, width=2)

    # draw grid cells
    t = time.time()
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            v = board[gy][gx]
            x = GRID_RECT.x + gx * CELL
            y = GRID_RECT.y + gy * CELL
            cellr = pygame.Rect(x, y, CELL, CELL)

            pygame.draw.rect(screen, GRID_BG, cellr)
            pygame.draw.rect(screen, GRID_LINE, cellr, 1)

            if v == WALL:
                rounded_rect(screen, cellr.inflate(-6, -6), WALL_COL, radius=8)
            elif v == EXIT:
                cx, cy = cellr.center
                soft_glow_circle(screen, (cx, cy), 12, EXIT_COL, layers=7, alpha_start=75)
                pygame.draw.circle(screen, EXIT_COL, (cx, cy), 12)
            elif v == PLAYER:
                cx, cy = cellr.center
                soft_glow_circle(screen, (cx, cy), 12, PLAYER_COL, layers=7, alpha_start=75)
                pygame.draw.circle(screen, PLAYER_COL, (cx, cy), 12)
            elif v == ENEMY:
                cx, cy = cellr.center
                soft_glow_circle(screen, (cx, cy), 11, ENEMY_COL, layers=6, alpha_start=70)
                pygame.draw.circle(screen, ENEMY_COL, (cx, cy), 11)

    # cursor highlight
    cx, cy = cursor
    cur_cell = pygame.Rect(GRID_RECT.x + cx * CELL, GRID_RECT.y + cy * CELL, CELL, CELL)
    pulse = (math.sin(t * 6.0) + 1.0) * 0.5
    soft_glow_rect(screen, cur_cell, CURSOR_COL, alpha=int(80 * pulse), grow=10, radius=12)
    pygame.draw.rect(screen, CURSOR_COL, cur_cell, 3, border_radius=8)

    # play runtime overlay
    if mode == MODE_PLAY:
        draw_runtime_entities()

    # status line
    status_rect = pygame.Rect(GRID_RECT.x, GRID_RECT.bottom + 18, GRID_RECT.w, 46)
    rounded_rect(screen, status_rect, (22, 26, 38), radius=16)
    rounded_rect(screen, status_rect, (60, 70, 95), radius=16, width=2)

    if mode == MODE_BUILD:
        msg = "BUILD: Tap=cycle tool • Double-tap=place • Hold=move cursor • Triple-tap=PLAY"
    else:
        if player_pos is None or exit_pos is None:
            msg = "PLAY: Place a PLAYER and an EXIT first. Triple-tap back to BUILD."
        elif game_state == "RUN":
            msg = "RUNNING... Tap=pause • Double-tap=reset • Triple-tap=BUILD"
        elif game_state == "WIN":
            msg = "YOU WIN! Double-tap=reset • Triple-tap=BUILD"
        elif game_state == "LOSE":
            msg = "YOU DIED! Double-tap=reset • Triple-tap=BUILD"
        else:
            msg = "PLAY READY: Tap=start • Double-tap=reset • Triple-tap=BUILD"

    screen.blit(font_small.render(msg, True, TEXT_DIM), (status_rect.x + 16, status_rect.y + 15))

def draw_runtime_entities():
    if player_pos is None:
        return

    # enemies first
    for ex, ey in enemy_positions:
        cellr = pygame.Rect(GRID_RECT.x + ex * CELL, GRID_RECT.y + ey * CELL, CELL, CELL)
        cx, cy = cellr.center
        soft_glow_circle(screen, (cx, cy), 11, ENEMY_COL, layers=8, alpha_start=85)
        pygame.draw.circle(screen, ENEMY_COL, (cx, cy), 11)

    px, py = player_pos
    cellr = pygame.Rect(GRID_RECT.x + px * CELL, GRID_RECT.y + py * CELL, CELL, CELL)
    cx, cy = cellr.center
    soft_glow_circle(screen, (cx, cy), 12, PLAYER_COL, layers=10, alpha_start=95)
    pygame.draw.circle(screen, PLAYER_COL, (cx, cy), 12)

# -----------------------------
# MAIN LOOP
# -----------------------------
reset_runtime_from_board()

while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    # Current button rect for hit test
    btn_rect = get_button_rect(press_amount)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Optional keyboard helpers
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                clear_board()
            elif event.key == pygame.K_r:
                play_reset()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Only count as "the button" if click started on the button rect
            if btn_rect.collidepoint(event.pos):
                is_pressing = True
                mouse_down_started_on_button = True
                press_start_time = time.time()
            else:
                mouse_down_started_on_button = False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if is_pressing and mouse_down_started_on_button:
                is_pressing = False
                mouse_down_started_on_button = False

                now = time.time()
                dur = now - press_start_time

                # HOLD just moves cursor continuously, no "release action"
                if dur < HOLD_THRESHOLD:
                    # TAP registered
                    register_tap(now)

                    # TRIPLE TAP => toggle mode immediately
                    if len(recent_taps(now, TRIPLE_TAP_WINDOW)) >= 3:
                        tap_times.clear()
                        pending_single_tap = False
                        toggle_mode()
                    else:
                        # wait to resolve single vs double
                        pending_single_tap = True
                        pending_tap_time = now
            else:
                is_pressing = False
                mouse_down_started_on_button = False

    # Animate press
    target = 1.0 if is_pressing else 0.0
    press_amount = lerp(press_amount, target, min(1.0, PRESS_SPEED * dt))

    # Hold moves cursor in BUILD mode (only while actually holding the button)
    if is_pressing and mode == MODE_BUILD:
        move_cursor_scan(dt)

    # Resolve single vs double tap
    if pending_single_tap:
        now = time.time()
        if len(recent_taps(now, DOUBLE_TAP_WINDOW)) >= 2:
            # DOUBLE TAP
            tap_times.clear()
            pending_single_tap = False

            if mode == MODE_BUILD:
                place_tool_at_cursor()
            else:
                play_reset()
        elif now - pending_tap_time > DOUBLE_TAP_WINDOW:
            # SINGLE TAP
            pending_single_tap = False

            if mode == MODE_BUILD:
                tool_index = (tool_index + 1) % len(TOOLS)
            else:
                play_toggle_run()

    # Simulate play
    if mode == MODE_PLAY and game_state == "RUN":
        sim_accum += dt
        while sim_accum >= SIM_STEP and game_state == "RUN":
            sim_accum -= SIM_STEP
            simulate_play_step()

    # -----------------------------
    # DRAW
    # -----------------------------
    # Right side first (background)
    draw_right_side()

    # Left panel on top
    draw_left_panel(mouse_pos)

    pygame.display.flip()