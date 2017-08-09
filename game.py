"""
This script builds a game of Pandemic

use this to open this script in the interactive shell:
exec( open( 'game.py', 'r' ).read() )
"""

import argparse
import cmd
import csv
import logging
import os
import random
import sys
import textwrap

# LOGGER
logging.basicConfig(stream=sys.stderr) # , level=logging.DEBUG
logger = logging.getLogger(__name__)

# SCREEN
SCREEN_WIDTH = 80
LOGO = """
|||||||||||||||||||||||||||||||||||
||                               ||
||  |¯_) /\ |\ ||¯¯\|_¯|\/||/¯¯  ||
||  |   /--\| \||__/|__|  ||\__  ||
||                               ||
|||||||||||||||||||||||||||||||||||
"""

# GAME ENGINE
CITY_CARDS = 48
EPIDEMIC = 'epidemic'
HAND_LIMIT = 7
ROLES = ['contingency planner',
         'operations expert',
         'dispatcher',
         'quarantine specialist',
         'medic',
         'researcher',
         'scientist']
EVENT_CARDS = ['government grant',
               'resilient population',
               'one quiet night',
               'airlift',
               'forecast']

gs = {} # holds the global game state

class City:

    """
    Foundation class of a city
    """

    def __init__(self, data):
        self.name = data[0]
        self.color = data[1]
        self.population = data[2]
        self.connections = data[3]
        self.disease_cubes = {
            'red' : 0,
            'blue' : 0,
            'black' : 0,
            'yellow' : 0
        }
        self.pawns = []
        self.research_station = False

    def __repr__(self):
        # need to fix indenting, but this works
        text = """{name}:
         Color: {color}
         Pawns: {pawns}
         Connections: {conn}
         Disease Cubes: {discubes}
         Research Station: {rstation}
         Population: {pop}
         """.format(name=self.name, color=self.color, pawns=self.pawns,
                    conn=self.connections, discubes=self.disease_cubes,
                    rstation=self.research_station, pop=self.population)
        return text

class GameState:

    """
    Maintains the board state and controls the game state
    """

    def __init__(self):
        """
        Builds the board state
        """

        # Player tracking
        self.player = {} # stores information about each player
        self.player_turn = None
        self.current_player = lambda: self.player[self.player_turn]
        self.dt = lambda: self.cities[self.current_player().location].connections

        # controls
        self.difficulty = None # the number of epidemics shuffled into the player deck
        self.player_count = None

        # board state
        self.cities = {} # will be loaded with city information by city_loader
        self.research_stations = 1 # Atlanta initially
        self.epidemic_cards_left = None
        self.event_cards_left = None

        # player deck
        self.player_deck = []
        self.player_discard_deck = []
        self.pds = lambda: len(self.player_deck) # player_deck_size
        self.pdds = lambda: len(self.player_discard_deck) # player_discard_deck_size

        # infection cards
        self.infection_deck = []
        self.infection_discard_deck = []
        self.ids = lambda: len(self.infection_deck) # infection deck size
        self.idds = lambda: len(self.infection_discard_deck) # infection discard deck size

        # These numbers change based on the board state
        self.cubes_in_storage = {'blue': 24, 'red': 24, 'yellow': 24, 'black': 24}

        # Current infection rate, and position of it
        self.infection_rate = 2

        # 7 total positions where {positions} -> rate
        # {1, 2, 3} -> 2, {4, 5} -> 3, {6, 7} -> 4
        self.infection_rate_position = 1

        # how many outbreaks are there?
        self.outbreaks = 0

        # 0 = no cure, 1 = cure, 2 = eradicated
        self.cures = {'red': 0, 'blue': 0, 'yellow': 0, 'black': 0}

    """
    These are general actions players can make to impact the global state.
    """
    def end_turn(self):
        """
        Changes the position of the current turn
        """
        self.draw_player_cards()
        # we + 1 at the end to ensure we're 1 indexed
        self.player_turn += (self.player_turn + 1 % len(self.player)) + 1
        self.draw_infection_cards()

    def draw_player_cards(self):
        """
        The player who's turns up draws two cards
        """

        if len(self.player_deck) < 2:
            self.lose_game()

        # draws
        draw1 = self.player_deck.pop(0)
        draw2 = self.player_deck.pop(0)

        print(draw1, draw2)

        # Check for any conditions
        if draw1 == EPIDEMIC:
            self.epidemic()
            draw1 = ''

        if draw2 == EPIDEMIC:
            self.epidemic()
            draw2 = ''

        if 2 + len(self.current_player().cards) > HAND_LIMIT:
            # prompt user to pick a card to remove, including 1 just picked up
            # or if there is an event card, can use it
            pass

        # Save cards
        if draw1:
            self.current_player().cards.append(draw1)
        if draw2:
            self.current_player().cards.append(draw2)

    def draw_infection_cards(self):
        # TODO: Make it pull out as many infection cards as the infection
        #       rate specifies, and infect those cities, causing outbreaks
        #       if needed.
        pass


    def infect_city(self, city, color='', cubes=1):
        """
        Infects a city
        """

        if city in self.cities:
            city = self.cities[city]
        else:
            raise ValueError('Can\'t find the city : {0}'.format(city))

        logger.debug('Before Infection: %s : %s', city.name, city.disease_cubes)

        # print(city)
        if color:
            if city.disease_cubes[color] + cubes > 3:
                self.outbreak(city, color)
            else:
                city.disease_cubes[color] += cubes
        else:
            if city.disease_cubes[city.color] + cubes > 3:
                self.outbreak(city, city.color)
            else:
                city.disease_cubes[city.color] += cubes

        logger.debug('After Infection : %s : %s', city.name, city.disease_cubes)

    def outbreak(self, city='', color=''):
        """
        Causes an outbreak in a given city
        """
        # TODO
        pass

    def epidemic(self, city='', color=''):
        """
        Causes an epidemic in a given city
        """
        # TODO
        pass

    def lose_game(self, city='', color=''):
        """
        Shows last remainding cards and any screens
        """
        # TODO
        pass

    def where_to(self):
        """
        This gives us the possible locations the current player can go.
        """
        return self.cities[self.current_player().location].connections

