import sys
import math
import time
import pygame

# True multi-window uses pygame._sdl2 (Pygame 2)
try:
    import pygame._sdl2 as sdl2
except Exception:
    print("This program needs pygame._sdl2 (Pygame 2) for true multi-window support.")
    print("Install/upgrade with: pip install -U pygame")
    sys.exit(1)

pygame.init()
pygame.font.init()

# -----------------------------
# THEME / COLORS
# -----------------------------
# Button window theme
BTN_BG = (245, 245, 248)
BTN_RED = (210, 40, 40)
BTN_HOVER = (240, 70, 70)
BTN_PRESSED = (190, 25, 25)
BTN_SHADOW = (150, 20, 20)
BTN_TEXT = (255, 255, 255)

# Board window theme (neon-dark)
BOARD_BG = (16, 18, 26)
BOARD_GRID = (30, 34, 48)
PANEL_BG = (25, 28, 40)
PANEL_BORDER = (70, 80, 110)
TEXT_MAIN = (240, 240, 255)
TEXT_DIM = (170, 175, 210)

ACCENT = (120, 200, 255)   # cyan
ACCENT2 = (255, 120, 170)  # pink

WALL_COL = (100, 110, 140)
PLAYER_COL = (80, 170, 255)
ENEMY_COL = (255, 90, 90)
EXIT_COL = (90, 255, 140)
ERASE_COL = (130, 130, 130)

# -----------------------------
# FONTS
# -----------------------------
font_btn = pygame.font.SysFont("arial", 34, bold=True)
font_big = pygame.font.SysFont("consolas", 32, bold=True)
font_mid = pygame.font.SysFont("consolas", 22, bold=True)
font_small = pygame.font.SysFont("consolas", 16, bold=False)

# -----------------------------
# WINDOWS
# -----------------------------
BTN_W, BTN_H = 420, 520
BOARD_W, BOARD_H = 1100, 740

button_win = sdl2.Window("THE BUTTON", size=(BTN_W, BTN_H), position=(80, 80))
board_win = sdl2.Window("ONE-BUTTON GAME MAKER", size=(BOARD_W, BOARD_H), position=(540, 60))

btn_renderer = sdl2.Renderer(button_win)
board_renderer = sdl2.Renderer(board_win)

btn_surface = pygame.Surface((BTN_W, BTN_H), pygame.SRCALPHA)
board_surface = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)

BTN_ID = button_win.id
BOARD_ID = board_win.id

def renderer_present_surface(renderer, surface, w, h):
    """Present a pygame Surface into an SDL2 renderer (robust across pygame builds)."""
    tex = sdl2.Texture.from_surface(renderer, surface)
    if hasattr(renderer, "clear"):
        renderer.clear()

    # Your pygame build wants destination rect positionally (no keyword).
    try:
        renderer.blit(tex, (0, 0, w, h))
    except TypeError:
        # Other builds may accept keyword variants
        try:
            renderer.blit(tex, dstrect=(0, 0, w, h))
        except TypeError:
            renderer.blit(tex, dest=(0, 0, w, h))

    renderer.present()
    tex.destroy()

# -----------------------------
# UTILS
# -----------------------------
def lerp(a, b, t):
    return a + (b - a) * t

def clamp(x, a, b):
    return max(a, min(b, x))

def rounded_rect(surf, rect, color, radius=16, width=0):
    pygame.draw.rect(surf, color, rect, width=width, border_radius=radius)

def soft_glow_circle(surf, pos, base_r, color, layers=6, alpha_start=60):
    for i in range(layers, 0, -1):
        r = base_r + i * 3
        a = int(alpha_start * (i / layers))
        glow = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color, a), (r + 1, r + 1), r)
        surf.blit(glow, (pos[0] - r - 1, pos[1] - r - 1))

def draw_grid_background(surf):
    surf.fill(BOARD_BG)
    step = 24
    for x in range(0, BOARD_W, step):
        pygame.draw.line(surf, (20, 22, 32), (x, 0), (x, BOARD_H))
    for y in range(0, BOARD_H, step):
        pygame.draw.line(surf, (20, 22, 32), (0, y), (BOARD_W, y))

