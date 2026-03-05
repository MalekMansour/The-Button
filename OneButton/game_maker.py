import pygame
import sys
import time
import math

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
# THEME
# -----------------------------
BG = (16, 18, 26)
PANEL_BG = (245, 245, 248)

GRID_BG = (30, 34, 48)
GRID_LINE = (25, 28, 42)

TOP_BAR = (25, 28, 40)
TOP_BORDER = (70, 80, 110)

TEXT_MAIN = (240, 240, 255)
TEXT_DIM = (170, 175, 210)

# Button colors (your style)
BTN_RED = (210, 40, 40)
BTN_HOVER = (240, 70, 70)
BTN_PRESSED = (190, 25, 25)
BTN_SHADOW = (150, 20, 20)
BTN_TEXT = (255, 255, 255)

# Tiles
WALL_COL = (105, 115, 150)
OBST_COL = (155, 140, 95)
ENEMY_COL = (255, 90, 90)
DOOR_COL = (190, 140, 255)
KEY_COL = (255, 220, 80)

PLAYER_COL = (80, 170, 255)
EXIT_COL = (90, 255, 140)

CURSOR_COL = (255, 230, 120)

# -----------------------------
# FONTS
# -----------------------------
font_big = pygame.font.SysFont("consolas", 32, bold=True)
font_mid = pygame.font.SysFont("consolas", 22, bold=True)
font_small = pygame.font.SysFont("consolas", 16, bold=False)
font_btn = pygame.font.SysFont("arial", 34, bold=True)

# -----------------------------
# LAYOUT
# -----------------------------
LEFT_W = 380
RIGHT_X = LEFT_W
RIGHT_W = WIDTH - LEFT_W

CELL = 34
GRID_W = 22
GRID_H = 16

GRID_X = RIGHT_X + 40
GRID_Y = 110
GRID_RECT = pygame.Rect(GRID_X, GRID_Y, GRID_W * CELL, GRID_H * CELL)

# -----------------------------
# TILE TYPES
# -----------------------------
EMPTY = 0
WALL = 1
OBSTACLE = 2
ENEMY = 3
DOOR = 4
KEY = 5

# Placement cycle (right click)
PLACE_ORDER = [
    (WALL, "WALL", WALL_COL),
    (OBSTACLE, "OBSTACLE", OBST_COL),
    (ENEMY, "MOVING ENEMY", ENEMY_COL),
    (DOOR, "DOOR", DOOR_COL),
    (KEY, "KEY", KEY_COL),
]
place_index = 0

# Board
board = [[EMPTY for _ in range(GRID_W)] for __ in range(GRID_H)]

# Start / Exit fixed
START = (0, 0)
EXIT = (GRID_W - 1, GRID_H - 1)

# Cursor (yellow selection)
cursor = [0, 0]

