import pygame
import sys

pygame.init()

# Window
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Button — Morse Code")
clock = pygame.time.Clock()

# Colors
BG = (240, 240, 240)
RED = (210, 40, 40)
HOVER_RED = (240, 70, 70)
PRESSED_RED = (190, 25, 25)
SHADOW = (150, 20, 20)
TEXT = (255, 255, 255)
INK = (20, 20, 20)
FAINT = (70, 70, 70)

# Fonts
font_btn = pygame.font.SysFont("arial", 36, bold=True)
font_out = pygame.font.SysFont("consolas", 28, bold=True)
font_small = pygame.font.SysFont("consolas", 18, bold=False)

# Base button (rest state)
BASE_W, BASE_H = 260, 120
base_center = (WIDTH // 2, HEIGHT // 2 + 120)

# Animation state
press_amount = 0.0
PRESS_SPEED = 14.0
is_pressing = False
mouse_down_started_on_btn = False

def lerp(a, b, t):
    return a + (b - a) * t

def clamp(x, a, b):
    return max(a, min(b, x))

def get_button_rect(press_t: float):
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
        color = PRESSED_RED
    else:
        color = HOVER_RED if hovering else RED

    border_radius = 20

    # Shadow
    shadow_offset = int(lerp(8, 4, press_t))
    shadow_rect = rect.copy()
    shadow_rect.y += shadow_offset
    pygame.draw.rect(screen, SHADOW, shadow_rect, border_radius=border_radius)

    # Button
    pygame.draw.rect(screen, color, rect, border_radius=border_radius)

    # Gloss
    highlight_alpha = int(lerp(70, 25, press_t))
    highlight_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 3)
    highlight_surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
    highlight_surface.fill((255, 255, 255, highlight_alpha))
    screen.blit(highlight_surface, highlight_rect.topleft)

    # Text
    text_surface = font_btn.render("MORSE", True, TEXT)
    text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery + int(lerp(0, 2, press_t))))
    screen.blit(text_surface, text_rect)

# --- Morse dictionary (letters, numbers, and common punctuation) ---
MORSE_TO_CHAR = {
    # Letters
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z",

    # Numbers
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",

    # Punctuation / symbols (common set)
    ".-.-.-": ".", "--..--": ",", "..--..": "?", ".----.": "'",
    "-.-.--": "!", "-..-.": "/", "-.--.": "(", "-.--.-": ")",
    ".-...": "&", "---...": ":", "-.-.-.": ";", "-...-": "=",
    ".-.-.": "+", "-....-": "-", "..--.-": "_", ".-..-.": "\"",
    "...-..-": "$", ".--.-.": "@",
}

# --- Morse timing (seconds) ---
DOT_MAX = 0.22          # <= this is a dot, above becomes dash (tweakable)
LETTER_GAP = 0.60       # pause after last press to commit a letter
WORD_GAP = 1.30         # longer pause to add a space

# State
current_morse = ""      # the letter being built, like ".-.."
output_text = ""        # final decoded message

press_time = 0.0
released_time = 0.0
waiting_since_release = False

def commit_letter():
    global current_morse, output_text
    if not current_morse:
        return
    output_text += MORSE_TO_CHAR.get(current_morse, "�")  # unknown = �
    current_morse = ""

def commit_space():
    global output_text
    if output_text and not output_text.endswith(" "):
        output_text += " "

def clear_all():
    global current_morse, output_text
    current_morse = ""
    output_text = ""

def backspace_one():
    global current_morse, output_text
    # If mid-letter, delete last dot/dash first
    if current_morse:
        current_morse = current_morse[:-1]
    elif output_text:
        output_text = output_text[:-1]

def draw_text_area():
    # Big output line (wrap manually-ish)
    pad = 40
    y = 60

    title = font_out.render("OUTPUT:", True, INK)
    screen.blit(title, (pad, y))

    # wrap output into lines
    max_chars = 48
    text = output_text
    lines = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
    if not lines:
        lines = [""]

    for i, line in enumerate(lines[-5:]):  # show last 5 lines
        surf = font_out.render(line, True, INK)
        screen.blit(surf, (pad, y + 40 + i * 34))

    # Current morse being typed
    morse_label = font_small.render("CURRENT MORSE:", True, FAINT)
    screen.blit(morse_label, (pad, HEIGHT - 170))

    current = current_morse if current_morse else "(empty)"
    current_surf = font_out.render(current, True, INK)
    screen.blit(current_surf, (pad, HEIGHT - 145))

    # Tiny controls hint (no morse alphabet shown)
    hint = font_small.render("Button only • Tap=dot • Hold=dash • C=clear • Backspace=delete", True, (60, 60, 60))
    screen.blit(hint, (pad, HEIGHT - 40))

while True:
    dt = clock.tick(60) / 1000.0
    mouse_pos = pygame.mouse.get_pos()

    # Hit test with current animated rect
    current_rect = get_button_rect(press_amount)

    # Timers
    if is_pressing:
        press_time += dt
        waiting_since_release = False
    else:
        # only start counting release time after at least one press happened
        if waiting_since_release:
            released_time += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                clear_all()
            elif event.key == pygame.K_BACKSPACE:
                backspace_one()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down_started_on_btn = current_rect.collidepoint(event.pos)
            if mouse_down_started_on_btn:
                is_pressing = True
                press_time = 0.0  # reset duration for this press

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if is_pressing:
                # Decide dot vs dash based on press duration
                if press_time <= DOT_MAX:
                    current_morse += "."
                else:
                    current_morse += "-"

                # Start counting gap time
                released_time = 0.0
                waiting_since_release = True

            is_pressing = False
            mouse_down_started_on_btn = False

    # If mouse held but moved off, cancel press (optional)
    if is_pressing and not current_rect.collidepoint(mouse_pos):
        is_pressing = False
        mouse_down_started_on_btn = False
        # do NOT add dot/dash here (treat as cancelled)

    # Commit letter/space based on how long since last release
    if waiting_since_release and not is_pressing:
        if released_time >= WORD_GAP:
            commit_letter()
            commit_space()
            waiting_since_release = False
            released_time = 0.0
        elif released_time >= LETTER_GAP:
            commit_letter()
            waiting_since_release = False
            released_time = 0.0

    # Animate press_amount
    target = 1.0 if is_pressing else 0.0
    press_amount = lerp(press_amount, target, min(1.0, PRESS_SPEED * dt))

    # Draw
    screen.fill(BG)
    draw_text_area()

    current_rect = get_button_rect(press_amount)
    draw_button(current_rect, mouse_pos, press_amount)

    pygame.display.flip()