"""
5/3/15 defines classes that will be used
"""
import random
import threading
import pygame
from pygame.locals import *
import time
from pic_grab import download_pic
import numpy as np
import sys


selector_group = None
card_group = [None, None]


class Card(pygame.sprite.Sprite):
    def __init__(self, params, player_id, screen_size, host=True):  # [name, type, id, cost, power, toughness, text, location]
        self.groups = card_group
        self._layer = 3
        pygame.sprite.Sprite.__init__(self)
        self.w              = int(screen_size[0])
        self.h              = int(screen_size[1]/6)
        self.tapped         = False     # False if untapped
        self.owner          = True      # False if stolen until end of turn
        self.can_block      = True      # False if can't block
        self.summoning_sickness = True  # only when it enters
        self.can_attack     = True      # can't attack when first used
        self.name           = params[0] # name of card
        self.type           = params[1].split(' - ') # type of card
        self.id             = params[2] # card identification number
        self.cost           = params[3] # mana cost
        self.power          = params[4] # base power
        self.toughness      = params[5] # base toughness
        self.text           = params[6] # card text
        hand        = [(0,        self.h),   # player 0  # hand[player][init/final]
                       (5*self.h, 6*self.h)]   # player 1  # middle is sum(hand[player])/2
        land        = [(self.h,   2*self.h),
                       (4*self.h, 5*self.h)]
        battlefield = [(2*self.h, 3*self.h),
                       (3*self.h, 4*self.h)]
        self.loc_id = {'hand':        hand,
                       'land':        land,
                       'battlefield': battlefield}
        try:
            self.front_image = pygame.image.load('cache/%s.jpeg'%self.id)
        except:
            download_pic(self.id)
            self.front_image = pygame.image.load('cache/%s.jpeg'%self.id)
        self.back_image = pygame.image.load('Decks/Card_Back/Back_of_Card.jpeg')
        self.image = self.back_image
        self.player_id = player_id
        if player_id:
            spot = 7
        else:
            spot = 2
        self.pos_id  = [player_id, 'hand', spot]
        self.x = self.y = 0
        self.update()
        self.image.unlock()
        self.p = self.power     # current power
        self.t = self.toughness # current toughness
        self.p_temp = 0  # power buff until end of turn
        self.t_temp = 0  # toughness buff until end of turn
        self.token  = False

    def update(self, spot=None):
        player = self.pos_id[0]
        loc  = self.pos_id[1]
        if spot == None:
            spot = self.pos_id[2]
        else:
            self.pos_id[2] = spot + (self.player_id+1)%2 * 3
        self.y = sum(self.loc_id[loc][player]) / 2
        self.x = self.h * ((spot % (self.w/self.h)) + 0.5)
        self.position = (int(self.x), int(self.y))
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def reveal(self):
        self.image = self.front_image
        self.image.unlock()

    def hide(self):
        self.image = self.back_image
        self.image.unlock()

    def tap(self):  # this method taps the card
        self.tapped = True
        self.image = pygame.transform.rotate(self.image, -90)
        self.place()

    def untap(self):  # this method untaps the card
        self.tapped = False
        self.image = pygame.transform.rotate(self.image, 90)
        self.place()

    def return_card(self): # run this method after card is returned to owner
        self.owner = True

    def end_sickness(self):
        self.summoning_sickness = False

    def rescale_card(self, screen_height):
        h = float(self.image.get_height())
        w = float(self.image.get_width())
        size = np.array([w/h, 1])*screen_height/6*0.95
        self.image = pygame.transform.scale(self.image, (int(size[0]), int(size[1])))
        h = float(self.back_image.get_height())
        w = float(self.back_image.get_width())
        size = np.array([w/h, 1])*screen_height/6*0.95
        self.back_image = pygame.transform.scale(self.back_image, (int(size[0]), int(size[1])))
        h = float(self.front_image.get_height())
        w = float(self.front_image.get_width())
        size = np.array([w/h, 1])*screen_height/6*0.95
        self.front_image = pygame.transform.scale(self.front_image, (int(size[0]), int(size[1])))


class Creature(Card):
    def counter_plus(self):  # puts a +1,+1 counter on card
        self.p = self.p + 1
        self.t = self.t + 1

    def counter_minus(self):  # puts a -1,-1 counter on card
        self.p = self.p - 1
        self.t = self.t - 1

    def buff(self, p, t): # puts a +p,+t buff on card until end of turn
        self.p_temp = p
        self.t_temp = t
        self.p = self.p + self.p_temp
        self.t = self.t + self.t_temp

    def reset_buff(self): # removes all temporary buffs from card
        self.p = self.p - self.p_temp
        self.t = self.t - self.t_temp
        self.p_temp = 0
        self.t_temp = 0

    def temp_stolen(self): # run this method if card is stolen until end of turn
        self.owner = False


