import pygame
import sys
import random
import colorsys

pygame.init()

# Window
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Button")
clock = pygame.time.Clock()

# Colors
BG = [240, 240, 240]
RED = [210, 40, 40]
HOVER_RED = (240, 70, 70)
SHADOW = (150, 20, 20)
TEXT = (255, 255, 255)

# Font
font = pygame.font.SysFont("arial", 36, bold=True)

# Base button (rest state)
BASE_W, BASE_H = 260, 120
base_center = (WIDTH // 2, HEIGHT // 2)

# Animation state
press_amount = 0.0
PRESS_SPEED = 14.0
is_pressing = False
mouse_down_started_on_btn = False

# Hold detection
press_start_time = 0.0
HOLD_TIME = 0.4


def lerp(a, b, t):
    return a + (b - a) * t


def random_color_wheel():
    h = random.random()
    s = 0.8
    v = 1.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return [int(r * 255), int(g * 255), int(b * 255)]


def get_button_rect(press_t: float):
    """
    Returns the animated rect.
    press_t: 0..1
    """
    scale = lerp(1.0, 0.94, press_t)
    y_offset = lerp(0.0, 10.0, press_t)

    w = int(BASE_W * scale)
    h = int(BASE_H * scale)

    rect = pygame.Rect(0, 0, w, h)
    rect.center = (base_center[0], int(base_center[1] + y_offset))
    return rect


def draw_button(rect, mouse_pos, press_t):
    hovering = rect.collidepoint(mouse_pos)

    if press_t > 0.5:
        color = [max(0, RED[0] - 20), max(0, RED[1] - 20), max(0, RED[2] - 20)]
    else:
        if hovering:
            color = [
                min(255, RED[0] + 30),
                min(255, RED[1] + 30),
                min(255, RED[2] + 30),
            ]
        else:
            color = RED

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
    highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 3)
    highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
    highlight_surface.fill((255, 255, 255, highlight_alpha))
    screen.blit(highlight_surface, highlight_rect.topleft)

    # Text
    text_surface = font.render("PRESS", True, TEXT)
    text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery + int(lerp(0, 2, press_t))))
    screen.blit(text_surface, text_rect)


while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    current_rect = get_button_rect(press_amount)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down_started_on_btn = current_rect.collidepoint(event.pos)
            if mouse_down_started_on_btn:
                is_pressing = True
                press_start_time = pygame.time.get_ticks() / 1000.0

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if mouse_down_started_on_btn:
                press_duration = (pygame.time.get_ticks() / 1000.0) - press_start_time

                if press_duration >= HOLD_TIME:
                    BG = random_color_wheel()   # hold = change background
                else:
                    RED = random_color_wheel()  # tap = change button

            is_pressing = False
            mouse_down_started_on_btn = False

    # If mouse moves off button while holding, stop pressing animation
    if is_pressing and not current_rect.collidepoint(mouse_pos):
        is_pressing = False

    # Animate press_amount toward target
    target = 1.0 if is_pressing else 0.0
    press_amount = lerp(press_amount, target, min(1.0, PRESS_SPEED * dt))

    # Draw
    screen.fill(BG)
    current_rect = get_button_rect(press_amount)
    draw_button(current_rect, mouse_pos, press_amount)

    pygame.display.flip()
