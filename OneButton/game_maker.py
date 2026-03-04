import pygame
import sys
import time

pygame.init()

# --- WINDOWS ---
button_screen = pygame.display.set_mode((300,300))
board_screen = pygame.display.set_mode((800,600))
pygame.display.set_caption("One Button Game Maker")

clock = pygame.time.Clock()

# --- GRID ---
GRID_W = 20
GRID_H = 15
CELL = 40

board = [[0 for x in range(GRID_W)] for y in range(GRID_H)]

# objects
EMPTY = 0
WALL = 1
PLAYER = 2
ENEMY = 3
EXIT = 4

objects = [WALL, PLAYER, ENEMY, EXIT, EMPTY]
object_names = ["Wall","Player","Enemy","Exit","Erase"]
current_object = 0

cursor_x = 0
cursor_y = 0

# press timing
press_start = 0
last_tap = 0
DOUBLE_TAP_TIME = 0.35
HOLD_TIME = 0.5

holding = False

font = pygame.font.SysFont("arial",20)

def draw_board():

    board_screen.fill((30,30,30))

    for y in range(GRID_H):
        for x in range(GRID_W):

            rect = pygame.Rect(x*CELL,y*CELL,CELL,CELL)

            v = board[y][x]

            color = (50,50,50)

            if v == WALL:
                color = (120,120,120)
            elif v == PLAYER:
                color = (0,150,255)
            elif v == ENEMY:
                color = (255,80,80)
            elif v == EXIT:
                color = (80,255,120)

            pygame.draw.rect(board_screen,color,rect)

            pygame.draw.rect(board_screen,(80,80,80),rect,1)

    # cursor
    rect = pygame.Rect(cursor_x*CELL,cursor_y*CELL,CELL,CELL)
    pygame.draw.rect(board_screen,(255,255,0),rect,3)

    # UI
    txt = font.render("Selected: "+object_names[current_object],True,(255,255,255))
    board_screen.blit(txt,(10,610-30))


def draw_button():

    button_screen.fill((220,220,220))

    rect = pygame.Rect(50,100,200,100)

    pygame.draw.rect(button_screen,(200,50,50),rect,0,20)

    txt = font.render("BUTTON",True,(255,255,255))
    button_screen.blit(txt,(115,140))


while True:

    now = time.time()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:

            press_start = now
            holding = True

        if event.type == pygame.MOUSEBUTTONUP:

            holding = False
            duration = now - press_start

            # HOLD → move cursor
            if duration > HOLD_TIME:

                cursor_x += 1

                if cursor_x >= GRID_W:
                    cursor_x = 0
                    cursor_y += 1
                    if cursor_y >= GRID_H:
                        cursor_y = 0

            else:

                # TAP / DOUBLE TAP
                if now - last_tap < DOUBLE_TAP_TIME:

                    # PLACE OBJECT
                    board[cursor_y][cursor_x] = objects[current_object]

                else:

                    # CHANGE OBJECT
                    current_object += 1
                    if current_object >= len(objects):
                        current_object = 0

                last_tap = now

    draw_board()
    draw_button()

    pygame.display.update()
    clock.tick(60)