class Token(Creature):
    def __init__(self, name, power, toughness, color, text):
        self.name      = name       # name of token: goblin, knight, etc.
        self.power     = power      # token base power
        self.toughness = toughness  # token base toughness
        self.color     = color      # colors of card
        self.text      = text       # any additional things: haste, vigilance, etc.
        self.token     = True
        self.p         = self.power      # current power
        self.t         = self.toughness  # current toughness
        self.p_temp    = 0               # amount of current power that is until end of turn
        self.t_temp    = 0               # amount of current toughness that is until end of turn


class Position(object):
    def __init__(self):
        self.cards = []

    def remove_card(self, index):
        del self.cards[index]


class Library(Position):
    def seed_card(self, params, player_id, screen_size, host=True):  # [name, type, id, cost, power, toughness, text]
        self.cards.append(Card(params, player_id, screen_size, host))

    #def scry(self, amount):

    #def rearange(self, amount):


class Battlefield(Position):
    def clear_buffs(self):
        threads = []
        for card in self.cards:
            t1 = threading.Thread(target=card.reset_buff)
            threads.append(t1)
            t1.start()
            t2 = threading.Thread(target=card.end_sickness)
            threads.append(t2)
            t2.start()

    def reset_field(self):
        threads = []
        for card in self.cards:
            t = threading.Thread(target=card.untap)
            threads.append(t)
            t.start()

    def add_token(self, name, power, toughness, color, text):
        self.cards.append(Token(name, power, toughness, color, text))


class Player(object):
    def __init__(self, deck, id, screen_size, host=True):
        self.id = id
        self.host = host
        self.location = {'library':     Library(),
                         'hand':        Position(),
                         'battlefield': Battlefield(),
                         'land':        Battlefield(),
                         'graveyard':   Position(),
                         'exiled':      Position(),
                         'stack':       Position()    }
        self.mana = { 'w': 0,
                      'k': 0,
                      'b': 0,
                      'g': 0,
                      'r': 0,
                      'c': 0  }
        self.cards = []
        card_keys = ['names', 'types', 'ids', 'costs', 'powers', 'toughs', 'texts']
        for i in range(len(deck['names'])):
            self.location['library'].seed_card([deck[key][i] for key in card_keys], self.id, screen_size, host)  # seed library
        self.shuffle_lib()

    def draw_card(self):
        card = self.location['library'].cards[0]
        if self.host:
            card.reveal()
        card.pos_id[1] = 'hand'
        card.pos_id[2] = len(self.location['hand'].cards) + (self.id+1)%2 * 3
        self.location['hand'].cards.append(card)
        self.location['library'].remove_card(0)
        card.update()

    def add_mana(self, color):
        self.mana[color] = self.mana[color] + 1

    def rem_mana(self, color):
        self.mana[color] = self.mana[color] - 1

    def shuffle_lib(self):
        self.shuffle()
        self.cut()
        self.shuffle()
        self.cut()

    def shuffle(self):
        random.shuffle(self.location['library'].cards)

    def cut(self):
        # cuts the deck at a random spot in the middle 3rd of the deck
        # 1/2*len(cards) +/- 1/3*len(cards)
        lower_bound = int(len(self.location['library'].cards)/2) - int(len(self.location['library'].cards)/3)
        spot = lower_bound + int(random.random()*len(self.location['library'].cards)/3)
        self.cards = self.location['library'].cards[spot:].extend(self.location['library'].cards[:spot])


class God(object):
    def __init__(self, width, height, deck1, deck2, game_seed, host=True):
        global card_group, selector_group
        #set up screen
        self.screen = Screen(width, height, True)
        self.clock = pygame.time.Clock()
        self.fps = 30
        self.deltat = self.clock.tick(self.fps)

        # set up layer controller
        self.layer = pygame.sprite.LayeredUpdates()

        # True if hosting, False if guest
        self.host = host

        # This is the seed that keeps the game sunk up for use of the random module
        #self.seed = game_seed
        random.seed(game_seed)

        self.screen.screen.fill((0, 0, 0))
        # create selector and place it on the field
        self.selector = Selector((width, height), self.host)
        selector_group = pygame.sprite.RenderPlain(self.selector)
        selector_group.draw(self.screen.screen)

        # Sets up players and their decks
        self.player = [Player(deck1, 0, (width, height), self.host),
                       Player(deck2, 1, (width, height), not self.host)]  # player[0] is host and player[1] is guest
        self.rescale_images()

        # set up card sprites
        for i in range(2):
            card_group[i] = pygame.sprite.RenderPlain(self.player[i].location['library'].cards)