# -----------------------------
# BUTTON ANIMATION (your exact vibe)
# -----------------------------
BASE_BTN_W, BASE_BTN_H = 260, 120
btn_center = (LEFT_W // 2, 290)

press_amount = 0.0
PRESS_SPEED = 14.0
is_pressing = False
mouse_down_started_on_button = False
press_start_time = 0.0

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(x, a, b):
    return max(a, min(b, x))

def get_button_rect(press_t: float):
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

# -----------------------------
# GLOW HELPERS
# -----------------------------
def rounded_rect(surf, rect, color, radius=16, width=0):
    pygame.draw.rect(surf, color, rect, width=width, border_radius=radius)

def soft_glow_circle(surf, pos, base_r, color, layers=7, alpha_start=85):
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
# INPUT LANGUAGE (as you described)
# -----------------------------
DOUBLE_WINDOW = 0.33
TRIPLE_WINDOW = 0.75
HOLD_THRESHOLD = 0.40

tap_times = []            # timestamps of LMB taps
pending_single = False
pending_time = 0.0

# For "hold on 2nd click" / "hold on 3rd click"
last_release_duration = 0.0

# Auto-move modes
auto_dx = 0
auto_dy = 0
auto_accum = 0.0
AUTO_STEP_TIME = 0.10

def record_tap(t):
    tap_times.append(t)
    while tap_times and (t - tap_times[0]) > TRIPLE_WINDOW:
        tap_times.pop(0)

def recent_count(t, window):
    return sum(1 for x in tap_times if (t - x) <= window)

def stop_auto_move():
    global auto_dx, auto_dy
    auto_dx, auto_dy = 0, 0

def move_cursor(dx, dy):
    cursor[0] = clamp(cursor[0] + dx, 0, GRID_W - 1)
    cursor[1] = clamp(cursor[1] + dy, 0, GRID_H - 1)

# -----------------------------
# BUILD / PLAY
# -----------------------------
MODE_BUILD = 0
MODE_PLAY = 1
mode = MODE_BUILD

# Player/enemy runtime state
player_cell = list(START)
has_key = False
game_over = None  # None / "WIN" / "LOSE"

# Enemies runtime (positions + velocities)
enemy_runtime = []  # list of dicts: {"x": int, "y": int, "vx": int, "vy": int}

def rebuild_enemies_from_board():
    """Create runtime enemies from ENEMY tiles."""
    enemy_runtime.clear()
    for y in range(GRID_H):
        for x in range(GRID_W):
            if board[y][x] == ENEMY:
                # simple default movement: horizontal
                enemy_runtime.append({"x": x, "y": y, "vx": 1, "vy": 0})

def reset_play_state():
    global player_cell, has_key, game_over
    player_cell = [START[0], START[1]]
    has_key = False
    game_over = None
    rebuild_enemies_from_board()

def is_solid_for_player(x, y):
    if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
        return True
    t = board[y][x]
    if t == WALL or t == OBSTACLE:
        return True
    if t == DOOR and not has_key:
        return True
    return False

def toggle_play():
    global mode
    if mode == MODE_BUILD:
        mode = MODE_PLAY
        reset_play_state()
        stop_auto_move()
    else:
        mode = MODE_BUILD
        stop_auto_move()

def place_at_cursor():
    """Left click once places current tile at cursor. Can't overwrite start/exit."""
    global board
    cx, cy = cursor
    if (cx, cy) == START or (cx, cy) == EXIT:
        return

    tid, _, _ = PLACE_ORDER[place_index]
    board[cy][cx] = tid

def cycle_place():
    global place_index
    place_index = (place_index + 1) % len(PLACE_ORDER)

# -----------------------------
# DRAW
# -----------------------------
def draw_left_panel(mouse_pos):
    pygame.draw.rect(screen, PANEL_BG, pygame.Rect(0, 0, LEFT_W, HEIGHT))

    screen.blit(font_mid.render("THE BUTTON", True, (25, 25, 35)), (26, 18))
    screen.blit(font_small.render("Build a maze, then press P to play.", True, (90, 90, 105)), (26, 48))

    badge = pygame.Rect(26, 78, LEFT_W - 52, 46)
    rounded_rect(screen, badge, (235, 235, 242), radius=14)
    rounded_rect(screen, badge, (210, 210, 220), radius=14, width=2)

    mtxt = "BUILD MODE" if mode == MODE_BUILD else "PLAY MODE"
    mcol = (40, 140, 255) if mode == MODE_BUILD else (40, 190, 120)
    screen.blit(font_mid.render(mtxt, True, mcol), (badge.x + 16, badge.y + 10))

    rect = get_button_rect(press_amount)
    label = "BUILD" if mode == MODE_BUILD else "PLAY"
    draw_button(screen, rect, mouse_pos, press_amount, label=label)

    tid, name, col = PLACE_ORDER[place_index]
    tool_box = pygame.Rect(26, 390, LEFT_W - 52, 62)
    rounded_rect(screen, tool_box, (235, 235, 242), radius=14)
    rounded_rect(screen, tool_box, col, radius=14, width=2)
    screen.blit(font_mid.render("PLACE:", True, (35, 35, 45)), (tool_box.x + 14, tool_box.y + 10))
    screen.blit(font_mid.render(name, True, col), (tool_box.x + 110, tool_box.y + 10))

    # Controls (exact ones you wrote)
    lines = [
        "Left click: PLACE (cursor)",
        "Right click: change tile",
        "",
        "Double-tap: 1 step RIGHT",
        "Double-tap + HOLD: auto LEFT",
        "Triple-tap: 1 step DOWN",
        "Triple-tap + HOLD: auto UP",
        "",
        "P: Play / Build toggle",
        "",
        "Start: top-left",
        "Exit: bottom-right",
    ]
    y = 470
    for ln in lines:
        screen.blit(font_small.render(ln, True, (95, 95, 110)), (26, y))
        y += 20

    return rect

def draw_right_side():
    # background
    pygame.draw.rect(screen, BG, pygame.Rect(RIGHT_X, 0, RIGHT_W, HEIGHT))

    # top bar
    top = pygame.Rect(RIGHT_X + 20, 18, RIGHT_W - 40, 56)
    rounded_rect(screen, top, TOP_BAR, radius=18)
    rounded_rect(screen, top, TOP_BORDER, radius=18, width=2)
    screen.blit(font_big.render("ONE-BUTTON GAME MAKER", True, TEXT_MAIN), (RIGHT_X + 40, 30))

    # frame
    frame = GRID_RECT.inflate(24, 24)
    rounded_rect(screen, frame, (22, 25, 36), radius=18)
    rounded_rect(screen, frame, (70, 80, 110), radius=18, width=2)

    # draw tiles
    for gy in range(GRID_H):
        for gx in range(GRID_W):
            x = GRID_RECT.x + gx * CELL
            y = GRID_RECT.y + gy * CELL
            cellr = pygame.Rect(x, y, CELL, CELL)

            pygame.draw.rect(screen, GRID_BG, cellr)
            pygame.draw.rect(screen, GRID_LINE, cellr, 1)

            t = board[gy][gx]
            if t == WALL:
                rounded_rect(screen, cellr.inflate(-6, -6), WALL_COL, radius=8)
            elif t == OBSTACLE:
                rounded_rect(screen, cellr.inflate(-6, -6), OBST_COL, radius=8)
            elif t == DOOR:
                rounded_rect(screen, cellr.inflate(-8, -8), DOOR_COL, radius=8)
            elif t == KEY:
                cx, cy = cellr.center
                soft_glow_circle(screen, (cx, cy), 10, KEY_COL, layers=7, alpha_start=85)
                pygame.draw.circle(screen, KEY_COL, (cx, cy), 10)
            elif t == ENEMY:
                cx, cy = cellr.center
                soft_glow_circle(screen, (cx, cy), 11, ENEMY_COL, layers=7, alpha_start=85)
                pygame.draw.circle(screen, ENEMY_COL, (cx, cy), 11)

    # start + exit always
    # start (player spawn)
    sx, sy = START
    start_rect = pygame.Rect(GRID_RECT.x + sx * CELL, GRID_RECT.y + sy * CELL, CELL, CELL)
    scx, scy = start_rect.center
    soft_glow_circle(screen, (scx, scy), 12, PLAYER_COL, layers=8, alpha_start=90)
    pygame.draw.circle(screen, PLAYER_COL, (scx, scy), 12)

    # exit
    ex, ey = EXIT
    exit_rect = pygame.Rect(GRID_RECT.x + ex * CELL, GRID_RECT.y + ey * CELL, CELL, CELL)
    ecx, ecy = exit_rect.center
    soft_glow_circle(screen, (ecx, ecy), 12, EXIT_COL, layers=9, alpha_start=95)
    pygame.draw.circle(screen, EXIT_COL, (ecx, ecy), 12)

    # cursor highlight (only in build)
    if mode == MODE_BUILD:
        cx, cy = cursor
        cur_cell = pygame.Rect(GRID_RECT.x + cx * CELL, GRID_RECT.y + cy * CELL, CELL, CELL)
        pulse = (math.sin(time.time() * 6.0) + 1.0) * 0.5
        soft_glow_rect(screen, cur_cell, CURSOR_COL, alpha=int(80 * pulse), grow=10, radius=12)
        pygame.draw.rect(screen, CURSOR_COL, cur_cell, 3, border_radius=8)

    # play overlay
    if mode == MODE_PLAY:
        draw_play_overlay()

def draw_play_overlay():
    # enemies
    for e in enemy_runtime:
        cellr = pygame.Rect(GRID_RECT.x + e["x"] * CELL, GRID_RECT.y + e["y"] * CELL, CELL, CELL)
        cx, cy = cellr.center
        soft_glow_circle(screen, (cx, cy), 11, ENEMY_COL, layers=9, alpha_start=95)
        pygame.draw.circle(screen, ENEMY_COL, (cx, cy), 11)

    # player
    cellr = pygame.Rect(GRID_RECT.x + player_cell[0] * CELL, GRID_RECT.y + player_cell[1] * CELL, CELL, CELL)
    cx, cy = cellr.center
    soft_glow_circle(screen, (cx, cy), 12, PLAYER_COL, layers=10, alpha_start=105)
    pygame.draw.circle(screen, PLAYER_COL, (cx, cy), 12)

    # status banner
    banner = pygame.Rect(GRID_RECT.x, GRID_RECT.bottom + 18, GRID_RECT.w, 46)
    rounded_rect(screen, banner, (22, 26, 38), radius=16)
    rounded_rect(screen, banner, (60, 70, 95), radius=16, width=2)

    if game_over == "WIN":
        msg = "YOU WIN! Press P to return to BUILD."
    elif game_over == "LOSE":
        msg = "YOU DIED! Press P to return to BUILD."
    else:
        msg = "PLAY: Move with WASD/Arrow Keys. Get KEY to open DOOR. Reach EXIT."

    # key indicator
    key_txt = "KEY: YES" if has_key else "KEY: NO"
    screen.blit(font_small.render(msg, True, TEXT_DIM), (banner.x + 16, banner.y + 15))
    screen.blit(font_small.render(key_txt, True, KEY_COL), (banner.right - 120, banner.y + 15))

# -----------------------------
# PLAY UPDATE
# -----------------------------
enemy_accum = 0.0
ENEMY_STEP_TIME = 0.22

def update_enemies(dt):
    global enemy_accum, game_over
    if game_over is not None:
        return

    enemy_accum += dt
    while enemy_accum >= ENEMY_STEP_TIME:
        enemy_accum -= ENEMY_STEP_TIME

        for e in enemy_runtime:
            nx = e["x"] + e["vx"]
            ny = e["y"] + e["vy"]

            # enemy treats door as wall if locked
            def enemy_blocked(x, y):
                if x < 0 or x >= GRID_W or y < 0 or y >= GRID_H:
                    return True
                t = board[y][x]
                if t in (WALL, OBSTACLE):
                    return True
                if t == DOOR and not has_key:
                    return True
                return False

            if enemy_blocked(nx, ny):
                # bounce: try swapping axis if possible, otherwise reverse
                e["vx"] *= -1
                e["vy"] *= -1
                nx = e["x"] + e["vx"]
                ny = e["y"] + e["vy"]
                if enemy_blocked(nx, ny):
                    # if still blocked, switch to vertical patrol
                    if e["vy"] == 0:
                        e["vx"], e["vy"] = 0, 1
                    else:
                        e["vx"], e["vy"] = 1, 0
                    nx = e["x"] + e["vx"]
                    ny = e["y"] + e["vy"]
                    if enemy_blocked(nx, ny):
                        # stuck; stay
                        nx, ny = e["x"], e["y"]

            e["x"], e["y"] = nx, ny

        # collision check with player
        for e in enemy_runtime:
            if e["x"] == player_cell[0] and e["y"] == player_cell[1]:
                game_over = "LOSE"
                return

def try_move_player(dx, dy):
    global has_key, game_over
    if game_over is not None:
        return

    nx = player_cell[0] + dx
    ny = player_cell[1] + dy
    if is_solid_for_player(nx, ny):
        return

    player_cell[0], player_cell[1] = nx, ny

    # key pickup
    if board[ny][nx] == KEY:
        board[ny][nx] = EMPTY
        has_key = True

    # win check
    if (nx, ny) == EXIT:
        game_over = "WIN"
        return

    # enemy collision
    for e in enemy_runtime:
        if e["x"] == nx and e["y"] == ny:
            game_over = "LOSE"
            return

# -----------------------------
# MAIN LOOP
# -----------------------------
while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    # Animate button press amount
    target = 1.0 if is_pressing else 0.0
    press_amount = lerp(press_amount, target, min(1.0, PRESS_SPEED * dt))

    # Auto move cursor (build only)
    if mode == MODE_BUILD and (auto_dx != 0 or auto_dy != 0):
        auto_accum += dt
        while auto_accum >= AUTO_STEP_TIME:
            auto_accum -= AUTO_STEP_TIME
            move_cursor(auto_dx, auto_dy)

    # Play update
    if mode == MODE_PLAY:
        update_enemies(dt)

    # Button rect for hit-testing
    button_rect = get_button_rect(press_amount)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # P to toggle play
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                toggle_play()

            if mode == MODE_PLAY and game_over is None:
                if event.key in (pygame.K_w, pygame.K_UP):
                    try_move_player(0, -1)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    try_move_player(0, 1)
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    try_move_player(-1, 0)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    try_move_player(1, 0)

        # Right click: cycle placement (build only)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if mode == MODE_BUILD:
                cycle_place()

        # Left click handling (ONLY when click is on the button)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if button_rect.collidepoint(event.pos) and mode == MODE_BUILD:
                is_pressing = True
                mouse_down_started_on_button = True
                press_start_time = time.time()
            else:
                mouse_down_started_on_button = False
                is_pressing = False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if mode == MODE_BUILD and mouse_down_started_on_button:
                is_pressing = False
                mouse_down_started_on_button = False

                now = time.time()
                dur = now - press_start_time
                last_release_duration = dur

                # If any auto move is active and you click the button (any tap), stop it FIRST.
                # Then interpret the tap normally.
                # (Feels more controllable.)
                if auto_dx != 0 or auto_dy != 0:
                    stop_auto_move()
                    # continue to also treat this tap as input below

                # Treat this as a "tap" if under hold threshold
                if dur < HOLD_THRESHOLD:
                    record_tap(now)

                    # Resolve triple immediately
                    if recent_count(now, TRIPLE_WINDOW) >= 3:
                        # TRIPLE TAP:
                        # - normal: step DOWN
                        # - if 3rd click was held (we detect by dur >= HOLD_THRESHOLD), start auto UP
                        # But dur here is 3rd click duration. Since dur < HOLD_THRESHOLD in this branch,
                        # it's a normal step DOWN.
                        tap_times.clear()
                        pending_single = False
                        move_cursor(0, 1)
                    else:
                        # Wait to see if it becomes double
                        pending_single = True
                        pending_time = now

                else:
                    # A HOLD release by itself doesn't place or move,
                    # it's only meaningful if it's the held second/third tap — handled below.
                    # We'll do nothing here.
                    pass

    # Resolve pending single vs double/triple based on time window
    if mode == MODE_BUILD and pending_single:
        now = time.time()
        # Double?
        if recent_count(now, DOUBLE_WINDOW) >= 2:
            # DOUBLE TAP:
            # normal: step RIGHT
            # if second click was held, start auto LEFT
            # We detect "held second click" by checking duration of the last release (this release).
            # If user did click-release then click-hold-release as the 2nd tap, dur will be >= HOLD_THRESHOLD.
            # BUT our "tap" branch only fires when dur < HOLD_THRESHOLD.
            # So to support "double tap then hold", we allow holding the 2nd click by:
            # - user: click-release, click-hold-release
            # => on second release dur >= HOLD_THRESHOLD, we won't register tap in that moment.
            # So we need another way: treat a long release that happened soon after a prior tap as "held 2nd tap".
            #
            # To keep it intuitive and match what you said:
            # We'll interpret:
            #   - If there is 1 tap recently, and the next press is a HOLD, that HOLD triggers the "held second tap" effect.
            pass

        # If time window expired and no second tap => SINGLE PLACE
        if now - pending_time > DOUBLE_WINDOW:
            pending_single = False
            tap_times.clear()
            place_at_cursor()

 
    screen.fill(BG)
    draw_right_side()
    draw_left_panel(mouse_pos)

    pygame.display.flip()