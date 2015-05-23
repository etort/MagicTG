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
health_group = [None, None]
button_group = None
expanded_group = None

pygame.font.init()

class Button(pygame.sprite.Sprite):
    def __init__(self, name, index, screen_size):
        self.groups = button_group
        self._layer = 4
        pygame.sprite.Sprite.__init__(self)
        self.x = screen_size[0]*(7./10)
        self.y = (screen_size[1]/12.)*(2+index)
        self.name = name
        self.image = pygame.image.load('images/%s.jpeg'%self.name)
        w = float(self.image.get_width())
        h = float(self.image.get_height())
        size = np.array([w/h, 1]) * screen_size[0]/20 * 0.80
        self.image = pygame.transform.scale(self.image, (int(size[0]), int(size[1])))
        self.position = [int(self.x), int(self.y)]
        self.rect = self.image.get_rect()
        self.update()
        self.image.unlock()

    def update(self):
        self.position = [int(self.x), int(self.y)]
        self.rect = self.image.get_rect()
        self.rect.center = self.position


class Health(pygame.sprite.Sprite):
    def __init__(self, health, player_id, screen_size):
        self.groups = health_group[player_id]
        self._layer = 3
        pygame.sprite.Sprite.__init__(self)
        self.health = health
        self.w = screen_size[0]
        self.h = screen_size[1]
        self.grid_number = 10
        self.grid_length = self.w/self.grid_number
        self.damage = 0
        self.healing = 0
        self.x = self.grid_length * ((9 % self.grid_number) + 0.1)
        self.y = self.h/6 * (1.5 + player_id*3)
        self.health = self.health - self.damage + self.healing
        self.damage = 0
        self.healing = 0
        self.position = [int(self.x), int(self.y)]
        self.font = pygame.font.Font(None, 52)
        self.color = (0, 250, 0)
        self.text = self.font.render('%d HP' % self.health, 1, self.color)
        self.rect = self.text.get_rect()
        self.rect.center = self.position

    def heal_one(self):
        self.healing = 1

    def damage_one(self):
        self.damage = 1

    def update(self):
        self.health = self.health - self.damage + self.healing
        self.damage = 0
        self.healing = 0
        # self.position = [int(self.x), int(self.y)]
        # self.font = pygame.font.Font(None, 36)
        if self.health <= 5:
            self.color = (250, 0, 0)
        else:
            self.color = (0, 250, 0)
        self.text = self.font.render('%d HP' % self.health, 1, self.color)
        self.rect = self.text.get_rect()
        self.rect.center = self.position