class Player:

    """
    Maintains the state of each character and controls
    """

    def __init__(self, location='atlanta', cards=[], role='', actions_left=4, turn_position=1):
        self.location = location
        self.cards = cards
        self.role = role
        self.actions_left = actions_left

        """ TODO : Describe the turn positions & logic for them
        - 1 = waiting
        - 2 = ??
        """
        self.turn_position = turn_position

    """
    Movement Actions
      These functions control how the player moves from space to space. They
      provide the base movement for all the roles. They'll be used by a
      movement action function that performs any extra checks to ensure the
      validity of the move. These functions can be swapped depending on the
      player's role.
    """

    def drive(self, _to):
        """
        This drives a player to a location
        """
        # is it connected to the city i'm in?
        if _to in gs.cities[self.location].connections:
            self.location = _to
            self.reduce_action()
        else:
            return "{0} isn\'t connected to {1}".format(self.location, _to)

    def charter_flight(self, _to):
        """
        """
        # is your location in any of the cards you're holding?
        if self.location in self.cards:
            self.remove_card(_to)
            self.location = _to
            self.reduce_action()
        else:
            raise ValueError("You don't have {0} to use charter flight.".format(self.location))

    def direct_flight(self, _to):
        """
        """
        # is desired location in any of the cards you're holding?
        if _to in self.cards:
            self.remove_card(_to)
            self.location = _to
            self.reduce_action()
        else:
            raise ValueError("You don't have {0} to use direct flight.".format(_to))

    def shuttle_flight(self, _to):
        """
        """

        # does my location and the desired location have a research station?
        if gs.cities[self.location].research_station:
            if gs.cities[_to].research_station:
                self.location = _to
                self.reduce_action()
            else:
                raise ValueError("{0} doesn't have a research station".format(_to))
        else:
            raise ValueError("You're not on a research station")

    """
    Other Actions
      These functions control the other actions the players have access to.
      These functions can be swapped depending on the role of the player.
      player's role.
    """

    def build_research_station(self, move_from=''):
        """
        """

        for card in self.cards:
            if card == self.location:
                if gs.cities[self.location].research_station != True:
                    if gs['research_stations'] < 6:
                        gs.cities[self.location].research_station = True
                        self.remove_card(self.location)
                        self.reduce_action()
                    elif move_from:
                        gs.cities[move_from].research_station = False
                        gs.cities[self.location].research_station = True
                        self.remove_card(self.location)
                        self.reduce_action()
                    else:
                        raise ValueError("""This game has reached it's max limit of research
                                         stations. Give me a location to remove a research
                                         station.""")
                else:
                    raise ValueError("This location already has a research station")
            else:
                raise ValueError("""You don't have the {0} city card to build a research station
                                 here""".format(self.location))

    def treat_disease(self, color=''):
        """
        """
        # can I treat?
        # _total = 0
        # for i in cities[self.location].disease_cubes:
        #     if i > 0:
        #         break

        if color:
            if gs.cities[self.location].disease_cubes[color] > 1:
                gs.cities[self.location].disease_cubes[color] -= 1
                self.reduce_action()
            else:
                raise ValueError("There aren't any {0} disease cubes here".format(color))
        else:
            color = gs.cities[self.location].color
            if gs.cities[self.location].disease_cubes[color] > 1:
                gs.cities[self.location].disease_cubes[color] -= 1
                self.reduce_action()
            else:
                raise ValueError("""There aren't any {0} disease cubes here, specify which color
                                 you want to remove.""".format(color))

    def share_knowledge(self, action, pn, card):
        """
        Share knowledge with a player
          action = 'give' or 'take'
          pn = player number
          card = card within your hand
        """

        # namespace easers
        player = gs.player[pn]

        if self.location == player.location:
            if action == 'give':
                if card in self.cards:
                    self.remove_card(card)
                    player.add_card(card)
                    self.reduce_action()
                else:
                    raise ValueError("Can't find card")
            elif action == 'take':
                if card in player.cards:
                    player.remove_card(card)
                    self.add_card(card)
                    self.reduce_action()
                else:
                    raise ValueError("Can't find card")
            else:
                raise ValueError("Action must be either 'give' or 'take'")
        else:
            raise ValueError("Your not in the same location")


    def discover_cure(self, color, discards):
        """
        """
        if gs.cities[self.location].research_station is True:
            if gs['cures'][color] != 1 or gs['cures'][color] != 2:
                # do I have 5 city cards?
                if len(self.cards) >= 5:
                    # do I have 5 city cards of same color?
                    _total = 0
                    _cards = []
                    for card in self.cards:
                        if gs.cities[card].color == color:
                            _cards.append(card)
                            _total += 1

                    if _total >= 5:
                        if set(_cards).issubset(set(self.cards)):
                            gs['cures'][color] = 1
                            self.reduce_action()
                            for card in discards:
                                self.remove_card(card)

    # Player Controls
    def add_card(self, card):
        self.cards.append(card)

    def remove_card(self, card):
        self.cards.remove(card)

    def reduce_action(self):
        self.actions_left -= 1

