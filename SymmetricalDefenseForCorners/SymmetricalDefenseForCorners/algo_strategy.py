import gamelib
import random
import math
import numpy as np
import warnings
from sys import maxsize
import json
#import heapq

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
        global WALL, FACTORY, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        FACTORY = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.breached_last_round = 0
        self.scored_on_locations = []
        self.enemy_location_all_rounds =[]

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


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """
    def turn_one(self, game_state, turret_location_sections, factory_location_sections, wall_location_sections):

        game_state.attempt_spawn(FACTORY, factory_location_sections)
        game_state.attempt_upgrade(factory_location_sections)
        # if game_state.turn_number == 1:
        #     game_state.attempt_upgrade([14, 0])
        # else:
        #     game_state.attempt_upgrade(factory_location_sections)
        game_state.attempt_spawn(TURRET, turret_location_sections)
        game_state.attempt_spawn(WALL, wall_location_sections)

    def starter_strategy(self, game_state: gamelib.game_state.GameState):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        factory_location_sections = [[[13, 0], [14, 0]],  # Bottom two factorys
                                     [[13, 2], [14, 2], [12, 3], [15, 3], [11, 4], [16, 4], [10, 5], [17, 5], [9, 6],
                                      [18, 6]],  # V
                                     [[12, 4], [13, 4], [14, 4], [15, 4], [13, 3], [14, 3]],
                                     # Fill bottom layer inside V
                                     [[11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5]]]  # Fill top layer inside V
        turret_location_sections = [[[24, 12], [3, 12]],  # Corner starting turrets
                                    [[7, 9], [20, 9]],  # Middle starting turrets
                                    [[6, 12], [9, 12], [18, 12], [21, 12], [10, 11], [17, 11], [11, 10], [16, 10]],
                                    # Second layer of turrets
                                    [[7, 12], [8, 12], [19, 12], [20, 12]]  # Third layer of turrets
                                    ]
        wall_location_sections = [
            [[24, 13], [3, 13]],  # Corner Turret defense
            [[9, 8], [18, 8]],  # Middle Turret defense
            [[2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [19, 13], [20, 13], [21, 13], [22, 13],
             [23, 13], [24, 13], [25, 13]],  # Rest of the walls at the front
            [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13]],  # Three walls on each edge at the front
            [[9, 12], [18, 12], [10, 12], [12, 10], [17, 12], [11, 11], [15, 10], [12, 9], [15, 9], [12, 8], [15, 8]],
            # Front wall diagonals
            [[7, 10], [20, 10], [8, 9], [19, 9], [9, 8], [18, 8], [10, 7], [17, 7], [11, 6], [12, 6], [13, 6], [14, 6],
             [15, 6], [16, 6]]  # Second layer walls
        ]

        # Check the opponent structures along two corners (setup to prevent for corner attack)
        if game_state.turn_number >= 1:
            r_check, r_enemy_corner_locations, r_counter = self.right_corner_attack_flag(game_state)
            l_check, l_enemy_corner_locations, l_counter = self.left_corner_attack_flag(game_state)

            if r_check:
                self.build_defenses_right_corner(game_state)
            if l_check:
                self.build_defenses_left_corner(game_state)
            
            symmetrical_turret_locations = []
            if r_counter >= l_counter and r_counter >= 3:
                gamelib.debug_write("Enemy's corner location: {}".format(r_enemy_corner_locations))
                #enemy_locations_flat_list = [item for sublist in r_enemy_corner_locations for item in sublist]
                for idx in range(len(r_enemy_corner_locations)):
                    turr_x, turr_y = r_enemy_corner_locations[idx]
                    symmetrical_turret_locations.append([turr_x, 27-turr_y])
                for idx in range(2):
                    turr_x, turr_y = symmetrical_turret_locations[idx]
                    game_state.attempt_spawn(TURRET, [turr_x, turr_y])
                    game_state.attempt_upgrade([turr_x, turr_y])
                    game_state.attempt_spawn(WALL, [turr_x, turr_y + 1])
                    game_state.attempt_upgrade([turr_x, turr_y + 1])
            
            symmetrical_turret_locations = []
            if l_counter >= 3:
                gamelib.debug_write("Enemy's corner location: {}".format(l_enemy_corner_locations))
                #enemy_locations_flat_list = [item for sublist in l_enemy_corner_locations for item in sublist]
                for idx in range(len(l_enemy_corner_locations)):
                    turr_x, turr_y = l_enemy_corner_locations[idx]
                    symmetrical_turret_locations.append([turr_x, 27-turr_y])
                for idx in range(2):
                    turr_x, turr_y = symmetrical_turret_locations[idx]
                    game_state.attempt_spawn(TURRET, [turr_x, turr_y])
                    game_state.attempt_upgrade([turr_x, turr_y])
                    game_state.attempt_spawn(WALL, [turr_x, turr_y + 1])
                    game_state.attempt_upgrade([turr_x, turr_y + 1])
            
            # Now build reactive defenses based on where the enemy scored
            if game_state.turn_number > 1 and game_state.get_resource(1, player_index=1) > int(game_state.my_health * 0.8):
                self.build_reactive_defense(game_state, turret_location_sections, wall_location_sections, min_turrets=4,
                                        min_walls=15)

            if game_state.turn_number < 4:
                spawned_factories = self.build_resources(game_state, factory_location_sections, max_factories=3)
            else:
                spawned_factories = self.build_resources(game_state, factory_location_sections, max_factories=2)
            
            if game_state.turn_number < 3:
                # First, place basic defenses
                self.build_defences(game_state, turret_location_sections, wall_location_sections, max_walls=1,
                                max_turrets=1)
            elif game_state.SP > 10:
                # First, place basic defenses
                self.build_defences(game_state, turret_location_sections, wall_location_sections, max_walls=100,
                                max_turrets=100)
            else:
                # First, place basic defenses
                self.build_defences(game_state, turret_location_sections, wall_location_sections, max_walls=8,
                                max_turrets=3)
            # If the turn is less than 5, stall with interceptors and wait to see enemy's base
            if game_state.turn_number < 9:
                self.attack_with_interceptors_or_scouts(game_state)
            else:
                # Now let's analyze the enemy base to see where their defenses are concentrated.
                # If they have many units in the front we can build a line for our demolishers to attack them at long range.
                if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                    self.demolisher_line_strategy(game_state)
                else:
                    self.attack_with_interceptors_or_scouts(game_state)

        if game_state.turn_number == 0 or game_state.turn_number > 3:
            self.turn_one(game_state, turret_location_sections[0], factory_location_sections[0], wall_location_sections[0])
            if game_state.turn_number == 0:
                game_state.attempt_spawn(INTERCEPTOR, [18, 4], 5)
                #game_state.attempt_spawn(INTERCEPTOR, [24, 10], 2)


        # if game_state.turn_number < 4:
        #     spawned_factories = self.build_resources(game_state, factory_location_sections, max_factories=10)
        # else:
        #     spawned_factories = self.build_resources(game_state, factory_location_sections, max_factories=2)

        # if game_state.turn_number < 3:
        #     # First, place basic defenses
        #     self.build_defences(game_state, turret_location_sections, wall_location_sections, max_walls=1,
        #                         max_turrets=1)
        # elif game_state.SP > 10:
        #     # First, place basic defenses
        #     self.build_defences(game_state, turret_location_sections, wall_location_sections, max_walls=100,
        #                         max_turrets=100)
        # else:
        #     # First, place basic defenses
        #     self.build_defences(game_state, turret_location_sections, wall_location_sections, max_walls=8,
        #                         max_turrets=3)


    def build_defenses_right_corner(self, game_state):
        wall_right_corner_locations = [[27, 13], [26, 13], [25, 13], [24, 13]]
        turret_right_corner_locations = [[25, 12], [26, 12], [24, 12]]

        for idx in range(len(wall_right_corner_locations)):
            turr_x, turr_y = wall_right_corner_locations[idx]
            game_state.attempt_spawn(WALL, [turr_x, turr_y])
            game_state.attempt_upgrade([turr_x, turr_y])
        
        for idx in range(len(turret_right_corner_locations)):
            turr_x, turr_y = turret_right_corner_locations[idx]
            game_state.attempt_spawn(TURRET, [turr_x, turr_y])
            game_state.attempt_upgrade([turr_x, turr_y])
    
    
    def build_defenses_left_corner(self, game_state):
        wall_left_corner_locations = [[0, 13], [1, 13], [2, 13], [3, 13]]
        turret_left_corner_locations = [[2, 12], [1, 12], [3, 12]]

        for idx in range(len(wall_left_corner_locations)):
            turr_x, turr_y = wall_left_corner_locations[idx]
            game_state.attempt_spawn(WALL, [turr_x, turr_y])
            game_state.attempt_upgrade([turr_x, turr_y])
        
        for idx in range(len(turret_left_corner_locations)):
            turr_x, turr_y = turret_left_corner_locations[idx]
            game_state.attempt_spawn(TURRET, [turr_x, turr_y])
            game_state.attempt_upgrade([turr_x, turr_y])


    def build_resources(self, game_state, factory_location_sections, max_factories=3):
        """
        Build resource factories whenever possible
        """
        SP = game_state.get_resource(0)
        total_spawned = 0
        # Spawn/upgrade as many as we can
        number_to_spawn = min(SP // 6, max_factories)
        for factory_location_section in factory_location_sections:
            # Attempt upgrade first
            for factory_location in factory_location_section:
                total_spawned += game_state.attempt_upgrade(factory_location)
                if total_spawned >= number_to_spawn: break
            # If nothing is upgraded attempt spawn one
            if total_spawned < number_to_spawn:
                for factory_location in factory_location_section:
                    total_spawned += game_state.attempt_spawn(FACTORY, factory_location)
                    if total_spawned >= number_to_spawn: break
        return total_spawned

    def build_defences(self, game_state, turret_location_sections, wall_location_sections, max_walls=2, max_turrets=2):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        turret_locations_flat_list = [item for sublist in turret_location_sections for item in sublist]
        wall_locations_flat_list = [item for sublist in wall_location_sections for item in sublist]
        max_elements = max(len(turret_locations_flat_list), len(wall_locations_flat_list))

        spawned_turrets = 0
        spawned_walls = 0
        range(max_elements)
        for idx in range(max_elements):
            if idx < len(turret_locations_flat_list) and spawned_turrets < max_turrets:
                turr_x, turr_y = turret_locations_flat_list[idx]
                spawned_turrets += game_state.attempt_spawn(TURRET, [turr_x, turr_y])
                spawned_turrets += game_state.attempt_upgrade([turr_x, turr_y])
                spawned_walls += game_state.attempt_spawn(WALL, [turr_x, turr_y + 1])
            if idx < len(wall_locations_flat_list) and spawned_walls < max_walls:
                spawned_walls += game_state.attempt_spawn(WALL, wall_locations_flat_list[idx])
                spawned_walls += game_state.attempt_upgrade(wall_locations_flat_list[idx])

    def build_reactive_defense(self, game_state, turret_location_sections, wall_location_sections, min_turrets=2,
                               min_walls=4):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        gamelib.debug_write("Reactive defense Breached?", self.breached_last_round)
        gamelib.debug_write("Reactive defense Turn number?", game_state.turn_number)
        gamelib.debug_write("Was reactive defenses set up?",
                            len(self.scored_on_locations) > 0 and self.breached_last_round)
        gamelib.debug_write("Scored on locations: ", self.scored_on_locations)
        count_of_enemy_unit_locations_our_side = {}
        if len(self.scored_on_locations) > 0 and self.breached_last_round:
            for coor, unit_type, unit_ID in self.scored_on_locations[-1]:
                # Find the closest turret for our configuration and priority build it
                # First layer gets priority
                for round in self.enemy_location_all_rounds:
                    for enemies_for_type in round:
                        for enemy in enemies_for_type:
                            x_unit, y_unit, unit_health, enemy_unit_ID = enemy.copy()
                            if y_unit < 14 and enemy_unit_ID == unit_ID:
                                coor_key = f"{x_unit},{y_unit}"
                                if count_of_enemy_unit_locations_our_side.get(coor_key) is None:
                                    count_of_enemy_unit_locations_our_side[coor_key] = 1
                                else:
                                    count_of_enemy_unit_locations_our_side[coor_key] += 1

            # Sort by place of highest occurrence on our side of occurrence
            count_of_enemy_unit_locations_our_side = {k: v for k, v in
                                                      sorted(count_of_enemy_unit_locations_our_side.items(),
                                                             key=lambda item: item[1], reverse=True)}
            spawned_walls = 0  # Spawn/upgrade at least three walls
            spawned_turrets = 0  # Nothing's spawned
            for key, value in count_of_enemy_unit_locations_our_side.items():
                enemy_location = [int(i) for i in key.split(',')]
                turret_distance_to_location = {}
                for turret_location_section in turret_location_sections:
                    for turret_location in turret_location_section:
                        turret_distance_to_location[','.join([str(i) for i in turret_location])] = np.linalg.norm(
                            np.array(turret_location) - np.array(enemy_location))

                wall_distance_to_location = {}
                for wall_location_section in wall_location_sections:
                    for wall_location in wall_location_section:
                        wall_distance_to_location[','.join([str(i) for i in wall_location])] = np.linalg.norm(
                            np.array(wall_location) - np.array(enemy_location))

                # Spawn/upgrade turret
                turret_distance_to_location = {k: v for k, v in
                                               sorted(turret_distance_to_location.items(), key=lambda item: item[1])}
                for key_2, val_2 in turret_distance_to_location.items():
                    turret_x, turret_y = [int(i) for i in key_2.split(',')]
                    tmp = game_state.attempt_spawn(TURRET, [turret_x, turret_y])  # Spawn turret
                    if not tmp:
                        spawned_turrets += game_state.attempt_upgrade([turret_x, turret_y])  # Spawn turret
                    spawned_turrets += tmp
                    if spawned_turrets >= min_turrets:
                        if not game_state.attempt_spawn(WALL, [turret_x, turret_y + 1]):  # Spawn protective wall
                            game_state.attempt_upgrade([turret_x, turret_y + 1])
                    if spawned_turrets >= min_turrets:
                        break

                # Spawn/upgrade walls
                wall_distance_to_location = {k: v for k, v in
                                             sorted(wall_distance_to_location.items(), key=lambda item: item[1])}
                for key_2, val_2 in wall_distance_to_location.items():
                    wall_x, wall_y = [int(i) for i in key_2.split(',')]
                    tmp = game_state.attempt_spawn(WALL, [wall_x, wall_y])  # Spawn wall
                    spawned_walls += game_state.attempt_upgrade([wall_x, wall_y])  # Spawn wall
                    spawned_walls += tmp
                    if spawned_walls >= min_walls:
                        break
                if spawned_walls >= min_walls or spawned_turrets >= min_turrets:
                    break


    def attack_with_interceptors_or_scouts(self, game_state):
        """
        Send out interceptors at opponent's 1st or 2nd weakest points (1:3 ratio)
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        
        [top_right, top_left, bottom_left, bottom_right] = game_state.game_map.get_edges()
        friendly_edges = bottom_left + bottom_right
        location_options = self.filter_blocked_locations(friendly_edges, game_state)
        #location_options = [edge for edge in friendly_edges if game_state.can_spawn(INTERCEPTOR, edge)]
        # for location in location_options:
        #     gamelib.debug_write("Location Option: {}".format(location))

        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        if game_state.turn_number == 1:
            deploy_location, target_location, predict_damage = self.least_damage_spawn_location(game_state, location_options)
        
        rand = random.random()
        if rand <= 0.30:    
            deploy_location, target_location, predict_damage = self.Nth_least_damage_spawn_location(game_state, location_options, 3)
        elif rand <= 0.70:
            deploy_location, target_location, predict_damage = self.Nth_least_damage_spawn_location(game_state, location_options, 2)
        else:
            deploy_location, target_location, predict_damage = self.least_damage_spawn_location(game_state, location_options)
        
        gamelib.debug_write("predict damage: ", predict_damage)
        gamelib.debug_write("INTERCEPTOR total health: ", 40 * game_state.number_affordable(INTERCEPTOR))
        if self.is_opposite_opponent_edge(game_state, deploy_location, target_location) and \
                ((40 * game_state.number_affordable(INTERCEPTOR) // 5) >= predict_damage):
            game_state.attempt_spawn(INTERCEPTOR, deploy_location, game_state.number_affordable(INTERCEPTOR))
        elif self.is_opposite_opponent_edge(game_state, deploy_location, target_location):
            gamelib.debug_write("Deploy Location", deploy_location)
            game_state.attempt_spawn(DEMOLISHER, deploy_location, game_state.number_affordable(DEMOLISHER))
            game_state.attempt_spawn(SCOUT, deploy_location, game_state.number_affordable(SCOUT))
        else:
            game_state.attempt_spawn(SCOUT, deploy_location, game_state.number_affordable(SCOUT))


    # def stall_with_interceptors(self, game_state):
    #     """
    #     Send out interceptors at random locations to defend our base from enemy moving units.
    #     """
    #     # We can spawn moving units on our edges so a list of all our edge locations
    #     friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
    #     # Remove locations that are blocked by our own structures 
    #     # since we can't deploy units there.
    #     deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
    #     # While we have remaining MP to spend lets send out interceptors randomly.
    #     while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
    #         # Choose a random deploy location.
    #         deploy_index = random.randint(0, len(deploy_locations) - 1)
    #         deploy_location = deploy_locations[deploy_index]
            
    #         game_state.attempt_spawn(INTERCEPTOR, deploy_location)
    #         """
    #         We don't have to remove the location since multiple mobile 
    #         units can occupy the same space.
    #         """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # # First let's figure out the cheapest unit
        # # We could just check the game rules, but this demonstrates how to use the GameUnit class
        # stationary_units = [WALL, TURRET, FACTORY]
        # cheapest_unit = WALL
        # for unit in stationary_units:
        #     unit_class = gamelib.GameUnit(unit, game_state.config)
        #     if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
        #         cheapest_unit = unit
        #
        # # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        # for x in range(27, 5, -1):
        #     game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    
    # def Nth_least_damage_self_destruct_spawn_location(self, game_state, location_options, enemy_locations, num=1):
    #     """
    #     This function will help us guess the Nth safest location to spawn moving units from.
    #     It considers that high chance that our opponent would build defensive units at the safest path on the turn, so we can 
    #     spawn our units at the 2nd safest location with certain probability.
    #     """
    #     damages = []
    #     target_locations = []
    #     # Get the damage estimate each path will take
    #     for location in location_options:
    #         path = game_state.find_path_to_edge(location)
    #         target_locations.append(path[-1])
    #         damage = 0
    #         for path_location in path:
    #             # Get number of enemy turrets that can attack each location and multiply by turret damage
    #             damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
    #         damages.append(damage)
    #     if len(damages) < 2:
    #         return [3, 10]
    #     n = self.nth_smallest(damages, num)
    #     # Now just return the location that takes the nth least damage
    #     return location_options[damages.index(n)], target_locations[damages.index(n)]

    def Nth_least_damage_spawn_location(self, game_state, location_options, num=1):
        """
        This function will help us guess the Nth safest location to spawn moving units from.
        It considers that high chance that our opponent would build defensive units at the safest path on the turn, so we can 
        spawn our units at the 2nd safest location with certain probability.
        """
        damages = []
        target_locations = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            target_locations.append(path[-1])
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        if len(damages) < 2:
            return [3, 10]
        n = self.nth_smallest(damages, num)
        # Now just return the location that takes the nth least damage
        return location_options[damages.index(n)], target_locations[damages.index(n)], n


    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        target_locations = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            target_locations.append(path[-1])
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        if len(damages) == 0:
            return [24, 10]
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))], target_locations[damages.index(min(damages))], min(damages)


    def nth_smallest(self, damages, num):
        '''
        Returns the nth smallest element in the list of damages
        '''    
        return sorted(damages)[num-1]


    def get_enemy_unit_type_coordinates(self, game_state, unit_type, valid_x = None, valid_y = None):
        unit_type_locations = []
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        unit_type_locations.append(location)
        return unit_type_locations
    
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
    
    def right_corner_attack_flag(self, game_state, NUMBER_UNITS_TO_FLAG = 5):
        counter = 0
        enemy_corner_locations = []
        enemy_corner_coors = [[13, 25], [14, 25], [14, 24], [15, 24], [15, 23], [16, 23], 
                               [16, 22], [17, 22], [17, 21], [18, 21], [18, 20], [19, 20], 
                               [19, 19], [20, 19], [20, 18], [21, 18], [21, 17], [22, 17], 
                               [22, 16], [23, 16], [23, 15], [24, 15], [24, 14], [25, 14]]
        
        enemy_structure_units = self.convert_enemy_units_to_coordinates()
        gamelib.debug_write("All Enemy Unit locations: {}".format(enemy_structure_units))

        for coor in enemy_corner_coors:
            if coor in enemy_structure_units:
                enemy_corner_locations.append(coor)
                counter = counter + 1
                if counter >= NUMBER_UNITS_TO_FLAG:
                    sorted(enemy_corner_locations, key=lambda k: k[0], reverse=True)
                    return True, enemy_corner_locations, counter
        sorted(enemy_corner_locations, key=lambda k: k[0], reverse=True)
        return False, enemy_corner_locations, counter

    def left_corner_attack_flag(self, game_state, NUMBER_UNITS_TO_FLAG = 5):
        counter = 0
        enemy_corner_locations = []
        
        enemy_corner_coors = [[14, 26], [13, 25], [14, 25], [12, 24], [13, 24], [11, 23], 
                               [12, 23], [10, 22], [11, 22], [9, 21], [10, 21], [8, 20], 
                               [9, 20], [7, 19], [8, 19], [6, 18], [7, 18], [5, 17], [6, 17], 
                               [4, 16], [5, 16], [3, 15], [4, 15], [2, 14], [3, 14]]
        
        enemy_structure_units = self.convert_enemy_units_to_coordinates()
        gamelib.debug_write("All Enemy Unit locations: {}".format(enemy_structure_units))

        for coor in enemy_corner_coors:
            if coor in enemy_structure_units:
                enemy_corner_locations.append(coor)
                counter = counter + 1
                if counter >= NUMBER_UNITS_TO_FLAG:
                    sorted(enemy_corner_locations, key=lambda k: k[0])
                    return True, enemy_corner_locations, counter
        sorted(enemy_corner_locations, key=lambda k: k[0])
        return False, enemy_corner_locations, counter
            
    def is_opposite_opponent_edge(self, game_state, start_location, opponent_location):
        [top_right, top_left, bottom_left, bottom_right] = game_state.game_map.get_edges()
        if ((start_location in bottom_left) and (opponent_location in top_right)) or \
           ((start_location in bottom_right) and (opponent_location in top_left)):
            return True
        else:
            return False

    
    def convert_enemy_units_to_coordinates(self):
        structure_units_coordinates = []
        last_round_enemy_units = self.enemy_location_all_rounds[-1]
        for item in last_round_enemy_units[0]:
            structure_units_coordinates.append([item[0], item[1]])
        for item in last_round_enemy_units[1]:
            structure_units_coordinates.append([item[0], item[1]])
        for item in last_round_enemy_units[2]:
            structure_units_coordinates.append([item[0], item[1]])
        return structure_units_coordinates

        
    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]

        # Save tracked information
        if state['turnInfo'][2] == 0:  # Had to use Action phase == 0  cause turn type is bugged
            self.breached_last_round = 0
            self.scored_on_locations.append([])
            self.enemy_location_all_rounds.append([])
            gamelib.debug_write("START OF ROUND Breached?", self.breached_last_round)


        # Track breaches
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_type = breach[2]
            unit_id = breach[3]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.breached_last_round = 1
                self.scored_on_locations[-1].extend([[location, unit_type, unit_id]])
                gamelib.debug_write("Breached?: {}".format(self.breached_last_round))
                #gamelib.debug_write("All locations: {}".format(self.scored_on_locations[-1]))

        # Track enemy location
        enemy_units = state['p2Units']
        self.enemy_location_all_rounds[-1] = enemy_units
       # gamelib.debug_write("All Enemy Unit locations: {}".format(self.enemy_location_all_rounds[-1]))

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()

