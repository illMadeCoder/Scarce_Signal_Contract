import xlsxwriter
import random
import sys
import math
from enum import Enum
WIFI_STRENGTH = 6 #each position == 5 ft, each WIFI_STRENGTH == 5ft
'''
workbook = xlsxwriter.Workbook('Expenses01.xlsx')
worksheet = workbook.add_worksheet()

worksheet.write(0,0,0)
workbook.close()
'''
def main():
    _workbook = xlsxwriter.Workbook('xlsx_SSC_Simulation.xlsx') #instantiate xlsx workbook
    _worksheet = _workbook.add_worksheet() #setup a worksheet to display on
    _map = Map(_worksheet) #instantiate a map to simulate xlsx
    _map.step(); #step through the simulation

class Map:
    '''
    Map class maintains a matrix where each element contains a set of signals relative to each carrier
    Matrix size is defined as a multiple of 8x8 * a number between 2 and 16
    Map generates and maintains a list of all characters with a count of 2 to 12
    Map maintains a xlsx worksheet
    Void Function step where
     a step will move each character in a random direction and may change each state

    '''
    #A Carrier Enum for each carrier
    class Carrier(Enum):
        ATnT = 1
        Sprint = 2
        Verizon = 3
        TMobile = 4
    class Position:
        '''
        Position class acts as the elements of each map index.
        A position maintains a dynamic list to hold each Character in its same x and y coordinates
        a position also maintains a list of each carrier and their relative strength to inform a
        character as to their signal strength where a character's signal strength is determined by
        its relative carrier to the signal strength of its position.
        '''
        @staticmethod
        def build_carrier_list():
            #build list of tuples which associate each carrier with a signal strength
            carrier_list = []
            for carrier in list(Map.Carrier):
                #As a scarce situation, signal is more likely to be 0
                rnd = random.randrange(10)
                strength = 0
                if (rnd > 4):
                    strength = random.randrange(1,5)
                tup = (carrier, strength)
                carrier_list.append(tup)
            return carrier_list

        def push(self,character):
            self.character_list.append(character)

        def clear(self):
            self.character_list = []

        def write_characters(self):
            if (len(self.character_list) <= 0):
                return "x"
            string = ""
            for character in self.character_list:
                string += character.get_name() + ","
            string = string[0:len(string)-1]
            return string

        def __init__(self):
            self.carrier_to_signal = Map.Position.build_carrier_list()
            self.character_list = []

        def get_carrier_to_signal(self):
            return self.carrier_to_signal

    class Character:
        '''
        Character Class acts as the nodes in the network.
        Maintains
        Name - An identifier for the node.
        State - A state of the node
            non state - a node without a calculated state
            potential client - a node with a connection to a potential host
            client - a node that is utilizing a host for connection
            potential host - a node with a global connection with no use
            host - a node with a global connection being used by either a client or itself
            offline - a node with no path to a global connection
        Carrier - Each phone carrier may have a different connection depending on the node's position
        Signal Strength - Whether or not a client has a connection relative to their carrier and position
        Potential Connections - A list of nodes within range to connect to by either a client or host
        Bandwidth Limits - Nodes may limit their bandwidth upload over the network
        Position - a node's x and y position on the map
        '''
        #A State Enum for each character state
        class State(Enum):
            resting = 0
            potential_client = 1
            client = 2
            potential_host = 3
            host = 4

        name_pool = ["Joe","Jim","Tomas","Sally","Diane","Sally","Scott","Lillian","Scott","Lynn","Bernice","Donnie"]
        name_index = 0
        state_pool = ["non state", "p client", "client", "p host", "host", "offline"]

        @staticmethod
        def new_name():
            #Get a name from the pool of names and up the index so that a name won't be chosen twice
            if (Map.Character.name_index >= len(Map.Character.name_pool)): #Assert index has not grown passed name pool size
                raise ValueError("Map.Character.name_index >= the Map.character.name_pool length, no name left to choose")
            else:
                name = Map.Character.name_pool[Map.Character.name_index]
                Map.Character.name_index += 1
                return name

        def __init__(self,size):
            #A character maintains the properties; name : string, state : string, carrier, signal strength,
            #potential connections, a
            self.name = Map.Character.new_name()
            self.state = Map.Character.State(0) #assign character state default to resting, figure during step
            self.carrier = Map.Carrier(random.randrange(1,len(Map.Carrier))) #choose a random carrier from enum Carrier
            self.signal_strength = 0 #Default signal_strength, figured in map step
            self.potential_connections = [] #Maintain a list of near enough characters to connect
            self.bandwidth_limit = random.randrange(5) #Choose a personal bandwidth limit
            self.position = random.randrange(size), random.randrange(size) #Hold tuple of local position on map
            self.connection = None #Hold a reference to a character which may be connected to

        def get_x(self):
            return self.position[0]

        def get_y(self):
            return self.position[1]

        def get_name(self):
            return self.name

        def get_state(self):
            return self.state
        def set_state(self, state):
            self.state = state

        def get_carrier(self):
            return self.carrier.name

        def get_signal_strength(self):
            return self.signal_strength

        def set_signal_strength(self, signal_strength):
            self.signal_strength = signal_strength

        def get_potential_connections(self):
            return self.potential_connections

        def add_potential_connection(self, connection):
            self.potential_connections.append(connection)

        def get_bandwidth_limit(self):
            return self.bandwidth_limit

        def set_connection(self, connection):
            self.connection = connection

        def get_connection(self):
            return self.connection

    def build_character_list(self,character_count,size):
        characters = []
        for i in range(character_count): #create a new character for the character_count
            characters.append(Map.Character(size)) #create a new instance of character and give it a position in the map
        return characters;

    @staticmethod
    def build_map(size):
        new_map = []
        for i in range(size):
          row = []
          for j in range(size):
            row.append(Map.Position())
          new_map.append(row)
        return new_map

    def __init__(self,worksheet):
        #instantiate properties; worksheet : xlsxwriter.Worksheet, size : int, map : [char][char], character_count : int, characters : [Characters]
        self.worksheet = worksheet #The data will be displayed through xlsx
        self.size = 16 #The size determines the matrix length
        self.map = Map.build_map(self.size) #Build the map
        self.character_count = random.randrange(2,13) # 2 to 12 inclusive
        self.characters = self.build_character_list(self.character_count,self.size) #maintain a list of characters of count 2 to 12

    def clear_map(self):
        for row in self.map:
            for pos in row:
                pos.clear()

    def write_map(self):
        for i in range(self.size):
            for j in range(self.size):
                sys.stdout.write(self.map[j][i].write_characters())
                self.worksheet.write(i,j,self.map[j][i].write_characters())
            sys.stdout.write('\n')

    def write_character_list(self):
        self.worksheet.write(self.size,0,"Name: ")
        self.worksheet.write(self.size+1,0,"Connect: ")
        self.worksheet.write(self.size+2,0,"Position: ")
        self.worksheet.write(self.size+3,0,"State: ")
        self.worksheet.write(self.size+4,0,"Carrier: ")
        self.worksheet.write(self.size+5,0,"Signal Str: ")
        self.worksheet.write(self.size+6,0,"Bandwidth: ")
        self.worksheet.write(self.size+7,0,"Potential Con: ")
        for i in range(len(self.characters)):
            print self.characters[i].get_name()
            self.worksheet.write(self.size,i+1,self.characters[i].get_name())
            if (self.characters[i].get_connection() != None): self.worksheet.write(self.size+1,i+1,self.characters[i].get_connection().get_name())
            self.worksheet.write(self.size+2,i+1,str(self.characters[i].get_x()) + "," + str(self.characters[i].get_y()))
            self.worksheet.write(self.size+3,i+1,self.characters[i].get_state().name)
            self.worksheet.write(self.size+4,i+1,self.characters[i].get_carrier())
            self.worksheet.write(self.size+5,i+1,self.characters[i].get_signal_strength())
            self.worksheet.write(self.size+6,i+1,self.characters[i].get_bandwidth_limit())
            conn = self.characters[i].get_potential_connections()
            for j in range(len(conn)):
                self.worksheet.write(self.size+7+j,i+1,conn[j].get_name())

    def write(self):
        self.write_map()
        self.write_character_list()

    def step_characters(self):
        for character in self.characters:
            x_mod = random.randrange(-1,2)
            y_mod = random.randrange(-1,2)
            while (character.position[0] + x_mod >= self.size or character.position[0] + x_mod < 0):
                x_mod = random.randrange(-1,2)
            while (character.position[1] + y_mod >= self.size or character.position[1] + y_mod < 0):
                y_mod = random.randrange(-1,2)
            character.position = (character.position[0]+x_mod, character.position[1]+y_mod)
            self.figure_signal_strength()

    def figure_potential_connections(self):
        for character in self.characters:
            character.potential_connections = []
            x = character.get_x()
            y = character.get_y()
            for other_character in self.characters:
                cx = other_character.get_x()
                cy = other_character.get_y()
                if (math.fabs(x-cx) <= WIFI_STRENGTH and math.fabs(y-cy) <= WIFI_STRENGTH):
                    character.potential_connections.append(other_character)

    def figure_signal_strength(self):
        for character in self.characters:
            carrier_to_signal = self.map[character.position[0]][character.position[1]].get_carrier_to_signal()
            for carrier, strength in carrier_to_signal:
                if (character.carrier == carrier):
                    character.set_signal_strength(strength)

    def step_network(self):
        #If resting, may become potential client or potential host.
        #If signal strength > 10 and bandwidth limit > 0 and not potential client or client may become potential host.
        #If potential client with a signal strength > 0 become client of self.
        #If potential client without a signal strength of 0 determine if a connected to potential host then become their client
        #If host and signal strength became 0 after step, change to resting and change client to potential client
        #If host, may become client to self, if so let current client know its now a potential client
        #If host, client may leave range and so become potential host again.
        #If client, may gain signal strength and so current connected host should become potential host and self hosts self
        #If client, may lose host after step, then look for another potential host
        #If client, may stop using internet and begin resting again
        self.figure_potential_connections()
        #If a change is made to any characters state, all other characters will be reevaluated
        dirty_flag = True
        while (dirty_flag):
            dirty_flag = False
            for character in self.characters:
                state = character.get_state()
                connections = character.get_potential_connections()
                if (state == Map.Character.State.resting):
                    if (character.get_signal_strength() > 0 and character.get_bandwidth_limit() > 0):
                        character.set_state(Map.Character.State.potential_host)
                        dirty_flag = True
                    elif (random.randrange(3) == 2 and character.get_bandwidth_limit() > 0):
                        character.set_state(Map.Character.State.potential_client)
                        dirty_flag = True
                elif (state == Map.Character.State.potential_client):
                    for connection in connections:
                        if (connection.get_state() == Map.Character.State.potential_host):
                            character.set_connection(connection)
                            connection.set_connection(character)
                            character.set_state(Map.Character.State.client)
                            dirty_flag = True
                            break
                elif (state == Map.Character.State.client):
                    pass
                elif (state == Map.Character.State.potential_host):
                    if (character.get_connection() != None):
                        character.set_state(Map.Character.State.host)
                        dirty_flag = True

                elif (state == Map.Character.State.host):
                    pass


    def populate_map(self):
        #Fill Map
        self.clear_map()
        for character in self.characters:
            self.map[character.get_x()][character.get_y()].push(character)

    def step(self):
        #Each step() is a call to move the dynamics of the simulation once, this includes characters walking,
        #gaining and losing signal strength, characters changing their states, new connections being formed

        #Move and place characters
        self.step_characters()
        #Populate Map With New Positions
        self.populate_map()
        #Figure character potential connections
        self.step_network()
        #write map and character information
        self.write()

main()
