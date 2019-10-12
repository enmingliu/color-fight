from colorfight import Colorfight
import time
import random
import math
from colorfight.constants import BLD_GOLD_MINE, BLD_ENERGY_WELL, BLD_FORTRESS, BUILDING_COST

energy_weight = 1
dist_weight = 20
attack_weight = 1
expand_dist_weight = 20
nat_energy_weight = 0.1
user_homes = {}
my_uid = 0
energy_well_cnt = 0
convert_ratio = 1/2
threshold = 150
building_threshold = 100
cur_game = None

def get_homes():
    global user_homes
    for i in range(cur_game.width):
        for j in range(cur_game.height):
            cell = cur_game.game_map[(i, j)]
            if cell.is_home:
                user_homes[cell.owner] = cell

def get_my_cells(cells_dict):
    my_cells = []
    for cell in cells_dict:
        if cell.owner == my_uid:
            my_cells.append(cell)
    return my_cells

def get_my_adj_cells(cells_dict):
    my_adj_cells = []
    for cell in cells_dict:
        for adj_pos in cell.position.get_surrounding_cardinals():
            c = cur_game.game_map[adj_pos]
            if c.owner != my_uid and c not in my_adj_cells:
                my_adj_cells.append(c)
    return my_adj_cells
    
def get_upgrade_value(cell):
    if cell.position.x == user_homes[my_uid].position.x and cell.position.y == user_homes[my_uid].position.y:
        return 0
    energy_val = cell.energy * energy_weight
    dist_val = 1/(math.sqrt((cell.position.x - user_homes[my_uid].position.x)**2 + (cell.position.y - user_homes[my_uid].position.y)**2)) * dist_weight
    return energy_val + dist_val

def get_expansion_value(cell):
    attack_val = 1/cell.attack_cost * attack_weight
    dist_val = 1/(math.sqrt((cell.position.x - user_homes[my_uid].position.x)**2 + (cell.position.y - user_homes[my_uid].position.y)**2)) * expand_dist_weight
    natural_energy_val = cell.natural_energy * nat_energy_weight
    return attack_val + dist_val + natural_energy_val

def check_building_threshold(cells_dict):
    upgraded_cnt = 0
    for cell in cells_dict:
        if cell.building.level == 3:
            upgraded_cnt += 1
            if upgraded_cnt >= building_threshold:
                return True
    return False;            