# -----------------------------
# BUTTON ANIMATION (your style)
# -----------------------------
BASE_BTN_W, BASE_BTN_H = 260, 120
btn_center = (BTN_W // 2, BTN_H // 2 + 30)

press_amount = 0.0
PRESS_SPEED = 14.0
is_pressing = False

def get_button_rect(press_t: float):
    scale = lerp(1.0, 0.94, press_t)
    y_offset = lerp(0.0, 10.0, press_t)
    w = int(BASE_BTN_W * scale)
    h = int(BASE_BTN_H * scale)
    rect = pygame.Rect(0, 0, w, h)
    rect.center = (btn_center[0], int(btn_center[1] + y_offset))
    return rect

def draw_button_ui(surf, mouse_pos, press_t, label="PRESS"):
    surf.fill(BTN_BG)

    title = font_mid.render("ONE BUTTON", True, (30, 30, 40))
    surf.blit(title, (24, 18))
    subtitle = font_small.render("Tap / Double Tap / Hold", True, (90, 90, 105))
    surf.blit(subtitle, (24, 48))

    rect = get_button_rect(press_t)
    hovering = rect.collidepoint(mouse_pos)

    if press_t > 0.5:
        color = BTN_PRESSED
    else:
        color = BTN_HOVER if hovering else BTN_RED

    border_radius = 20

    shadow_offset = int(lerp(8, 4, press_t))
    shadow_rect = rect.copy()
    shadow_rect.y += shadow_offset
    pygame.draw.rect(surf, BTN_SHADOW, shadow_rect, border_radius=border_radius)

    pygame.draw.rect(surf, color, rect, border_radius=border_radius)

    highlight_alpha = int(lerp(70, 25, press_t))
    highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 3)
    highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
    highlight_surface.fill((255, 255, 255, highlight_alpha))
    surf.blit(highlight_surface, highlight_rect.topleft)

    text_surface = font_btn.render(label, True, BTN_TEXT)
    text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery + int(lerp(0, 2, press_t))))
    surf.blit(text_surface, text_rect)

    hints = [
        "Tap: cycle tool",
        "Double-tap: place / reset",
        "Hold: move cursor (BUILD)",
        "Triple-tap: BUILD / PLAY",
        "Optional: C clear, R reset play",
    ]
    y = BTN_H - 150
    for h in hints:
        s = font_small.render(h, True, (85, 85, 100))
        surf.blit(s, (24, y))
        y += 22

    return rect

# -----------------------------
# GAME MAKER (board window)
# -----------------------------
CELL = 34
GRID_W = 24
GRID_H = 18
GRID_X = 30
GRID_Y = 90

EMPTY = 0
WALL = 1
PLAYER = 2
ENEMY = 3
EXIT = 4

TOOLS = [
    (WALL, "WALL", WALL_COL),
    (PLAYER, "PLAYER", PLAYER_COL),
    (ENEMY, "ENEMY", ENEMY_COL),
    (EXIT, "EXIT", EXIT_COL),
    (EMPTY, "ERASE", ERASE_COL),
]
tool_index = 0

board = [[EMPTY for _ in range(GRID_W)] for __ in range(GRID_H)]
cursor = [0, 0]

cursor_move_accum = 0.0
CURSOR_STEP_TIME = 0.12

MODE_BUILD = 0
MODE_PLAY = 1
mode = MODE_BUILD

player_pos = None
enemy_positions = []
exit_pos = None

game_state = "READY"  # READY / RUN / WIN / LOSE
sim_accum = 0.0
SIM_STEP = 0.16

def reset_level_runtime_from_board():
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
    reset_level_runtime_from_board()

def grid_in_bounds(x, y):
    return 0 <= x < GRID_W and 0 <= y < GRID_H

def is_blocked(x, y):
    return (not grid_in_bounds(x, y)) or board[y][x] == WALL

def neighbors4(x, y):
    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
        nx, ny = x + dx, y + dy
        if grid_in_bounds(nx, ny) and not is_blocked(nx, ny):
            yield (nx, ny)

def bfs_next_step(start, goal):
    if start is None or goal is None:
        return start
    if start == goal:
        return start

    from collections import deque
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

