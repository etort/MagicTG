"""
5/3/15 defines classes that will be used
"""
import random2
import threading
import pygame
import time

random2 = random2.Random2()


class Card(object):
    def __init__(self, params):  # [name, type, id, cost, power, toughness, text, location]
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
        self.p = self.power     # current power
        self.t = self.toughness # current toughness
        self.p_temp = 0  # power buff until end of turn
        self.t_temp = 0  # toughness buff until end of turn
        self.token  = False

    def tap(self): # this method taps the card
        self.tapped = True

    def untap(self): # this method untaps the card
        self.tapped = False

    def return_card(self): # run this method after card is returned to owner
        self.owner = True

    def end_sickness(self):
        self.can_attack = True


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

    def seed_card(self, params):  # [name, type, id, cost, power, toughness, text]
        self.cards.append(Card(params))

    def remove_card(self, index):
        del self.cards[index]


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
    def __init__(self, deck, seed):
        location_keys = ['library', 'hand', 'battlefield', 'land', 'graveyard', 'exiled', 'stack']
        location_list = [Position(), Position(), Battlefield(), Battlefield(), Position(), Position(), Position()]
        self.location = dict(zip(location_keys, location_list)) # locations for cards
        self.mana = { 'w': 0,
                      'k': 0,
                      'b': 0,
                      'g': 0,
                      'r': 0,
                      'c': 0  }
        self.cards = []
        card_keys = ['names', 'types', 'ids', 'costs', 'powers', 'toughs', 'texts']
        for i in range(len(deck['names'])):
            self.location['library'].cards.seed_card([deck[key][i] for key in card_keys]) # seed library
        self.shuffle_lib(seed)

    def draw_card(self):
        self.location['hand'].cards.append(self.location['library'][0])
        self.location['library'].remove_card(0)

    def add_mana(self, color):
        self.mana[color] = self.mana[color] + 1

    def rem_mana(self, color):
        self.mana[color] = self.mana[color] - 1

    def shuffle_lib(self, seed):
        self.shuffle(self, seed)
        self.cut(self, seed)
        self.shuffle(self, seed)
        self.cut(self, seed)

    def shuffle(self, seed):
        random2.shuffle(self.location['library'].cards, seed)

    def cut(self, seed):
        # cuts the deck at a random spot in the middle 3rd of the deck
        # 1/2*len(cards) +/- 1/3*len(cards)
        lower_bound = int(len(self.location['library'].cards)/2) - int(len(self.location['library'].cards)/3)
        spot = lower_bound + int(random2.random(seed)*len(self.location['library'].cards)/3)
        self.cards = self.location['library'].cards[spot:].extend(self.location['library'].cards[:spot])


class God(object):
    def __init__(self, width, height, deck1, deck2, seed, host=True):
        self.screen = Screen(width, height)
        self.clock = pygame.time.Clock()
        self.fps = 30
        self.deltat = self.clock.tick(self.fps)
        self.host = host  # True if hosting, False if guest
        self.seed = seed
        self.player = [Player(deck1, seed), Player(deck2, seed)] # player[0] is host and player[1] is guest
        self.stack = Position()
        self.turn = 0   # integer values for host, half integer values for guest
        self.phase = 0  # phase of battle: 'beginning', 'first main', 'combat', 'second main', 'end'
        self.who = 0
        self.done = False

    def new_seed(self):
        random2.next_seed(self.seed)

    def play_card(self, index, p=0):
        card = self.player[p].location['hand'].cards[index]
        self.stack.cards.append(card)
        self.player[p].location['stack'].cards.append(card)
        self.player[p].location['hand'].remove_card(index)

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
    def __init__(self, width, height):
        self.card_size   = (223, 310)  # standard size of cards in pixels (x, y)

        #set up screen
        self.width       = int(width)  # width of screen in pixels
        self.height      = int(height) # height of screen in pixels
        self.screen      = pygame.display.set_mode((self.width, self.height))
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
