import xlsxwriter
import random
import sys
import math
from time import time
from enum import Enum
WIFI_STRENGTH = 6 #each position == 5 ft, each WIFI_STRENGTH == 5ft

def main():
    #argv[1] 0 < Character Count > 12
    #argv[2] 0 < Map Size < 16
    #argv[3] Step Count
    #argv[4] Skip -- use to skip printing in workbook, so 1 prints all, 2 prints every other, so on
    #Asserts
    try:
        character_count = int(sys.argv[1]);
    except IndexError:
        character_count = random.randrange(1,12);
    try:
        map_size = int(sys.argv[2]);
    except IndexError:
        map_size = random.randrange(1,16);
    try:
        step_count = int(sys.argv[3]);
    except IndexError:
        step_count = random.randrange(1,1000);
    try:
        skip = int(sys.argv[4]);
    except IndexError:
        skip = random.randrange(1,100,10);
        if (skip > step_count):
            skip = step_count;

    print("Character Count: " + str(character_count) + " Map Size: " + str(map_size) + " Map Steps: " + str(step_count) + " Skip: " + str(skip));

    if (character_count > 12 or character_count < 1):
        raise ValueError("Bad Arg 1, character range should be between 1 and 12 inclusive given: " + character_count);
    elif (map_size > 16 or character_count < 1):
        raise ValueError("Bad Arg 2, map size range should be between 1 and 16 inclusive given: " + map_size);
    elif (step_count < 1):
        raise ValueError("Bad Arg 3, steps to do should be over 0, given: " + step_count);
    elif (skip < 1):
        raise ValueError("Bad Arg 4, skip to do should be over 0, given: " + skip);
    else:
        _workbook = xlsxwriter.Workbook('xlsx_SSC_Simulation.xlsx') #instantiate xlsx workbook
        #Size, CharacterCount
        _map = Map(_workbook,character_count,map_size,skip) #instantiate a map to simulate xlsx
        for i in range(step_count):
            _map.step(); #step through the simulation
        _workbook.close();

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

        def push_connection_vector(self,vector):
            self.connection_vector += vector;

        def clear(self):
            self.character_list = []
            self.connection_vector = ""

        def write_characters(self):
            if (len(self.character_list) <= 0):
                if (self.connection_vector == ""):
                    return "x"
                else:
                    return self.connection_vector;

            string = ""
            for character in self.character_list:
                string += character.get_name()
                if (character.get_state() == Map.Character.State.client):
                    string += ":c "
                elif (character.get_state() == Map.Character.State.host):
                    string += ":h "
                elif (character.get_state() == Map.Character.State.p_host):
                    string += ":ph "
                elif (character.get_state() == Map.Character.State.p_client):
                    string += ":pc "
                elif (character.get_state() == Map.Character.State.resting):
                    string += ":r "
                string += ","
            string = string.strip(",")
            return string

        def __init__(self):
            self.carrier_to_signal = Map.Position.build_carrier_list()
            self.character_list = []
            self.connection_vector = "x"

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
            resting = 0;
            p_client = 1;
            client = 2;
            p_host = 3;
            host = 4;

        name_pool = ["Joe","Jim","Tomas","Sally","Diane","Ian","Will","Lillian","Scott","Lynn","Bernice","Donnie"];
        name_index = 0;

        @staticmethod
        def new_name():
            #Get a name from the pool of names and up the index so that a name won't be chosen twice
            if (Map.Character.name_index >= len(Map.Character.name_pool)): #Assert index has not grown passed name pool size
                raise ValueError("Map.Character.name_index >= the Map.character.name_pool length, no name left to choose");
            else:
                name = Map.Character.name_pool[Map.Character.name_index];
                Map.Character.name_index += 1;
                return name;

        def __init__(self,size):
            #A character maintains the properties; name : string, state : string, carrier, signal strength,
            #potential connections, a
            self.name = Map.Character.new_name();
            self.state = Map.Character.State(0); #assign character state default to resting, figure during step
            self.carrier = Map.Carrier(random.randrange(1,len(Map.Carrier))); #choose a random carrier from enum Carrier
            self.signal_strength = 0; #Default signal_strength, figured in map step
            self.potential_connections = []; #Maintain a list of near enough characters to connect
            self.bandwidth_limit = random.randrange(5); #Choose a personal bandwidth limit
            self.position = random.randrange(size), random.randrange(size); #Hold tuple of local position on map
            self.client_connection = None; #Hold a reference to a character which may be connected to
            self.host_connections = [];

        def get_x(self):
            return self.position[0];

        def get_y(self):
            return self.position[1];

        def get_name(self):
            return self.name;

        def get_state(self):
            return self.state;

        def set_state(self, state):
            self.state = state;

        def get_carrier(self):
            return self.carrier.name;

        def get_signal_strength(self):
            return self.signal_strength;

        def set_signal_strength(self, signal_strength):
            self.signal_strength = signal_strength;

        def get_potential_connections(self):
            return self.potential_connections;

        def add_potential_connection(self, connection):
            self.potential_connections.append(connection);

        def get_bandwidth_limit(self):
            return self.bandwidth_limit;

        def set_client_connection(self, connection):
            self.client_connection = connection;

        def get_client_connection(self):
            return self.client_connection;

        def push_host_connection(self, connection):
            self.host_connections.append(connection);

        def get_host_connections(self):
            return self.host_connections;

        def rem_host_connection(self,connection):
            self.host_connections.remove(connection);

        def clear_host_connections(self):
            self.host_connections = [];

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

    def __init__(self,workbook,character_count,size,skip):
        #instantiate properties; worksheet : xlsxwriter.Worksheet, size : int, map : [char][char], character_count : int, characters : [Characters]
        self.workbook = workbook;
        self.size = size;
        self.map = Map.build_map(self.size); #Build the map
        self.character_count = character_count;
        self.skip = skip;
        self.characters = self.build_character_list(self.character_count,self.size); #maintain a list of characters of count 2 to 12
        self.time_total = 0;
        self.time_diff = 0;
        self.time_sim = 0;
        self.step_count = 0;
        self.time_average_dif = 0;


    def clear_map(self):
        for row in self.map:
            for pos in row:
                pos.clear();

    def write_map(self):
        form = self.workbook.add_format();
        form.set_align("center");
        form.set_align("vcenter");
        form.set_font_size(14);
        form.set_shrink();
        for i in range(self.size):
            for j in range(self.size):
                self.worksheet.write(i,j,self.map[j][i].write_characters(),form)

    def write_character_list(self):
        form = self.workbook.add_format();
        form.set_shrink()
        self.worksheet.write(self.size,0,"Name: ",form)
        self.worksheet.write(self.size+1,0,"Connect: ",form)
        self.worksheet.write(self.size+2,0,"Position: ",form)
        self.worksheet.write(self.size+3,0,"State: ",form)
        self.worksheet.write(self.size+4,0,"Carrier: ",form)
        self.worksheet.write(self.size+5,0,"Signal Str: ",form)
        self.worksheet.write(self.size+6,0,"Bandwidth: ",form)
        self.worksheet.write(self.size+7,0,"Potential Con: ",form)
        for i in range(len(self.characters)):
            form.set_align("center");
            self.worksheet.write(self.size,i+1,self.characters[i].get_name(),form)
            if (self.characters[i].get_state() == Map.Character.State.client):
                self.worksheet.write(self.size+1,i+1,self.characters[i].get_client_connection().get_name(),form)
            elif (self.characters[i].get_state() == Map.Character.State.host):
                client_list = ""
                for client in self.characters[i].get_host_connections():
                    client_list += client.get_name() + " ,"
                client_list = client_list.strip(" ")
                client_list = client_list.strip(",")
                self.worksheet.write(self.size+1,i+1,client_list,form)

            self.worksheet.write(self.size+2,i+1,str(self.characters[i].get_x()) + "," + str(self.characters[i].get_y()),form)
            self.worksheet.write(self.size+3,i+1,self.characters[i].get_state().name,form)
            self.worksheet.write(self.size+4,i+1,self.characters[i].get_carrier(),form)
            self.worksheet.write(self.size+5,i+1,self.characters[i].get_signal_strength(),form)
            self.worksheet.write(self.size+6,i+1,self.characters[i].get_bandwidth_limit(),form)
            conn = self.characters[i].get_potential_connections()
            for j in range(len(conn)):
                self.worksheet.write(self.size+7+j,i+1,conn[j].get_name(),form)

    def write_meta_data(self):
        form = self.workbook.add_format();
        form.set_shrink();
        form.set_align("center");
        #write current step
        self.worksheet.write(0,self.size,"Step:",form)
        self.worksheet.write(0,self.size+1,self.step_count,form)
        #write total time
        self.worksheet.write(1,self.size,"Total Time:",form)
        self.worksheet.write(1,self.size+1,str(round(self.time_total*1000000,1)) + "ms",form)
        self.worksheet.write(1,self.size+2,str(round(self.time_total,1)) + "s",form)
        #write time difference between steps
        self.worksheet.write(2,self.size,"Diff Time:",form)
        self.worksheet.write(2,self.size+1,str(round(self.time_diff*1000000,1)) + "ms",form)
        #write time difference between steps
        self.worksheet.write(3,self.size,"Aver Diff:",form)
        self.worksheet.write(3,self.size+1,str(round(self.time_average_dif*1000000,1)) + "ms",form)
        #write simulation time
        self.worksheet.write(4,self.size,"Sim Time:",form)
        self.worksheet.write(4,self.size+1,str(round(self.time_sim,1)) + "s",form)
        self.worksheet.write(4,self.size+2,str(round(self.time_sim/60,1)) + "m",form)
        self.worksheet.write(4,self.size+3,str(round(self.time_sim/60/60,1)) + "h",form)

    def write(self):
        self.worksheet = self.workbook.add_worksheet(); #The data will be displayed through xlsx
        for i in range(0,self.size):
            self.worksheet.set_row(i,18)
        self.write_map()
        self.write_character_list()
        self.write_meta_data()

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

    @staticmethod
    def figure_potential_connection(character,other_character):
        x = character.get_x()
        y = character.get_y()
        cx = other_character.get_x()
        cy = other_character.get_y()
        if (math.fabs(x-cx) <= WIFI_STRENGTH and math.fabs(y-cy) <= WIFI_STRENGTH):
            return True;

    def figure_potential_connections(self):
        for character in self.characters:
            character.potential_connections = []
            for other_character in self.characters:
                if (Map.figure_potential_connection(character,other_character)):
                    character.potential_connections.append(other_character);

    def figure_signal_strength(self):
        for character in self.characters:
            carrier_to_signal = self.map[character.position[0]][character.position[1]].get_carrier_to_signal()
            for carrier, strength in carrier_to_signal:
                if (character.carrier == carrier):
                    character.set_signal_strength(strength)

    def figure_connection_vectors(self):
        for character in self.characters:
            if (character.get_state() == Map.Character.State.client):
                x = character.get_x();
                y = character.get_y();
                cx = character.get_client_connection().get_x();
                cy = character.get_client_connection().get_y();
                dx = abs(cx - x);
                dy = abs(cy - y);
                x_sign = 1;
                y_sign = 1;
                if (cx - x < 0):
                    x_sign = -1;
                if (cy - y < 0):
                    y_sign = -1;

                for i in range(dx):
                    self.map[character.get_x()+(i*x_sign)][character.get_y()].push_connection_vector("-");
                for i in range(dy):
                    self.map[character.get_x()+(dx)*x_sign][character.get_y()+(i*y_sign)].push_connection_vector("|");


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
        self.figure_potential_connections();
        #If a change is made to any characters state, all other characters will be reevaluated
        dirty_flag = True;
        while (dirty_flag):
            dirty_flag = False;
            for character in self.characters:
                state = character.get_state();
                connections = character.get_potential_connections();
                #Resting
                if (state == Map.Character.State.resting):
                    #To p_host
                    if (character.get_signal_strength() > 0 and character.get_bandwidth_limit() > 0):
                        character.set_state(Map.Character.State.p_host)
                        dirty_flag = True
                    #To p_client
                    elif (random.randrange(100) == 0): #Every 5 minutes a shift to client will occur on average
                        character.set_state(Map.Character.State.p_client)
                        dirty_flag = True
                #Potential Client
                elif (state == Map.Character.State.p_client):
                    #To p_host, Check for p_host to connect to
                    for connection in connections:
                        if (connection.get_state() == Map.Character.State.p_host):
                            character.set_client_connection(connection)
                            connection.push_host_connection(character)
                            character.set_state(Map.Character.State.client)
                            dirty_flag = True
                            break
                        #To resting state
                        elif (random.randrange(100) == 0): #Every 5 minutes a shift to client will occur on average
                            character.set_state(Map.Character.State.resting)
                            dirty_flag = True
                #Client
                elif (state == Map.Character.State.client):
                    #determine if connection was lost
                    still_connected = False
                    for connection in connections:
                        if (connection == character.get_client_connection() and connection.get_state() == Map.Character.State.host):
                            still_connected = True;
                            break;
                    #To p_client, check if connection was lost
                    if (character.get_client_connection() == None):
                        character.set_state(Map.Character.State.p_client);
                        dirty_flag = True;
                    elif (not still_connected):
                        character.set_state(Map.Character.State.p_client);
                        character.get_client_connection().rem_host_connection(character);
                        dirty_flag = True;
                    #To resting state
                    elif (random.randrange(100) == 0): #Every 5 minutes a shift to client will occur on average
                        character.set_state(Map.Character.State.resting)
                        character.get_client_connection().rem_host_connection(character);
                        character.set_client_connection(None);
                        dirty_flag = True

                #Potential Host
                elif (state == Map.Character.State.p_host):
                    #To host, Check if connection is filled
                    if (character.get_host_connections() != []):
                        character.set_state(Map.Character.State.host);
                        dirty_flag = True;
                    #To resting, check if signal strength was lost
                    elif (character.get_signal_strength() == 0):
                        character.set_state(Map.Character.State.resting);
                        dirty_flag = True;
                #Host
                elif (state == Map.Character.State.host):
                    #To potential host. if all client is lost
                    if (character.get_host_connections == []):
                        character.set_state(Map.Character.State.p_host)
                        dirty_flag = True;
                    #To resting, if signal strength is lost
                    elif (character.get_signal_strength() == 0):
                        for client in character.get_host_connections():
                            client.set_client_connection(None);
                        character.clear_host_connections();
                        character.set_state(Map.Character.State.resting);
                        dirty_flag = True;



    def populate_map(self):
        #Fill Map
        self.clear_map()
        self.figure_connection_vectors();
        for character in self.characters:
            self.map[character.get_x()][character.get_y()].push(character);

    def step(self):
        #Each step() is a call to move the dynamics of the simulation once, this includes characters walking,
        #gaining and losing signal strength, characters changing their states, new connections being formed
        #Move and place characters
        self.step_characters();
        #Start tracking time between network steps
        self.step_count += 1;
        self.time_diff = 0;
        self.time_sim = self.step_count * 3.24; #A char can walk 5 feet, 5 feet takes 3.24 seconds to walk average.
        time_init = time();
        #Figure character potential connections
        self.step_network();
        #Figure time between algorithms
        self.time_diff = time() - time_init;
        self.time_total += self.time_diff;
        if (self.step_count == 1):
            self.time_average_dif = self.time_diff;
        else:
            self.time_average_dif = (self.time_average_dif + self.time_diff)/2;
        #Populate Map With New Positions
        self.populate_map();
        #write map and character information
        if (self.step_count % self.skip == 0 or self.step_count == 1):
            self.write();


main()