#        self.card_group.draw(self.screen.screen)
#        pygame.display.flip()

        # Sets up the stack
        self.stack = Position()

        # Sets up the turn tracker
        self.turn = 0   # integer values for host, half integer values for guest
        self.phase = 0  # phase of battle: 'beginning', 'first main', 'combat', 'second main', 'end'
        self.who = 0    # who's turn it is: 0 for player 1 and 1 for player 2
        self.done = False

        #card_group = pygame.sprite.RenderPlain()
        #selector_group = pygame.sprite.RenderPlain()

        for i in range(2):
            time.sleep(0.01)
            card_group[i].draw(self.screen.screen)
        pygame.display.flip()

    def start(self):
        for p in self.player:
            for k in range(7):
                p.draw_card()
        self.run()

    def run(self):
        try:
            while True:
                deltat = self.clock.tick(self.fps)
                for event in pygame.event.get():
                    if not hasattr(event, 'key'): continue
                    if not event.type == KEYDOWN: continue
                    if event.key == K_RIGHT: self.selector.move_right()
                    elif event.key == K_LEFT: self.selector.move_left()
                    elif event.key == K_UP: self.selector.move_up()
                    elif event.key == K_DOWN: self.selector.move_down()
                    elif event.key == K_RETURN: self.action()
                    elif event.key == K_ESCAPE: sys.exit(0)
                # Rendering
                self.screen.screen.fill((0, 0, 0,))
                selector_group.update()
                selector_group.draw(self.screen.screen)
                for i in range(2):
                    card_group[i].update()
                    card_group[i].draw(self.screen.screen)
                pygame.display.flip()
        except KeyboardInterrupt:
            print 'user quit'


    def rescale_images(self):
        # for scaling the images of the cards at the beginning of the game
        for p in self.player:
            threads = []
            for card in p.location['library'].cards:
                t = threading.Thread(target=card.rescale_card, args=(self.screen.height,))
                threads.append(t)
                t.start()

    def play_card(self, index, p):
        hand = self.player[p].location['hand'].cards
        card = hand[index]
        #self.stack.cards.append(card)
        #self.player[p].location['stack'].cards.append(card)
        if 'Land' in card.type[0]:
            cards = self.player[p].location['land'].cards
            cards.append(card)
            card.pos_id[1] = 'land'
            if card.name == 'Plains':     card.pos_id[2] = 0
            elif card.name == 'Island':   card.pos_id[2] = 1
            elif card.name == 'Swamp':    card.pos_id[2] = 2
            elif card.name == 'Mountain': card.pos_id[2] = 3
            elif card.name == 'Forest':   card.pos_id[2] = 4
            else:
                card_names = []
                for card in cards:
                    card_names.append(card.name)
                if card.name in set(card_names):
                    ind = card_names.index(card.name)
                    card.pos_id[2] = cards[ind].pos_id[2]
                else:
                    land_types = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']
                    for land_type in land_types:
                        card_names.append(land_type)
                    card.pos_id[2] = len(set(card_names))
        else:
            cards = self.player[p].location['battlefield'].cards
            cards.append(card)
        self.player[p].location['hand'].remove_card(index)
        card.update()
        threads = []
        for i in range(len(hand)):
            t = threading.Thread(target=hand[i].update, args=(i,))
            threads.append(t)
            t.start()



    def action(self):
        p = self.selector.pos_id[0]
        loc = self.selector.pos_id[1]
        spot = self.selector.pos_id[2]
        if p == 0 and loc == 'hand' and spot == 2:  # then player[0]'s library
            self.player[p].draw_card()
        elif p == 1 and loc == 'hand' and spot == 7:  # then player[1]'s library
            self.player[p].draw_card()
        elif loc == 'hand':
            index = spot - (p+1)%2 *3
            self.play_card(index, p)


#    def execute_phase(self):
#        self.done = False
#        if self.phase == 0:
#            self.beginning_phase()
#        if self.phase == 1:
#            self.main_phase()
#        if self.phase == 2:
#            self.combat_phase()
#        if self.phase == 3:
#            self.main_phase()
#        if self.phase == 4:
#            self.end_phase()
#        self.phase = (self.phase + 1) % 5
#        if self.phase == 0:
#            self.turn = self.turn + 0.5
#            self.who = (self.turn % 1)*2  # since self.turn is int for player[0] or half int for player [1]

#    def beginning_phase(self):
#        self.player[self.who].location['battlefield'].reset_field()  # untap step
#        self.upkeep()  # upkeep step
#        self.player[self.who].draw_card()  # draw step

#    def upkeep(self):
#        while not self.done:
#            self.clock.tick(30)
#            for event in pygame.event.get():