def city_loader():
    """
    Returns a dict of all the cities
    """
    logger.info('Started: City Loader')
    cities = {}

    # open csv file of cities and load into memory
    with open('data/cities.csv', 'r') as csvfile:
        cityreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        # reads each new line
        for data in cityreader:
            # splits the connecting cities data point into a list
            data[3] = data[3].split(',')
            # stores the object into the dict
            cities[data[0]] = City(data)

    # removes the header
    cities.pop('city', None)

    ## DEBUGGING
    for i in cities:
        logger.debug(i)

    return cities

def infection_loader():
    """
    Returns a list of tuples of all the cities:
    (city name, color)
    """

    infection_cities = []

    # open csv file of cities and load into memory
    with open('data/cities.csv', 'r') as csvfile:
        cityreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for data in cityreader:
            # clean the data
            data[3] = data[3].split(',')
            # 0 = city name, 1 = city color
            infection_cities.append((data[0], data[1]))

    # removes the header
    infection_cities.pop(0)

    return infection_cities


def clean_setup(players, difficulty):
    """
    Creates a new game by overwriting all the variables in the game state
    """
    logger.info('Started: arg check')

    # make sure players and difficulty is correct
    if players > 4 or players < 2:
        raise ValueError('Players must be between 2-4')

    if difficulty > 6 or difficulty < 4:
        raise ValueError('Difficulty must be between 4-6')
    
    gs.player_count = players
    gs.difficulty = difficulty
    gs.epidemic_cards_left = difficulty

    """
    Role distribution
    """
    logger.info('Started: Role distribution')

    # get a sample from the roles and distribute it to the players
    player_roles = random.sample(ROLES, players)
    for i in range(players):
        i_1 = i+1 # 1 index the player numbers
        gs.player[i_1] = Player()
        gs.player[i_1].role = player_roles[i]

    ## DEBUGGING
    for i in range(players):
        logger.info(' Player %s\'s Role: %s', i+1, gs.player[i+1].role)

    """
    Building the city tracker
    """
    logger.info('Started: Build cities dict')

    gs.cities = city_loader()

    for i in gs.cities:
        logger.debug('%s\n  population:  %s\n  connections: %s\n',
                     i, gs.cities[i].population, gs.cities[i].connections)

    """
    Player city card distribution
    """
    logger.info('Started: Player city card distribution')

    if players == 2:
        cards_per_player = 4
    elif players == 3:
        cards_per_player = 3
    elif players == 4:
        cards_per_player = 2

    # get random samples of cards
    player_cards = random.sample(list(gs.cities) + list(EVENT_CARDS), cards_per_player*players)

    # store which cards remain left in the main player deck
    remaining_cards = [x for x in gs.cities if x not in player_cards]

    # get each player's card deck
    card_deck = [player_cards[i:i + cards_per_player]
                 for i in range(0, len(player_cards), cards_per_player)]

    # store each player their card deck
    for index, deck in enumerate(card_deck):
        gs.player[index+1].cards = deck

    ## DEBUGGING
    for k,v in gs.player.items():
        logger.debug(' Player %s Cards: %s', k, v.cards)
    logger.debug(' Should be empty if nothing went wrong: %s',
                 set(player_cards).intersection(set(remaining_cards)))

    """
    Who goes first?
    """
    logger.info('Started: Determine who goes first')

    player_pops = []

    for pn in list(gs.player):
        pops = []
        for city in gs.player[pn].cards:
            # build list of populations for each player's cards
            if city in gs.cities: # make sure it's not an event card
                pops.append(int(gs.cities[city].population))
        logger.debug('Population for player %s: %s', pn, pops)
        # default to 0 just in case a player has all event cards
        player_pops.append(max(pops, default=0))

    ## check which player has largest population
    goes_first = player_pops.index(max(player_pops)) + 1 # +1 to reset index
    gs.player_turn = goes_first

    ## DEBUGGING
    logger.info(' Player %s goes first', goes_first)
    logger.debug('Populations that were maxed: %s', player_pops)

    """
    Build infection deck
    """
    logger.info('Started: Build infection deck')

    # build infection deck
    infection_deck = infection_loader()
    gs.infection_deck = random.sample(infection_deck, len(infection_deck)) # save state

    # disease disribution - disease chosen cities from infection pile
    # get first 3 of infection deck
    a, b, c = gs.infection_deck[:3], gs.infection_deck[4:7], gs.infection_deck[8:11]
    for i in a:
        # i[0] is city name, i[1] is city color
        gs.infect_city(i[0], i[1], 3)
    for i in b:
        gs.infect_city(i[0], i[1], 2)
    for i in c:
        gs.infect_city(i[0], i[1], 1)

    gs.infection_discard_deck = gs.infection_deck[:11]
    del gs.infection_deck[:11]

    ## DEBUGGING
    logger.info(' Infected Cities with 3: %s', a)
    logger.info(' Infected Cities with 2: %s', b)
    logger.info(' Infected Cities with 1: %s', c)
    logger.debug(' Infected City Deck: %s %s', len(gs.infection_deck), gs.infection_deck)
    logger.debug(' Infected Discard Deck: %s %s',
                 len(gs.infection_discard_deck), gs.infection_discard_deck)

    """
    Put research station on Atlanta
    """
    # set beginning research station ( to atlanta )
    gs.cities['atlanta'].research_station = True

    """
    Player deck prep:
    Based on difficulty, it shuffles chunks of the player deck evenly
    """
    logger.info('Started: Player deck prep')

    # get n nearly equal chunks
    partitions = partition(remaining_cards, difficulty)
    epi_partitions = []

    for i, d in enumerate(partitions):
        d.append(EPIDEMIC) # add epidemic card
        logger.debug(' Before Epidemic: %s %s', len(d), d)
        epi_partitions.append(random.sample(d, len(d))) # shuffle this deck
        logger.debug(' After  Epidemic: %s %s', len(epi_partitions), epi_partitions[i])

    # concat to form player deck
    player_deck = []
    for i in epi_partitions:
        player_deck += i

    # store deck
    gs.player_deck = player_deck

    ## DEBUGGING
    logger.debug(' Original Partitions :')
    for i in partitions:
        logger.debug('  %s %s', len(i), i)

    logger.debug(' Epidemic Partitions :')
    for i in epi_partitions:
        logger.debug('  %s %s', len(i), i)

    logger.debug(' Player_deck')
    logger.debug('  %s', player_deck)

    """
    We made it home boys, say hi.
    """

    print_welcome_message(a, b, c)

    return gs


