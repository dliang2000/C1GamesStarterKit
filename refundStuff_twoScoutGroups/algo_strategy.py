import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips:

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical
  board states. Though, we recommended making a copy of the map to preserve
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.previous_enemy_health = 0
        self.offense_mode = False
        self.next_piece = SCOUT

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()

    def starter_strategy(self, game_state):
        piece = [SCOUT, DEMOLISHER]
        if game_state.turn_number < 3:
            self.build_defences(game_state)
        else:
            if self.attackMadeNoDifference(game_state):
                self.build_defensive_structure(game_state)
                self.attack(game_state, piece[1])
            elif game_state.enemy_health - self.previous_enemy_health <= 6:
                #self.next_piece = piece[0]
                self.build_defensive_structure(game_state)
                self.attack(game_state, piece[0])
            else:
                self.build_offensive_structure(game_state)
                self.attack_offensive(game_state, piece[0])

        self.previous_enemy_health = game_state.enemy_health

    def attackMadeNoDifference(self, game_state):
        return game_state.enemy_health - self.previous_enemy_health <= 3

    def build_defences(self, game_state, offense = False, remove = False):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place walls in front of turrets to soak up damage for them
        if offense:
            self.build_offensive_structure(game_state)
        else:
            self.build_defensive_structure(game_state, remove)
        self.build_reactive_defense(game_state)

    def build_offensive_structure(self, game_state):
        support_locations = [[12, 5], [13, 5], [15, 5], [16, 5], [12, 4], [13, 4], [15, 4], [16, 4], [12, 3], [13, 3], [15, 3], [16, 3], [12, 2], [13, 2], [15, 2], [16, 2], [12, 1], [13, 1], [15, 1], [13, 0]]
        game_state.attempt_spawn(SUPPORT, support_locations)
        game_state.attempt_remove(support_locations)
        game_state.attempt_upgrade(support_locations)
        wall_locations = [[12, 6], [13, 6], [15, 6], [16, 6], [11, 5], [17, 5]]
        game_state.attempt_spawn(WALL, wall_locations)
        game_state.attempt_remove(wall_locations)

    def build_defensive_structure(self, game_state, remove = False):
        shielded_wall_locations = [[0, 13], [1, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13], [22, 12], [20, 11], [22, 11], [19, 10]]
        game_state.attempt_spawn(WALL, shielded_wall_locations)
        if remove:
            game_state.attempt_remove(shielded_wall_locations)
        wall_locations = [[2, 13], [3, 13], [4, 13], [5, 12], [6, 11], [7, 10], [8, 9], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9]]
        game_state.attempt_spawn(WALL, wall_locations)
        if remove:
            game_state.attempt_remove(wall_locations)
        turret_locations = [[2, 12], [3, 12], [23, 12], [26, 12], [23, 11], [20, 10], [22, 10]]
        game_state.attempt_spawn(TURRET, turret_locations)
        game_state.attempt_upgrade(turret_locations)
        game_state.attempt_upgrade(shielded_wall_locations)
        if remove:
            game_state.attempt_remove(turret_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def attack(self, game_state, piece):
        turn = game_state.turn_number
        own_mp = game_state.get_resource(1)
        if turn > 3 and turn < 10 and own_mp >= 11:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.6))
            game_state.attempt_spawn(piece, [17, 3], game_state.number_affordable(piece))
        elif turn >= 10 and turn < 20 and own_mp >= 20:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.5))
            game_state.attempt_spawn(piece, [17, 3], game_state.number_affordable(piece))
        elif turn >= 20 and turn < 30 and own_mp >= 30:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.45))
            game_state.attempt_spawn(piece, [17, 3], game_state.number_affordable(piece))
        elif own_mp >= 40:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.4))
            game_state.attempt_spawn(piece, [17, 3], game_state.number_affordable(piece))

    def attack_offensive(self, game_state, piece):
        turn = game_state.turn_number
        own_mp = game_state.get_resource(1)
        if turn > 3 and turn < 10 and own_mp >= 11:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.6))
            game_state.attempt_spawn(piece, [18, 4], game_state.number_affordable(piece))
        elif turn >= 10 and turn < 20 and own_mp >= 20:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.5))
            game_state.attempt_spawn(piece, [18, 4], game_state.number_affordable(piece))
        elif turn >= 20 and turn < 30 and own_mp >= 30:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.45))
            game_state.attempt_spawn(piece, [18, 4], game_state.number_affordable(piece))
        elif own_mp >= 40:
            game_state.attempt_spawn(piece, [14, 0], int(game_state.number_affordable(piece) * 0.4))
            game_state.attempt_spawn(piece, [18, 4], game_state.number_affordable(piece))


    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
