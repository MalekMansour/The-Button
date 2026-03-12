import pygame
import sys

pygame.init()

# Window
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Buttons")
clock = pygame.time.Clock()

# Colors
BG = (240, 240, 240)

RED = (210, 40, 40)
HOVER_RED = (240, 70, 70)
PRESSED_RED = (190, 25, 25)
RED_SHADOW = (150, 20, 20)

BLUE = (50, 100, 220)
HOVER_BLUE = (80, 130, 250)
PRESSED_BLUE = (30, 80, 190)
BLUE_SHADOW = (20, 50, 140)

TEXT = (255, 255, 255)
DARK = (40, 40, 40)

# Fonts
font = pygame.font.SysFont("arial", 36, bold=True)
number_font = pygame.font.SysFont("arial", 72, bold=True)

# Counter
value = 0

# Button settings
BASE_W, BASE_H = 260, 120
left_center = (WIDTH // 2 - 170, HEIGHT // 2 + 40)
right_center = (WIDTH // 2 + 170, HEIGHT // 2 + 40)

# Animation states
left_press_amount = 0.0
right_press_amount = 0.0
PRESS_SPEED = 14.0

left_is_pressing = False
right_is_pressing = False

left_mouse_down_started = False
right_mouse_down_started = False


def lerp(a, b, t):
    return a + (b - a) * t


def get_button_rect(center, press_t: float):
    scale = lerp(1.0, 0.94, press_t)
    y_offset = lerp(0.0, 10.0, press_t)

    w = int(BASE_W * scale)
    h = int(BASE_H * scale)

    rect = pygame.Rect(0, 0, w, h)
    rect.center = (center[0], int(center[1] + y_offset))
    return rect


def draw_button(rect, mouse_pos, press_t, base_color, hover_color, pressed_color, shadow_color, label):
    hovering = rect.collidepoint(mouse_pos)

    if press_t > 0.5:
        color = pressed_color
    else:
        color = hover_color if hovering else base_color

    border_radius = 20

    # Shadow
    shadow_offset = int(lerp(8, 4, press_t))
    shadow_rect = rect.copy()
    shadow_rect.y += shadow_offset
    pygame.draw.rect(screen, shadow_color, shadow_rect, border_radius=border_radius)

    # Button body
    pygame.draw.rect(screen, color, rect, border_radius=border_radius)

    

    # Text
    text_surface = font.render(label, True, TEXT)
    text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery + int(lerp(0, 2, press_t))))
    screen.blit(text_surface, text_rect)


while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    left_rect = get_button_rect(left_center, left_press_amount)
    right_rect = get_button_rect(right_center, right_press_amount)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            left_mouse_down_started = left_rect.collidepoint(event.pos)
            right_mouse_down_started = right_rect.collidepoint(event.pos)

            if left_mouse_down_started:
                left_is_pressing = True
            if right_mouse_down_started:
                right_is_pressing = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if left_mouse_down_started and left_rect.collidepoint(event.pos):
                value += 1

            if right_mouse_down_started and right_rect.collidepoint(event.pos):
                value -= 1

            left_is_pressing = False
            right_is_pressing = False
            left_mouse_down_started = False
            right_mouse_down_started = False

    # Stop press animation if mouse moves off while holding
    if left_is_pressing and not left_rect.collidepoint(mouse_pos):
        left_is_pressing = False
    if right_is_pressing and not right_rect.collidepoint(mouse_pos):
        right_is_pressing = False

    # Animate
    left_target = 1.0 if left_is_pressing else 0.0
    right_target = 1.0 if right_is_pressing else 0.0

    left_press_amount = lerp(left_press_amount, left_target, min(1.0, PRESS_SPEED * dt))
    right_press_amount = lerp(right_press_amount, right_target, min(1.0, PRESS_SPEED * dt))
  
    left_rect = get_button_rect(left_center, left_press_amount)
    right_rect = get_button_rect(right_center, right_press_amount)

    draw_button(left_rect, mouse_pos, left_press_amount, RED, HOVER_RED, PRESSED_RED, RED_SHADOW, "+1")
    draw_button(right_rect, mouse_pos, right_press_amount, BLUE, HOVER_BLUE, PRESSED_BLUE, BLUE_SHADOW, "-1")

    pygame.display.flip()