def partition(lst, n):
    """
    Create a new list of n nearly equal chunks

    Shamelessly taken from:
      http://stackoverflow.com/questions/2659900/python-slicing-a-list-into-n-nearly-equal-length-partitions
    """
    division = len(lst) / n
    return [lst[round(division * i):round(division * (i + 1))] for i in range(n)]

def print_welcome_message(d3, d2, d1):
    """
    Prints the welcome message to a clean game
    """
    print(LOGO, '\n')
    print('WELCOME TO PANDEMIC!\n')
    print('Do you have what it takes to save humanity? Let\'s find out!')
    print('Here\'s everything you need to get started:\n')
    print(' The infected cities:\n\n  3 cubes : {d3}\n  2 cubes : {d2}\n  1 cube  : {d1}\n'
          .format(d3=d3, d2=d2, d1=d1))
    print('Here are the player hands:\n')
    for i in gs.player:
        print('  Player {i}:'.format(i=i))
        print('    Role : {role}'.format(role=gs.player[i].role))
        print('    Cards: {cards}\n'.format(cards=gs.player[i].cards))
    print('Player {first} goes first. Good luck!'.format(first=gs.player_turn))

def print_end_turn():
    """
    Prints the gameboard and stuff
    """
    print(LOGO, '\n')
    print("Player {}'s turn ".format(gs.player_turn))
    print(' Here are the player hands:\n')
    for i in gs.player:
        print('  Player {i}:'.format(i=i))
        print('    Role : {role}'.format(role=gs.player[i].role))
        print('    Cards: {cards}\n'.format(cards=gs.player[i].cards))