class Card(pygame.sprite.Sprite):
    def __init__(self, params, player_id, screen_size, host=True):  # [name, type, id, cost, power, toughness, text, location]
        self.groups = card_group
        self._layer = 3
        pygame.sprite.Sprite.__init__(self)
        self.screen_size = screen_size
        self.w              = int(screen_size[0])
        self.h              = int(screen_size[1])
        self.grid_number    = 10
        self.grid_width     = self.w/self.grid_number
        self.tapped         = False      # False if untapped
        self.owner          = True       # False if stolen until end of turn
        self.can_block      = True       # False if can't block
        self.summoning_sickness = True   # only when it enters
        self.can_attack     = True       # can't attack when first used
        self.name           = params[0]  # name of card
        self.type           = params[1].split(' - ')  # type of card
        self.id             = params[2]  # card identification number
        self.cost           = params[3]  # mana cost
        self.power          = params[4]  # base power
        self.toughness      = params[5]  # base toughness
        self.text           = params[6]  # card text
        hand        = [(0,        self.h/6),   # player 0  # hand[player][init/final]
                       (5*self.h/6, 6*self.h/6)]   # player 1  # middle is sum(hand[player])/2
        land        = [(self.h/6,   2*self.h/6),
                       (4*self.h/6, 5*self.h/6)]
        battlefield = [(2*self.h/6, 3*self.h/6),
                       (3*self.h/6, 4*self.h/6)]
        self.loc_id = {'hand':        hand,
                       'land':        land,
                       'battlefield': battlefield}
        try:
            self.front_image = pygame.image.load('cache/%s.jpeg'%self.id)
        except:
            download_pic(self.id)
            self.front_image = pygame.image.load('cache/%s.jpeg'%self.id)
        #self.tapped_image = pygame.image.load('cache/%s.jpeg'%self.id)
        #self.tapped_image = pygame.transform.rotate(self.tapped_image, -90)
        self.big_front_image = pygame.image.load('cache/%s.jpeg'%self.id)
        self.back_image = pygame.image.load('images/Back_of_Card.jpeg')
        self.big_back_image = pygame.image.load('images/Back_of_Card.jpeg')
        self.image = self.back_image
        self.revealed = False
        self.expanded = False
        self.player_id = player_id
        self.pos_id = [player_id, 'land', 5]  #library location
        self.x = self.y = 0
        self.update()
        self.image.unlock()
        self.p = self.power      # current power
        self.t = self.toughness  # current toughness
        self.p_temp = 0  # power buff until end of turn
        self.t_temp = 0  # toughness buff until end of turn
        self.token  = False
        self.buttons = []

    def expand(self):
        self._layer = 4
        self.groups = expanded_group
        self.y = self.h/2
        self.x = self.w/2
        if self.revealed:
            self.image = self.big_front_image
        else:
            self.image = self.big_back_image
        self.position = (int(self.x), int(self.y))
        self.rect = self.image.get_rect()
        self.rect.center = self.position
        self.buttons.append(Button('exile_card', len(self.buttons), self.screen_size))
        if self.pos_id[1] == 'hand':
            self.buttons.append(Button('discard_card', len(self.buttons), self.screen_size))
            self.buttons.append(Button('play_card', len(self.buttons), self.screen_size))
        elif self.pos_id == [0, 'land', 5] or self.pos_id == [1, 'land', 5]:  # then a library
            self.buttons.append(Button('discard_card', len(self.buttons), self.screen_size))
            self.buttons.append(Button('scry', len(self.buttons), self.screen_size))
            self.buttons.append(Button('rearrange', len(self.buttons), self.screen_size))
            self.buttons.append(Button('draw_card', len(self.buttons), self.screen_size))
        else:
            if self.pos_id[1] == 'land' or self.pos_id[1] == 'battlefield':
                self.buttons.append(Button('send_to_graveyard', len(self.buttons), self.screen_size))
                self.buttons.append(Button('add_counter', len(self.buttons), self.screen_size))
                self.buttons.append(Button('remove_counter', len(self.buttons), self.screen_size))
                self.buttons.append(Button('untap_card', len(self.buttons), self.screen_size))
                self.buttons.append(Button('tap_card', len(self.buttons), self.screen_size))
        self.pos_id[0] = 3

    def shrink(self):
        self._layer = 3
        self.groups = card_group
        if self.revealed:
            self.image = self.front_image
        else:
            self.image = self.back_image
        self.pos_id[0] = self.player_id
        for button in self.buttons:
            button.kill()
        self.buttons = []
        self.update()

    def update(self, spot=None):
        if self.expanded:
            if self.revealed:
                self.image = self.big_front_image
            else:
                self.image = self.big_back_image
        else:
            if self.tapped:
                self.image = self.tapped_image
        #else:
        #if True:
        #    if self.revealed:
        #        self.image = self.front_image
        #    else:
        #        self.image = self.back_image
        player = self.pos_id[0]
        loc  = self.pos_id[1]
        if spot == None:
            spot = self.pos_id[2]
        else:
            self.pos_id[2] = spot
        if player == 3:
            self.x = self.w/2
            self.y = self.h/2
        else:
            self.x = self.grid_width * ((spot % (self.grid_number)) + 0.5)
            self.y = sum(self.loc_id[loc][player]) / 2
        self.position = (int(self.x), int(self.y))
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def reveal(self):
        self.revealed = True
        self.image = self.front_image
        self.image.unlock()

    def hide(self):
        self.revealed = False
        self.image = self.back_image
        self.image.unlock()

    def tap(self):  # this method taps the card
        self.tapped = True
        self.image = self.tapped_image
        self.image.unlock()

    def untap(self):  # this method untaps the card
        self.tapped = False
        self.image = self.front_image
        self.image.unlock()

    def return_card(self):  # run this method after card is returned to owner
        self.owner = True

    def end_sickness(self):
        self.summoning_sickness = False

    def counter_plus(self):  # puts a +1,+1 counter on card
        pass

    def counter_minus(self):  # puts a -1,-1 counter on card
        pass

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
        #h = float(self.tapped_image.get_height())
        #w = float(self.tapped_image.get_width())
        #size = np.array([1, h/w])*screen_height/6*0.95
        #self.tapped_image = pygame.transform.scale(self.tapped_image, (int(size[0]), int(size[1])))
        self.tapped_image = pygame.transform.rotate(self.front_image, -90)


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
        if 'Creature' in params[1]:
            self.cards.append(Creature(params, player_id, screen_size, host))
        else:
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