#    def main_phase(self):
#        self.done = False
#        while not self.done:
#            time.sleep(1./30)


class Screen(object):
    def __init__(self, width, height, fullscreen=False):
        #set up screen
        self.width       = int(width)  # width of screen in pixels
        self.height      = int(height) # height of screen in pixels
        if fullscreen:
            self.screen = pygame.display.set_mode((self.width, self.height), FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height))
        hand        = [(0,               self.height/6),   # player 0  # hand[player][init/final]
                       (5*self.height/6, self.height)  ]   # player 1  # middle is sum(hand[player])/2
        land        = [(self.height/6,   2*self.height/6),
                       (4*self.height/6, 5*self.height/6)]
        battlefield = [(2*self.height/6, 3*self.height/6),
                       (3*self.height/6, 4*self.height/6)]
        self.location = {'hand':        hand,
                         'land':        land,
                         'battlefield': battlefield}
        self.clock = pygame.time.Clock()
        self.fps = 30
        self.deltat = self.clock.tick(self.fps)

    def add_image(self, image, params, tapped=False):  # params = (player, loc, spot)
        player = params[0]
        loc    = params[1]
        spot   = params[2]
        if loc in self.location.keys() and player in [0, 1]:
            if tapped:
                image = pygame.transform.rotate(image, -90)
            yoff = (self.height/6 - image.get_height()) / 2
            xoff = (self.height/6 - image.get_width()) / 2
            y = self.location[loc][player][0] + yoff
            x = self.height/6 * (spot % (self.width/(self.height/6))) + xoff
            self.screen.blit(image, (int(x), int(y)))
            pygame.display.flip()
        else:
            raise IOError


class Selector(pygame.sprite.Sprite):
    def __init__(self, screen_size, host):
        self.groups = selector_group
        self._layer = 2
        pygame.sprite.Sprite.__init__(self)
        self.w      = screen_size[0]
        self.h      = screen_size[1]/6
        hand        = [(0,        self.h),   # player 0  # hand[player][init/final]
                       (5*self.h, 6*self.h)]   # player 1  # middle is sum(hand[player])/2
        land        = [(self.h,   2*self.h),
                       (4*self.h, 5*self.h)]
        battlefield = [(2*self.h, 3*self.h),
                       (3*self.h, 4*self.h)]
        self.location = {'hand':        hand,
                         'land':        land,
                         'battlefield': battlefield}
        self._layer = 0
        w = h = self.h
        self.image = pygame.Surface((w, h))
        pygame.draw.rect(self.image, (200, 0, 0), self.image.get_rect())
        if host:
            self.pos_id = [0, 'hand', 2]
        else:
            self.pos_id = [1, 'hand', 7]
        self.update()


    def update(self):
        player = self.pos_id[0]
        loc    = self.pos_id[1]
        spot   = self.pos_id[2]
        self.y = sum(self.location[loc][player]) / 2
        self.x = self.h * ((spot % (self.w/self.h)) + 0.5)
        self.position = (int(self.x), int(self.y))
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def move_right(self):
        self.pos_id[2] = self.pos_id[2] + 1
        self.update()

    def move_left(self):
        self.pos_id[2] = self.pos_id[2] - 1
        self.update()

    def move_up(self):
        if self.pos_id[0] == 0:
            if self.pos_id[1] == 'hand':
                self.pos_id[0] = (self.pos_id[0] + 1) % 2
            elif self.pos_id[1] == 'land':
                self.pos_id[1] = 'hand'
            elif self.pos_id[1] == 'battlefield':
                self.pos_id[1] = 'land'
        elif self.pos_id[0] == 1:
            if self.pos_id[1] == 'hand':
                self.pos_id[1] = 'land'
            elif self.pos_id[1] == 'land':
                self.pos_id[1] = 'battlefield'
            elif self.pos_id[1] == 'battlefield':
                self.pos_id[0] = (self.pos_id[0] + 1) % 2
        self.update()

    def move_down(self):
        if self.pos_id[0] == 0:
            if self.pos_id[1] == 'hand':
                self.pos_id[1] = 'land'
            elif self.pos_id[1] == 'land':
                self.pos_id[1] = 'battlefield'
            elif self.pos_id[1] == 'battlefield':
                self.pos_id[0] = (self.pos_id[0] + 1) % 2
        elif self.pos_id[0] == 1:
            if self.pos_id[1] == 'hand':
                self.pos_id[0] = (self.pos_id[0] + 1) % 2
            elif self.pos_id[1] == 'land':
                self.pos_id[1] = 'hand'
            elif self.pos_id[1] == 'battlefield':
                self.pos_id[1] = 'land'
        self.update()