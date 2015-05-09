import pygame
from pygame.locals import *
import time
import random2
from objects import God
import pickle

def start_game(deck1, deck2, seed, host):
    deck_data1 = pickle.load(open('Decks/deck_data/'+deck1))
    deck_data2 = pickle.load(open('Decks/deck_data/'+deck2))
    game = God(1600, 900, deck_data1, deck_data2, seed, host)
    return game

game = start_game()
# set up timing
card = [pygame.image.load('cache/275705.jpeg'), pygame.image.load('cache/275706.jpeg')]
screen.blit(card[0], (0, 0))
screen.blit(card[1], (100, 10))
pygame.display.flip()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print 'user quit'
