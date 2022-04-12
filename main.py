import os
import random
import pygame
from pygame.locals import *

from objects import World, Player, Button, draw_lines, load_level, draw_text, sounds


SIZE = WIDTH , HEIGHT= 1000, 650
TILE_SIZE = 50


pygame.init()
win = pygame.display.set_mode(SIZE)
pygame.display.set_caption('RUN')
clock = pygame.time.Clock()
FPS = 40
WHITE = (255, 255, 255)


#DECORATORS
#Decorator for resetting level
def reset_level_decorator(func):
	def wrapper(*args, **kwargs):
		global CUR_SCORE
		CUR_SCORE = 0
		func(*args, **kwargs)
	return wrapper

# Decorator for resetting player
def reset_player_decorator(func):
	def wrapper(*args, **kwargs):
		global CUR_SCORE
		CUR_SCORE = 0
		func(*args, **kwargs)
	return wrapper

# background images
bg1 = pygame.image.load('assets/BG1.png')
bg2 = pygame.image.load('assets/BG2.png')
bg = bg1
sun = pygame.image.load('assets/sun.png')
jungle_run = pygame.image.load('assets/9fWW38bLEdofv77bUPLIu8zLN6.jpg')
you_won = pygame.image.load('assets/won.png')


# loading level 1
LEVEL = 1
max_level = len(os.listdir('levels/'))
data = load_level(LEVEL)
player_pos = (10, 340)


# creating world & sprite objects 
water_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
forest_group = pygame.sprite.Group()
diamond_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
bridge_group = pygame.sprite.Group()
groups = [water_group, lava_group, forest_group, diamond_group, enemies_group, exit_group, platform_group,
			bridge_group]
world = World(win, data, groups)
player = Player(win, player_pos, world, groups)

# creating buttons
play= pygame.image.load('assets/play.png')
REPLAY = pygame.image.load('assets/replay.png')
HOME = pygame.image.load('assets/home.png')
EXIT = pygame.image.load('assets/exit.png')
setting = pygame.image.load('assets/setting.png')

play_btn = Button(play, (128, 64), WIDTH//2 - WIDTH // 16, HEIGHT//2)
replay_btn  = Button(REPLAY, (45,42), WIDTH//2 - 110, HEIGHT//2 + 20)
home_btn  = Button(HOME, (45,42), WIDTH//2 - 20, HEIGHT//2 + 20)
exit_btn  = Button(EXIT, (45,42), WIDTH//2 + 70, HEIGHT//2 + 20)




# resets world level after player reset
def reset_level(LEVEL):
	global CUR_SCORE
	CUR_SCORE = 0

	data = load_level(LEVEL)
	if data:
		for group in groups:
			group.empty()
		world = World(win, data, groups)
		player.reset(win, player_pos, world, groups)
# 10, 340
	return world

SCORE = 0
CUR_SCORE = 0

MAIN_MENU = True
GAME_OVER = False
LEVEL_WON = False
GAME_WON = False
RUNNING = True
while RUNNING:
	for event in pygame.event.get():
		if event.type == QUIT:
			RUNNING = False
	pressed_keys = pygame.key.get_pressed()

	# displaying background & sun image
	win.blit(bg, (0,0))
	win.blit(sun, (40,40))
	world.draw()
	for group in groups:
		group.draw(win)

	# drawing grid
	# draw_lines(win)
	# checks for main_menu game drawing of game play win or loss types
	if MAIN_MENU:
		win.blit(jungle_run, (WIDTH//2 - WIDTH//8, HEIGHT//4))

		PLAY_GAME = play_btn.draw(win)
		if PLAY_GAME:
			MAIN_MENU = False
			GAME_OVER = False
			GAME_WON = False
			SCORE = 0

	else:
		if not GAME_OVER and not GAME_WON:
			
			enemies_group.update(player)
			platform_group.update()
			exit_group.update(player)
			if pygame.sprite.spritecollide(player, diamond_group, True):
				sounds[0].play()
				CUR_SCORE += 1
				SCORE += 1	
			draw_text(win, f'{SCORE}', ((WIDTH//TILE_SIZE - 2) * TILE_SIZE, TILE_SIZE//2 + 10))
			
		GAME_OVER, LEVEL_WON = player.update(pressed_keys, GAME_OVER, LEVEL_WON, GAME_WON)

		if GAME_OVER and not GAME_WON:
			REPLAY = replay_btn.draw(win)
			HOME = home_btn.draw(win)
			EXIT = exit_btn.draw(win)

			if REPLAY:
				SCORE -= CUR_SCORE
				world = reset_level(LEVEL)
				GAME_OVER = False
			if HOME:
				GAME_OVER = True
				MAIN_MENU = True
				bg = bg1
				LEVEL = 1
				world = reset_level(LEVEL)
			if EXIT:
				RUNNING = False

		if LEVEL_WON:
			if LEVEL <= max_level:
				LEVEL += 1
				game_level = f'levels/level{LEVEL}_DATA'
				if os.path.exists(game_level):
					data = []
					world = reset_level(LEVEL)
					LEVEL_WON = False
					SCORE += CUR_SCORE

				bg = random.choice([bg1, bg2])
			else:
				GAME_WON = True
				bg = bg1
				win.blit(you_won, (WIDTH//4, HEIGHT // 4))
				HOME = home_btn.draw(win)

				if HOME:
					GAME_OVER = True
					MAIN_MENU = True
					LEVEL_WON = False
					LEVEL = 1
					world = reset_level(LEVEL)

	pygame.display.flip()
	clock.tick(FPS)

pygame.quit()