def draw_board_window(surf):
    draw_grid_background(surf)

    # Top bar
    rounded_rect(surf, pygame.Rect(20, 18, BOARD_W - 40, 56), PANEL_BG, radius=18)
    rounded_rect(surf, pygame.Rect(20, 18, BOARD_W - 40, 56), PANEL_BORDER, radius=18, width=2)
    surf.blit(font_big.render("ONE-BUTTON GAME MAKER", True, TEXT_MAIN), (40, 30))

    mode_txt = "BUILD" if mode == MODE_BUILD else "PLAY"
    mode_col = ACCENT if mode == MODE_BUILD else EXIT_COL
    mode_badge = pygame.Rect(BOARD_W - 180, 26, 140, 40)
    rounded_rect(surf, mode_badge, (35, 40, 58), radius=14)
    rounded_rect(surf, mode_badge, mode_col, radius=14, width=2)
    surf.blit(font_mid.render(mode_txt, True, mode_col), (mode_badge.x + 34, mode_badge.y + 9))

    # Tool panel
    panel = pygame.Rect(20, 90, 260, BOARD_H - 110)
    rounded_rect(surf, panel, PANEL_BG, radius=18)
    rounded_rect(surf, panel, PANEL_BORDER, radius=18, width=2)

    surf.blit(font_mid.render("TOOLS", True, TEXT_MAIN), (40, 110))
    surf.blit(font_small.render("Tap to cycle • Double-tap to place", True, TEXT_DIM), (40, 140))

    y = 175
    for i, (_, name, col) in enumerate(TOOLS):
        r = pygame.Rect(40, y, 220, 44)
        selected = (i == tool_index)
        rounded_rect(surf, r, (32, 36, 52) if selected else (28, 32, 46), radius=14)
        if selected:
            rounded_rect(surf, r, col, radius=14, width=2)

        icon_center = (r.x + 22, r.y + 22)
        soft_glow_circle(surf, icon_center, 10, col, layers=5, alpha_start=55)
        pygame.draw.circle(surf, col, icon_center, 10)

        surf.blit(font_mid.render(name, True, TEXT_MAIN), (r.x + 48, r.y + 10))
        y += 56

    # Grid
    grid_rect = pygame.Rect(GRID_X + 280, GRID_Y, GRID_W * CELL, GRID_H * CELL)
    rounded_rect(surf, pygame.Rect(grid_rect.x - 10, grid_rect.y - 10, grid_rect.w + 20, grid_rect.h + 20),
                 (22, 25, 36), radius=18)
    rounded_rect(surf, pygame.Rect(grid_rect.x - 10, grid_rect.y - 10, grid_rect.w + 20, grid_rect.h + 20),
                 (70, 80, 110), radius=18, width=2)

    t = time.time()
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            v = board[gy][gx]
            x = grid_rect.x + gx * CELL
            y = grid_rect.y + gy * CELL
            cellr = pygame.Rect(x, y, CELL, CELL)

            pygame.draw.rect(surf, BOARD_GRID, cellr)
            pygame.draw.rect(surf, (25, 28, 42), cellr, 1)

            if v == WALL:
                rounded_rect(surf, cellr.inflate(-6, -6), WALL_COL, radius=8)
            elif v == EXIT:
                cx, cy = cellr.center
                soft_glow_circle(surf, (cx, cy), 12, EXIT_COL, layers=7, alpha_start=70)
                pygame.draw.circle(surf, EXIT_COL, (cx, cy), 12)
            elif v == PLAYER:
                cx, cy = cellr.center
                soft_glow_circle(surf, (cx, cy), 12, PLAYER_COL, layers=7, alpha_start=70)
                pygame.draw.circle(surf, PLAYER_COL, (cx, cy), 12)
            elif v == ENEMY:
                cx, cy = cellr.center
                soft_glow_circle(surf, (cx, cy), 11, ENEMY_COL, layers=6, alpha_start=65)
                pygame.draw.circle(surf, ENEMY_COL, (cx, cy), 11)

    # Cursor highlight
    cx, cy = cursor
    cur_cell = pygame.Rect(grid_rect.x + cx * CELL, grid_rect.y + cy * CELL, CELL, CELL)
    pulse = (math.sin(t * 6.0) + 1.0) * 0.5
    glow_col = (255, 230, 120)

    glow = pygame.Surface((cur_cell.w + 24, cur_cell.h + 24), pygame.SRCALPHA)
    pygame.draw.rect(glow, (*glow_col, int(70 * pulse)), (0, 0, glow.get_width(), glow.get_height()), border_radius=12)
    surf.blit(glow, (cur_cell.x - 12, cur_cell.y - 12))
    pygame.draw.rect(surf, glow_col, cur_cell, 3, border_radius=8)

    # Play status line (small)
    if mode == MODE_PLAY:
        status = "Tap = start/pause • Double-tap = reset • Triple-tap = back to BUILD"
        if game_state == "WIN":
            status = "YOU WIN! Double-tap reset • Triple-tap back to BUILD"
        elif game_state == "LOSE":
            status = "YOU DIED! Double-tap reset • Triple-tap back to BUILD"
        surf.blit(font_small.render(status, True, TEXT_DIM), (grid_rect.x, grid_rect.bottom + 18))

def place_tool_at_cursor():
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
    reset_level_runtime_from_board()

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
    reset_level_runtime_from_board()

def play_reset():
    reset_level_runtime_from_board()

def play_toggle_run():
    global game_state
    if game_state == "READY":
        game_state = "RUN"
    elif game_state == "RUN":
        game_state = "READY"
    else:
        game_state = "READY"