def clear_screen():
    """Helper function that clears the screen using either program"""
    os.system('cls' if os.name == 'nt' else 'clear')

class PandemicCmd(cmd.Cmd):
    prompt = '\n> '

    # The default() method is called when none of the other do_*() command methods match.
    def default(self, arg):
        print('I do not understand that command. Type "help" for a list of commands.')

    def emptyline(self):
        pass

    def precmd(self, line):
        # clear_screen()
        return line

    # def postcmd(self, stop, line):
    #     return line


    def do_quit(self, arg):
        """Quit the game."""
        return True # this exits the Cmd application loop in TextAdventureCmd.cmdloop()

    """
    These are the commands used to control the current player
    """
    def do_drive(self, loc):
        """Drive to a connected location"""
        gs.current_player().drive(loc)
        self.do_connections()

    def do_direct_flight(self, loc):
        """Go to the area to the south, if possible."""
        gs.current_player().direct_flight(loc)

    def do_charter_flight(self, loc):
        """Go to the area to the east, if possible."""
        gs.current_player().charter_flight(loc)

    def do_shuttle_flight(self, loc):
        """Go to the area to the west, if possible."""
        gs.current_player().shuttle_flight(loc)

    def do_build_research_station(self):
        """Go to the area upwards, if possible."""
        gs.current_player().build_research_station()

    def do_treat_disease(self, arg):
        """Go to the area downwards, if possible."""
        gs.current_player().treat_disease()

    def do_share_knowledge(self, arg):
        """Go to the area downwards, if possible."""
        gs.current_player().share_knowledge()

    def do_discover_cure(self, arg):
        """Discovers a cure, if possible."""
        gs.current_player().discover_cure()

    def do_end_turn(self):
        """Ends turn"""
        # TODO
        print_end_turn()
        pass

    def do_connections(self, city=''):
        """Prints the current connections the current player is in, or for a city"""
        if city:
            print(gs.cities[city].connections)
        else:
            print(gs.cities[gs.current_player().location].connections)

    def help_combat(self):
        print('Combat is not implemented in this program.')

def main():

    """
    Sets up conditions for game
    """

    parser = argparse.ArgumentParser(description="The board game Pandemic made in Python.",
                                     epilog="""Made by unnamedplay-r, August 2017:\n
                                     github.com/unnamedplay-r""",
                                     prog='pandemic')
    parser.add_argument("players", help="the number of players",
                        type=int, choices=[2, 3, 4])
    parser.add_argument("difficulty",
                        help="""the difficulty of the game corresponding to the
                        number of epidemic cards in the player deck""",
                        type=int, choices=[4, 5, 6])
    parser.add_argument("--verbose", help="increase output verbosity", type=int, choices=[1, 2])
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = parser.parse_args()

    # check for optionals
    if args.verbose == 1:
        print("Verbose logging turned on.\n")
        logger.setLevel('INFO')
    elif args.verbose == 2:
        print("Verbose logging turned on.\n")
        logger.setLevel('DEBUG')

    # create clean board
    global gs
    gs = GameState()
    clear_screen()
    clean_setup(args.players, args.difficulty)

    # start the loop
    PandemicCmd().cmdloop()
    print('\nThanks for playing!')

if __name__ == '__main__':
    main()