def play_game(
        game, \
        room     = 'public', \
        username = 'ExampleAI', \
        password = str(int(time.time()))):
    # Connect to the server. This will connect to the public room. If you want to
    # join other rooms, you need to change the argument
    game.connect(room = room)
    
    # game.register should return True if succeed.
    # As no duplicate usernames are allowed, a random integer string is appended
    # to the example username. You don't need to do this, change the username
    # to your ID.
    # You need to set a password. For the example AI, the current time is used
    # as the password. You should change it to something that will not change 
    # between runs so you can continue the game if disconnected.
    if game.register(username = username, \
            password = password):
        # This is the game loop
        while True:
            # The command list we will send to the server
            cmd_list = []
            # The list of cells that we want to attack
            my_attack_list = []
            # update_turn() is required to get the latest information from the
            # server. This will halt the program until it receives the updated
            # information. 
            # After update_turn(), game object will be updated.   
            # update_turn() returns a Boolean value indicating if it's still 
            # the same game. If it's not, break out
            if not game.update_turn():
                break

            # if we reach certain threashold for number of cells owned, keep a mines ratio
    
            # Check if you exist in the game. If not, wait for the next round.
            # You may not appear immediately after you join. But you should be 
            # in the game after one round.
            if game.me == None:
                continue
    
            global cur_game
            cur_game = game
            me = game.me
            global my_uid
            my_uid = me.uid

            if not user_homes:
                get_homes()

            adj_cells = get_my_adj_cells(me.cells.values())
            adj_cells.sort(key=get_expansion_value, reverse=True)

            if not (len(me.cells) > threshold and not check_building_threshold(me.cells.values())):
                for cell in adj_cells:
                    if cell.attack_cost < me.energy and cell.position not in my_attack_list:
                        cmd_list.append(game.attack(cell.position, cell.attack_cost))
                        print("We are attacking ({}, {}) with {} energy".format(cell.position.x, cell.position.y, cell.attack_cost))
                        me.energy -= cell.attack_cost
                        my_attack_list.append(cell.position)

            if me.tech_level == 1 and me.gold > 1000 and me.energy > 1000:
                cmd_list.append(game.upgrade(user_homes[my_uid].position))
                print("We upgraded home at ({}, {})".format(user_homes[my_uid].position.x, user_homes[my_uid].position.y))
                me.gold -= 1000
                me.energy -= 1000
            elif me.tech_level == 2 and me.gold > 2000 and me.energy > 2000:
                cmd_list.append(game.upgrade(user_homes[my_uid].position))
                print("We upgraded home at ({}, {})".format(user_homes[my_uid].position.x, user_homes[my_uid].position.y))
                me.gold -= 2000
                me.energy -= 2000

            # game.me.cells is a dict, where the keys are Position and the values
            # are MapCell. Get all my cells.
            my_cells = get_my_cells(me.cells.values())
            my_cells.sort(key=get_upgrade_value, reverse=True)

            global energy_well_cnt
            for cell in my_cells:
                if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]:
                    building = BLD_ENERGY_WELL
                    if(len(me.cells) / (game.width * game.height) > convert_ratio):
                        building = BLD_GOLD_MINE
                    if not (energy_well_cnt % 4) and energy_well_cnt != 0:
                        building = BLD_GOLD_MINE

                    cmd_list.append(game.build(cell.position, building))
                    print("We build {} on ({}, {})".format(building, cell.position.x, cell.position.y))
                    me.gold -= 200
                    energy_well_cnt += 1
                elif cell.owner == me.uid and cell.building.can_upgrade and me.gold >= cell.building.upgrade_gold and cell.building.level < me.tech_level:
                    cmd_list.append(game.upgrade(cell.position))
                    print("We upgraded ({}, {})".format(cell.position.x, cell.position.y))
                    me.gold   -= cell.building.upgrade_gold
                    me.energy -= cell.building.upgrade_energy
            # close to threshold, home.level == 3, 
            # for cell in me.cells.values():
                # Check the surrounding position
                '''for pos in cell.position.get_surrounding_cardinals():
                    # Get the MapCell object of that position
                    c = game.game_map[pos]
                    # Attack if the cost is less than what I have, and the owner
                    # is not mine, and I have not attacked it in this round already
                    # We also try to keep our cell number under 100 to avoid tax
                    if c.attack_cost < me.energy and c.owner != game.uid \
                            and c.position not in my_attack_list \
                            and len(me.cells) < 95:
                        # Add the attack command in the command list
                        # Subtract the attack cost manually so I can keep track
                        # of the energy I have.
                        # Add the position to the attack list so I won't attack
                        # the same cell
                        cmd_list.append(game.attack(pos, c.attack_cost))
                        print("We are attacking ({}, {}) with {} energy".format(pos.x, pos.y, c.attack_cost))
                        me.energy -= c.attack_cost
                        my_attack_list.append(c.position)'''

                # If we can upgrade the building, upgrade it.
                # Notice can_update only checks for upper bound. You need to check
                # tech_level by yourself. 
                '''if cell.building.can_upgrade and \
                        (cell.building.is_home or cell.building.level < me.tech_level) and \
                        cell.building.upgrade_gold < me.gold and \
                        cell.building.upgrade_energy < me.energy:
                    cmd_list.append(game.upgrade(cell.position))
                    print("We upgraded ({}, {})".format(cell.position.x, cell.position.y))
                    me.gold   -= cell.building.upgrade_gold
                    me.energy -= cell.building.upgrade_energy'''
                    
                # Build a random building if we have enough gold
                '''if cell.owner == me.uid and cell.building.is_empty and me.gold >= BUILDING_COST[0]:
                    building = random.choice([BLD_FORTRESS, BLD_GOLD_MINE, BLD_ENERGY_WELL])
                    cmd_list.append(game.build(cell.position, building))
                    print("We build {} on ({}, {})".format(building, cell.position.x, cell.position.y))
                    me.gold -= 100'''
    
            # Send the command list to the server
            result = game.send_cmd(cmd_list)
            print(result)

    # Do this to release all the allocated resources. 
    game.disconnect()

if __name__ == '__main__':
    # Create a Colorfight Instance. This will be the object that you interact
    # with.
    game = Colorfight()

    # ================== Find a random non-full rank room ==================
    #room_list = game.get_gameroom_list()
    #rank_room = [room for room in room_list if room["rank"] and room["player_number"] < room["max_player"]]
    #room = random.choice(rank_room)["name"]
    # ======================================================================
    room = 'public' # Delete this line if you have a room from above

    # ==========================  Play game once ===========================
    #play_game(
    #    game     = game, \
    #    room     = room, \
    #    username = 'nani ' + str(random.randint(1, 100)), \
    #    password = str(int(time.time()))
    #)
    # ======================================================================

    # ========================= Run my bot forever =========================
    while True:
        try:
            play_game(
                game     = game, \
                room     = room, \
                username = 'nani ' + str(random.randint(1, 100)), \
                password = str(int(time.time()))
            )
        except Exception as e:
            print(e)
            time.sleep(2)