def simulate_play_step():
    global player_pos, enemy_positions, game_state
    if player_pos is None or exit_pos is None:
        game_state = "READY"
        return

    player_pos = bfs_next_step(player_pos, exit_pos)
    enemy_positions = [bfs_next_step(e, player_pos) for e in enemy_positions]

    if any(e == player_pos for e in enemy_positions):
        game_state = "LOSE"
        return
    if player_pos == exit_pos:
        game_state = "WIN"
        return

def draw_runtime_entities_on_grid(surf):
    if mode != MODE_PLAY or player_pos is None:
        return
    grid_rect = pygame.Rect(GRID_X + 280, GRID_Y, GRID_W * CELL, GRID_H * CELL)

    for ex, ey in enemy_positions:
        cellr = pygame.Rect(grid_rect.x + ex * CELL, grid_rect.y + ey * CELL, CELL, CELL)
        cx, cy = cellr.center
        soft_glow_circle(surf, (cx, cy), 11, ENEMY_COL, layers=7, alpha_start=80)
        pygame.draw.circle(surf, ENEMY_COL, (cx, cy), 11)

    px, py = player_pos
    cellr = pygame.Rect(grid_rect.x + px * CELL, grid_rect.y + py * CELL, CELL, CELL)
    cx, cy = cellr.center
    soft_glow_circle(surf, (cx, cy), 12, PLAYER_COL, layers=9, alpha_start=90)
    pygame.draw.circle(surf, PLAYER_COL, (cx, cy), 12)

# -----------------------------
# ONE-BUTTON INPUT LANGUAGE
# -----------------------------
DOUBLE_TAP_WINDOW = 0.33
TRIPLE_TAP_WINDOW = 0.75
HOLD_THRESHOLD = 0.38

btn_mouse_pos = (0, 0)
press_start_time = 0.0
tap_times = []

pending_single_tap = False
pending_tap_time = 0.0

def register_tap(t):
    tap_times.append(t)
    while tap_times and t - tap_times[0] > TRIPLE_TAP_WINDOW:
        tap_times.pop(0)

def recent_taps(t, window):
    return [x for x in tap_times if t - x <= window]

# -----------------------------
# MAIN LOOP
# -----------------------------
running = True
last_time = time.time()

reset_level_runtime_from_board()

while running:
    now = time.time()
    dt = clamp(now - last_time, 0.0, 0.05)
    last_time = now

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Optional keyboard helpers (not required)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                clear_board()
            elif event.key == pygame.K_r:
                play_reset()

        if event.type == pygame.MOUSEMOTION:
            wid = getattr(event, "window", None)
            if wid is None:
                wid = getattr(event, "windowID", None)
            if wid == BTN_ID:
                btn_mouse_pos = event.pos

        # One-button presses ONLY from the button window
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            wid = getattr(event, "window", None)
            if wid is None:
                wid = getattr(event, "windowID", None)
            if wid == BTN_ID:
                rect = get_button_rect(press_amount)
                if rect.collidepoint(event.pos):
                    is_pressing = True
                    press_start_time = now

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            wid = getattr(event, "window", None)
            if wid is None:
                wid = getattr(event, "windowID", None)
            if wid == BTN_ID and is_pressing:
                is_pressing = False
                dur = now - press_start_time

                if dur < HOLD_THRESHOLD:
                    register_tap(now)

                    # Triple tap -> toggle mode
                    if len(recent_taps(now, TRIPLE_TAP_WINDOW)) >= 3:
                        tap_times.clear()
                        pending_single_tap = False
                        toggle_mode()
                    else:
                        pending_single_tap = True
                        pending_tap_time = now

    # Animate button
    target = 1.0 if is_pressing else 0.0
    press_amount = lerp(press_amount, target, min(1.0, PRESS_SPEED * dt))

    # Holding moves cursor in BUILD mode
    if is_pressing and mode == MODE_BUILD:
        move_cursor_scan(dt)

    # Resolve single vs double
    if pending_single_tap:
        if len(recent_taps(now, DOUBLE_TAP_WINDOW)) >= 2:
            tap_times.clear()
            pending_single_tap = False
            if mode == MODE_BUILD:
                place_tool_at_cursor()
            else:
                play_reset()
        elif now - pending_tap_time > DOUBLE_TAP_WINDOW:
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

    # Draw button window
    btn_label = "BUILD" if mode == MODE_BUILD else "PLAY"
    draw_button_ui(btn_surface, btn_mouse_pos, press_amount, label=btn_label)
    renderer_present_surface(btn_renderer, btn_surface, BTN_W, BTN_H)

    # Draw board window
    draw_board_window(board_surface)
    draw_runtime_entities_on_grid(board_surface)
    renderer_present_surface(board_renderer, board_surface, BOARD_W, BOARD_H)

    pygame.time.delay(10)

pygame.quit()
sys.exit(0)