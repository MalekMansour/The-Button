import pygame
import sys

pygame.init()

# Window
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Button — Pump Blood")
clock = pygame.time.Clock()

# Colors
CANDY_RED = (210, 35, 55)
RED = (210, 40, 40)
HOVER_RED = (240, 70, 70)
PRESSED_RED = (170, 20, 20)
SHADOW = (120, 10, 10)
TEXT = (255, 255, 255)
PANEL = (255, 255, 255, 30)

BAR_BG = (30, 10, 12)
BAR_BORDER = (255, 255, 255)
SAFE_ZONE = (80, 220, 140)   # green-ish safe zone
FILL = (255, 80, 100)        # blood fill

# Fonts
font_big = pygame.font.SysFont("arial", 36, bold=True)
font_small = pygame.font.SysFont("arial", 20, bold=True)
font_mid = pygame.font.SysFont("arial", 26, bold=True)

# Button (rest state)
BASE_W, BASE_H = 260, 120
base_center = (WIDTH // 2, HEIGHT // 2 + 40)

# Animation state
press_amount = 0.0
PRESS_SPEED = 16.0
is_pressing = False
mouse_down_started_on_btn = False

# Game state: blood
blood = 0.55  # start in a safe-ish place (0..1)
PUMP_RATE = 0.55    # per second while holding
DRAIN_RATE = 0.28   # per second while not holding

# Safe zone range (you can tweak)
SAFE_MIN = 0.35
SAFE_MAX = 0.70

dead = False

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(x, a, b):
    return max(a, min(b, x))

def get_button_rect(press_t: float):
    # When pressed: shrink + move down
    scale = lerp(1.0, 0.94, press_t)
    y_offset = lerp(0.0, 10.0, press_t)
    w = int(BASE_W * scale)
    h = int(BASE_H * scale)
    rect = pygame.Rect(0, 0, w, h)
    rect.center = (base_center[0], int(base_center[1] + y_offset))
    return rect

def draw_rounded_panel(x, y, w, h, alpha=35, radius=16):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    pygame.draw.rect(surf, (255, 255, 255, alpha), (0, 0, w, h), border_radius=radius)
    screen.blit(surf, (x, y))

def draw_blood_bar(value_0_1):
    # Bar layout
    bar_w = 560
    bar_h = 28
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 80

    # Panel behind
    draw_rounded_panel(bar_x - 20, bar_y - 35, bar_w + 40, 90, alpha=25, radius=18)

    # Title
    title = font_mid.render("PUMP BLOOD", True, (255, 235, 240))
    screen.blit(title, (bar_x, bar_y - 34))

    # Background
    pygame.draw.rect(screen, BAR_BG, (bar_x, bar_y, bar_w, bar_h), border_radius=10)

    # Safe zone overlay
    safe_x = bar_x + int(SAFE_MIN * bar_w)
    safe_w = int((SAFE_MAX - SAFE_MIN) * bar_w)
    safe_rect = pygame.Rect(safe_x, bar_y, safe_w, bar_h)
    safe_surf = pygame.Surface((safe_rect.width, safe_rect.height), pygame.SRCALPHA)
    safe_surf.fill((*SAFE_ZONE, 90))
    screen.blit(safe_surf, safe_rect.topleft)

    # Fill
    fill_w = int(clamp(value_0_1, 0.0, 1.0) * bar_w)
    pygame.draw.rect(screen, FILL, (bar_x, bar_y, fill_w, bar_h), border_radius=10)

    # Border
    pygame.draw.rect(screen, BAR_BORDER, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=10)

    # Marker text
    pct = int(value_0_1 * 100)
    label = font_small.render(f"{pct}%", True, (255, 255, 255))
    screen.blit(label, (bar_x + bar_w + 12, bar_y + 3))

    # Instructions
    instr = "Hold click on the button to pump • Don't hit 0% or 100% • Press R to restart"
    instr_s = font_small.render(instr, True, (255, 230, 235))
    screen.blit(instr_s, (bar_x - 20, bar_y + 40))

def draw_button(rect, mouse_pos, press_t, dead_state):
    hovering = rect.collidepoint(mouse_pos)

    if dead_state:
        color = (80, 30, 35)  # dead / muted
    else:
        if press_t > 0.5:
            color = PRESSED_RED
        else:
            color = HOVER_RED if hovering else RED

    border_radius = 20

    # Shadow
    shadow_offset = int(lerp(8, 4, press_t))
    shadow_rect = rect.copy()
    shadow_rect.y += shadow_offset
    pygame.draw.rect(screen, SHADOW, shadow_rect, border_radius=border_radius)

    # Button body
    pygame.draw.rect(screen, color, rect, border_radius=border_radius)

    # Gloss highlight
    highlight_alpha = int(lerp(70, 25, press_t))
    if dead_state:
        highlight_alpha = 10
    highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 3)
    highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
    highlight_surface.fill((255, 255, 255, highlight_alpha))
    screen.blit(highlight_surface, highlight_rect.topleft)

    # Text
    if dead_state:
        text = "DEAD"
    else:
        text = "HOLD"
    text_surface = font_big.render(text, True, TEXT)
    text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery + int(lerp(0, 2, press_t))))
    screen.blit(text_surface, text_rect)

def draw_death_overlay():
    # Dark overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    screen.blit(overlay, (0, 0))

    msg = font_big.render("THE BUTTON DIED", True, (255, 235, 235))
    msg2 = font_mid.render("Press R to restart", True, (255, 235, 235))

    screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
    screen.blit(msg2, msg2.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    # Current animated rect for hit testing
    current_rect = get_button_rect(press_amount)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                blood = 0.55
                dead = False
                is_pressing = False
                mouse_down_started_on_btn = False
                press_amount = 0.0

        if dead:
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down_started_on_btn = current_rect.collidepoint(event.pos)
            if mouse_down_started_on_btn:
                is_pressing = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            is_pressing = False
            mouse_down_started_on_btn = False

    # If mouse held down but moved off the button, stop pressing
    if not dead and is_pressing and not current_rect.collidepoint(mouse_pos):
        is_pressing = False

    # Animate press_amount
    target = 1.0 if (is_pressing and not dead) else 0.0
    press_amount = lerp(press_amount, target, min(1.0, PRESS_SPEED * dt))

    # Game logic: blood level
    if not dead:
        if is_pressing:
            blood += PUMP_RATE * dt
        else:
            blood -= DRAIN_RATE * dt

        # Death conditions
        if blood <= 0.0 or blood >= 1.0:
            dead = True
            blood = clamp(blood, 0.0, 1.0)
            is_pressing = False

    # Draw
    screen.fill(CANDY_RED)

    # Bar + UI
    draw_blood_bar(blood)

    # Small hint about safe range
    hint = f"SAFE ZONE: {int(SAFE_MIN*100)}% – {int(SAFE_MAX*100)}%"
    hint_s = font_small.render(hint, True, (255, 230, 235))
    screen.blit(hint_s, hint_s.get_rect(center=(WIDTH // 2, 160)))

    # Button
    current_rect = get_button_rect(press_amount)
    draw_button(current_rect, mouse_pos, press_amount, dead)

    # Death overlay
    if dead:
        draw_death_overlay()

    pygame.display.flip()