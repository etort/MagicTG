import pickle
import csv
import sys

def load_deck(raw_deck):
    path = 'Decks/'
    with open(path+raw_deck, 'rt') as f:
        reader = csv.reader(f, delimiter=',', skipinitialspace=True)
        linedata = list()
        cols = next(reader)
        for col in cols:
            linedata.append(list())
        for line in reader:
            linedata[0].append(line[0].replace('\xe2\x80\x99',"'"))
            linedata[1].append(int(line[1]))
        data = dict()
        for i in range(len(linedata[0])):
            data[linedata[0][i]] = linedata[1][i]
    return data


def get_card_info(card_name):
    path = 'Card_Dictionary/'
    cards_info = pickle.load(open(path+'%s_info_dict.pkl'%card_name[:2]))
    card_index = cards_info['names'].index(card_name)
    keys = ['names', 'ids', 'types', 'texts', 'costs', 'powers', 'toughs']
    card = {}
    for key in keys:
        card[key] = cards_info[key][card_index]
    return card


def create_deck(deck_data):
    deck = {'names':  [],
            'ids':    [],
            'types':  [],
            'texts':  [],
            'costs':  [],
            'powers': [],
            'toughs': [] }

    for card_name in deck_data:
        card = get_card_info(card_name)
        for key in deck.keys():
            deck[key].append(card[key])
    return deck


def export_deck(deck, deck_name):
    path = 'Decks/Deck_Data/'
    pickle.dump(deck, open(path+deck_name+'.pkl', 'wb'))


if __name__ == '__main__':

    deck_name = 'Deck_Example'

    if len(sys.argv) > 1:
        deck_name = sys.argv[1]

    deck_raw = deck_name + '.txt'

    data = load_deck(deck_raw)
    deck = create_deck(data)
    export_deck(deck, deck_name)