class Lands(Position):
    def __init__(self):
        Position.__init__(self)
        self.land_type = {}
        self.land_key = []

    def reset_field(self):
        threads = []
        for type in self.land_types.keys():
            t = threading.Thread(target=self.land_type[type].reset_field)
            threads.append(t)
            t.start()

    def add_land_type(self, name):
        self.land_type[name] = BasicLand(len(self.land_type.keys()))
        self.land_key.append(name)


class BasicLand(Battlefield):
    def __init__(self, spot):
        Battlefield.__init__(self)
        self.spot = spot

    def tap_land(self):
        for card in self.cards:
            if card.tapped == False:
                card.tap()
                break

    def untap_land(self):
        for card in self.cards:
            if card.tapped == True:
                card.untap()
                break

    def update(self):
        for card in self.cards:
            card.pos_id[2] = self.spot


class Player(object):
    def __init__(self, deck, id, screen_size, host=True):
        self.id = id
        self.screen_size = screen_size
        self.host = host
        self.health = Health(20, id, screen_size)
        self.location = {'library':     Library(),
                         'hand':        Position(),
                         'battlefield': Battlefield(),
                         'land':        Lands(),
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
            max_hand_size = self.screen_size[0]/(self.screen_size[1]/6)
            if len(self.location['hand'].cards) < max_hand_size:
                card = self.location['library'].cards[0]
                if self.host:
                    card.reveal()
                card.pos_id[1] = 'hand'
                card.pos_id[2] = len(self.location['hand'].cards)
                self.location['hand'].cards.append(card)
                self.location['library'].remove_card(0)
                card.update()

    def rearrange(self, n=3):
        pass

    def scry(self, n=1):
        pass

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
    def __init__(self, screen_size, deck1, deck2, game_seed, host=True):
        global card_group, selector_group
        #set up screen
        self.screen_size = screen_size
        width = screen_size[0]
        height = screen_size[1]
        self.screen = Screen(screen_size, True)
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
        self.selector = Selector(self.screen_size, self.host)
        selector_group = pygame.sprite.RenderPlain(self.selector)
        selector_group.draw(self.screen.screen)

        # Sets up player's and their decks
        self.player = [Player(deck1, 0, self.screen_size, self.host),
                       Player(deck2, 1, self.screen_size, not self.host)]  # player[0] is host and player[1] is guest
        self.rescale_images()

        for i in range(2):
            # set up card sprites
            card_group[i] = pygame.sprite.RenderPlain(self.player[i].location['library'].cards)
            # Sets up player's health
            health_group[i] = pygame.sprite.RenderPlain(self.player[i].health)

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
        global selector_group, button_group, card_group, health_group, expanded_group
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
                    health_group[i].update()
                    self.screen.screen.blit(self.player[i].health.text, self.player[i].health.position)
                if button_group != None:
                    button_group.update()
                    button_group.draw(self.screen.screen)
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
        card.reveal()
        #self.stack.cards.append(card)
        #self.player[p].location['stack'].cards.append(card)
        if 'Land' in card.type[0]:
            if card.name in set(self.player[p].location['land'].land_type.keys()):
                self.player[p].location['land'].land_type[card.name]
            else:
                self.player[p].location['land'].add_land_type(card.name)
            card.pos_id[1] = 'land'
            self.player[p].location['land'].land_type[card.name].cards.append(card)
            self.player[p].location['land'].land_type[card.name].update()
        else:
            cards = self.player[p].location['battlefield'].cards
            card.pos_id[1] = 'battlefield'
            card_names = []
            for c in cards:
                card_names.append(c.name)
            #if card.name in set(card_names):
            #    for c in cards:
            #        if card.name == c.name:
            #            card.pos_id[2] = c.pos_id[2]
            #            break
            #else:
            #    card.pos_id[2] = len(set(card_names))
            ##
            card.pos_id[2] = len(card_names)
            ##
            cards.append(card)

        self.player[p].location['hand'].remove_card(index)
        card.update()
        threads = []
        for i in range(len(hand)):
            t = threading.Thread(target=hand[i].update, args=(i,))
            threads.append(t)
            t.start()

    def discard_card(self, card, index, pos_id, exiled=False):
        send_to = 'graveyard'
        if exiled: send_to = 'exiled'
        self.player[pos_id[0]].location[send_to].cards.append(card)
        card.pos_id = [pos_id[0], 'land', 6+exiled]
        if pos_id[1] == 'land' and pos_id[2] == 5:
            self.player[pos_id[0]].location['library'].remove_card(index)
            card.reveal()
        elif pos_id[1] == 'land' and pos_id[2] == 6:
            self.player[pos_id[0]].location['graveyard'].remove_card(index)
        elif pos_id[1] == 'land' and pos_id[2] == 7:
            self.player[pos_id[0]].location['exiled'].remove_card(index)
        else:
            self.player[pos_id[0]].location[pos_id[1]].remove_card(index)
        card.update()
        threads = []
        for i in range(len(self.player[pos_id[0]].location[pos_id[1]].cards)):
            t = threading.Thread(target=self.player[pos_id[0]].location[pos_id[1]].cards[i].update, args=(i,))
            threads.append(t)
            t.start()

    #def expand_card(self):

    def action(self):
        global selector_group, button_group, card_group, health_group, expanded_group
        pos_id = self.selector.pos_id
        # if health selected
        self.expanded_running = True
        if pos_id[2] == 9 and pos_id[1] == 'land':
            blink = 0
            try:
                while self.expanded_running:
                    deltat = self.clock.tick(self.fps)
                    blink = blink + deltat
                    if blink > 400:
                        blink = 0
                        self.selector.color[0] = (self.selector.color[0] + 200) % 400
                    for event in pygame.event.get():
                        if not hasattr(event, 'key'): continue
                        if not event.type == KEYDOWN: continue
                        if event.key == K_UP: self.player[pos_id[0]].health.heal_one()
                        elif event.key == K_DOWN: self.player[pos_id[0]].health.damage_one()
                        elif event.key == K_ESCAPE or K_RETURN: self.expanded_running = False
                    # Rendering
                    self.screen.screen.fill((0, 0, 0,))
                    selector_group.update()
                    selector_group.draw(self.screen.screen)
                    for i in range(2):
                        card_group[i].update()
                        card_group[i].draw(self.screen.screen)
                        health_group[i].update()
                        self.screen.screen.blit(self.player[i].health.text, self.player[i].health.position)
                    if button_group != None:
                        button_group.update()
                        button_group.draw(self.screen.screen)
                    pygame.display.flip()
            except KeyboardInterrupt:
                print 'user quit'
        # if card selected
        else:
            #spot_mod = self.screen_size[0]/(self.screen_size[1]/6)
            #if pos_id[1] == 'land' and pos_id[2] == (-3 % spot_mod):  # then player's library
            if pos_id[1] == 'land':
                if pos_id[2] == 5:
                    if len(self.player[pos_id[0]].location['library'].cards) > 0:
                        card = self.player[pos_id[0]].location['library'].cards[0]
                        index = 0
                    else:
                        self.expanded_running = card = False
                elif pos_id[2] == 6:
                    if len(self.player[pos_id[0]].location['graveyard'].cards) > 0:
                        card = self.player[pos_id[0]].location['graveyard'].cards[0]
                        index = 0
                    else:
                        self.expanded_running = card = False
                elif pos_id[2] == 7:
                    if len(self.player[pos_id[0]].location['exiled'].cards) > 0:
                        card = self.player[pos_id[0]].location['exiled'].cards[0]
                        index = 0
                    else:
                        self.expanded_running = card = False
                else:
                    if len(self.player[pos_id[0]].location['land'].land_type) > 0:
                        land_key = self.player[pos_id[0]].location['land'].land_key[pos_id[2]]
                        card = self.player[pos_id[0]].location['land'].land_type[land_key].cards[-1]
                        index = None
                    else:
                        self.expanded_running = card = False
            else:
                index = pos_id[2]
                if index < len(self.player[pos_id[0]].location[pos_id[1]].cards):
                    #self.play_card(index, p)
                    card = self.player[pos_id[0]].location[pos_id[1]].cards[index]
                else:
                    self.expanded_running = card = False
            if card:
                card.expand()
                expanded_group = pygame.sprite.RenderPlain(card)
                button_group = pygame.sprite.RenderPlain(card.buttons)
                button_group.draw(self.screen.screen)
                buttons_length = len(card.buttons)
                self.subselector = SubSelector(self.screen_size, buttons_length)
                selector_group = pygame.sprite.RenderPlain(self.subselector)
                selector_group.draw(self.screen.screen)
            try:
                while self.expanded_running:
                    deltat = self.clock.tick(self.fps)
                    for event in pygame.event.get():
                        if not hasattr(event, 'key'): continue
                        if not event.type == KEYDOWN: continue
                        if event.key == K_RIGHT: self.subselector.move_right()
                        elif event.key == K_LEFT: self.subselector.move_left()
                        elif event.key == K_UP: self.subselector.move_up()
                        elif event.key == K_DOWN: self.subselector.move_down()
                        elif event.key == K_RETURN: self.subaction(card, index, pos_id)
                        elif event.key == K_ESCAPE: self.expanded_running = False
                    # Rendering
                    self.screen.screen.fill((0, 0, 0,))
                    for i in range(2):
                        card_group[i].update()
                        card_group[i].draw(self.screen.screen)
                        health_group[i].update()
                        self.screen.screen.blit(self.player[i].health.text, self.player[i].health.position)
                    selector_group.update()
                    selector_group.draw(self.screen.screen)
                    if button_group != None:
                        button_group.update()
                        button_group.draw(self.screen.screen)
                    expanded_group.update()
                    expanded_group.draw(self.screen.screen)
                    pygame.display.flip()
                if card:
                    card.shrink()
                    card.update()
                    self.subselector.kill()
            except KeyboardInterrupt:
                print 'user quit'
            self.selector.update()
            selector_group = pygame.sprite.RenderPlain(self.selector)
            selector_group.draw(self.screen.screen)

    def subaction(self, card, index, pos_id):
        for button in card.buttons:
            if self.subselector.position[0] in set(range(button.position[0]-5, button.position[0]+5)):
                if self.subselector.position[1] in set(range(button.position[1]-5, button.position[1]+5)):
                    name = button.name
                    break
        if name == 'exile_card': self.discard_card(card, index, pos_id, exiled=True)
        elif name == 'discard_card': self.discard_card(card, index, pos_id)
        elif name == 'scry': self.player[pos_id[0]].scry()
        elif name == 'rearrange': self.player[pos_id[0]].rearrange()
        elif name == 'draw_card': self.player[pos_id[0]].draw_card()
        elif name == 'play_card': self.play_card(index, pos_id[0])
        elif name == 'send_to_graveyard': self.discard_card(card, index, pos_id)
        elif name == 'tap_card':
            if pos_id[1] == 'land':
                self.player[pos_id[0]].location['land'].land_type[card.name].tap_land()
            else:
                card.tap()
        elif name == 'untap_card': card.untap()
        elif name == 'add_counter': card.counter_plus()
        elif name == 'remove_counter': card.counter_minus()
        card.shrink()
        self.expanded_running = False

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
    def __init__(self, screen_size, fullscreen=False):
        #set up screen
        self.width       = int(screen_size[0])  # width of screen in pixels
        self.height      = int(screen_size[1]) # height of screen in pixels
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
    def __init__(self, screen_size, host, pos_id=None):
        self.groups = selector_group
        self._layer = 2
        pygame.sprite.Sprite.__init__(self)
        self.w      = int(screen_size[0])
        self.h      = int(screen_size[1])
        hand        = [(0,        self.h/6),   # player 0  # hand[player][init/final]
                       (5*self.h/6, 6*self.h/6)]   # player 1  # middle is sum(hand[player])/2
        land        = [(self.h/6,   2*self.h/6),
                       (4*self.h/6, 5*self.h/6)]
        battlefield = [(2*self.h/6, 3*self.h/6),
                       (3*self.h/6, 4*self.h/6)]
        self.location = {'hand':        hand,
                         'land':        land,
                         'battlefield': battlefield}
        self._layer = 0
        h = self.h/6
        self.grid_number = 10
        self.grid_width = w = self.w/self.grid_number
        self.image = pygame.Surface((w, h))
        self.color = [200, 0, 0]
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        pos_id = [0, 'land', 7]
        if not host:
            pos_id[0] = 1
        if not pos_id == None:
            self.pos_id = pos_id
        self.update()


    def update(self):
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        player = self.pos_id[0]
        loc    = self.pos_id[1]
        spot   = self.pos_id[2]
        self.y = sum(self.location[loc][player]) / 2
        self.x = self.grid_width * ((spot % self.grid_number) + 0.5)
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


class SubSelector(pygame.sprite.Sprite):
    def __init__(self, screen_size, buttons_length):
        self.groups = selector_group
        self._layer = 2
        pygame.sprite.Sprite.__init__(self)
        self.transformed = False
        self.w      = float(screen_size[0])
        self.h      = float(screen_size[1])
        self.buttons_length = buttons_length
        self._layer = 0
        transformed_size = np.array([4, 1]) * self.w/20
        self.image = pygame.Surface(transformed_size)
        self.color = [200, 0, 0]
        self.x = self.w*(7./10)
        self.y = (self.h/12.)*(1+buttons_length)
        self.update()

    def update(self):
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        self.position = (int(self.x), int(self.y))
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def move_right(self):
        self.x = self.w - self.x
        self.update()

    def move_left(self):
        self.x = self.w - self.x
        self.update()

    def move_up(self):
        self.y = self.y - self.h/12.
        if self.y == self.h/12.:
            self.y = (self.h/12.)*(1+self.buttons_length)
        self.update()

    def move_down(self):
        self.y = self.y + self.h/12.
        if self.y == self.h/12.*(2+self.buttons_length):
            self.y = (self.h/12.)*2
        self.update()