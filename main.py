import pygame
from pygame.locals import *
import time
import random
from useful_objects import God
import pickle

def create_game(deck1, deck2, seed, host):
    deck_data1 = pickle.load(open('Decks/Deck_Data/'+deck1))
    deck_data2 = pickle.load(open('Decks/Deck_Data/'+deck2))
    game = God(1600, 900, deck_data1, deck_data2, seed, host)
    return game

deck1 = 'Deck_Example.pkl'
deck2 = 'Deck_Example.pkl'

seed = 3

host = True

game = create_game(deck1, deck2, seed, host)
game.start()
