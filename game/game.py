import pandas as pd
import itertools
import random
import math 
import time
import curses
import os
from heroes import *
from skills import *
from game.status_effect_manager import StatusEffectManager

ORANGE = "\033[38;5;208m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Game:

    def __init__(self, player_heroes, opponent_heroes, mode, interface=None):
        self.player_heroes = player_heroes
        self.opponent_heroes = opponent_heroes
        self.mode = mode
        self.heroes = self.player_heroes + self.opponent_heroes
        self.defeated_heroes = []
        self.winner = []
        self.groups_hero = {}
        self.winner = []
        self.round_counter = 1
        self.round_counter_max = 30
        self.output_buffer = []
        self.interface = interface  # New addition to hold GameInterface instance
        self.status_manager = StatusEffectManager(self)  # Instantiate the status manager
        self.observers = []
        self.game_state = "game_initialization"
        self.current_action_hero = None  # Keep track of the hero currently taking action
        self.selected_skill_index = 0
        self.selected_target_index = 0
        self.valid_targets = []
        self.skill_selection_active = False


    def clear_screen(self):
        os.system('cls')
    
    def register_observer(self, observer):
        """Add an observer to the list."""
        self.observers.append(observer)

    def notify_observers(self):
        """Notify all observers of a state change."""
        for observer in self.observers:
            observer.update_display(self)

    def grouping(self):
      for hero in self.heroes:
        if hero.group not in self.groups_hero:
          self.groups_hero[hero.group] = []
        self.groups_hero[hero.group].append(hero)

    def update_allies_opponents_list(self):
      for hero in self.heroes:
          hero.allies = [h for h in self.heroes if h.group == hero.group and h.hp > 0]
          hero.allies_self_excluded = [h for h in hero.allies if h != hero]
          hero.opponents = [h for h in self.heroes if h.group != hero.group and h.hp > 0]

    def find_hero_with_summon_skills(self, heroes):
        for hero in heroes:
            for skill in hero.skills:
                if skill.skill_type == "summon":
                  hero.take_game_instance(self)

    def pass_game_instance(self, heroes):
        for hero in heroes:
            hero.take_game_instance(self)
    
    def pass_interface_to_heroes(self):
        for hero in self.heroes:
              hero.take_interface(self.interface)

    def update_hero_action_sequence(self):
        self.sorted_heroes = sorted(self.heroes, key=lambda hero: hero.agility, reverse=True)
        self.unactioned_sorted_heroes = self.sorted_heroes.copy()
        for hero in self.unactioned_sorted_heroes:
            if hero.actioned:
                self.unactioned_sorted_heroes.remove(hero)

    def reset_hero_action_label(self):
        for hero in self.heroes:
            hero.actioned = False

    def check_groups_status(self):
        alive_groups = set(hero.group for hero in self.heroes if hero.hp > 0)
        return alive_groups

    def update_battle_information(self):
      for hero in self.heroes:
        self.check_heroes_skill_cooldown(hero)
        #self.notify_observers()
      for hero in self.heroes:
        self.status_manager.check_heroes_status_effects(hero)
        #self.notify_observers()

    def check_heroes_skill_cooldown(self, hero):
      if hero.hp > 0:
        for skill in hero.skills:
            if skill.if_cooldown == True:
               if skill.cooldown > 0:
                skill.cooldown -=1
                self.display_status_updates(f"{GREEN}{hero.name}'s {skill.name} skill is cooling down. It will be usable after {skill.cooldown + 1} rounds.{RESET}")
               elif skill.cooldown == 0:
                self.display_status_updates(f"{GREEN}{hero.name}'s {skill.name} skill has finished cooldown. It can be used now.{RESET}")
                skill.if_cooldown = False

    def display_manual(self, message, delay = 1):
        self.output_buffer.append(message)
        if self.mode =="manual":
          time.sleep(delay)
          print(message)
        elif self.mode == "simulation":
          pass

    def display_manual_log(self, message, delay = 1):
        if self.mode =="manual":
          time.sleep(delay)
          for observer in self.observers:
                observer.add_log(message)
                observer.draw_game_log()
        elif self.mode == "simulation":
          pass

    def display_battle_info(self, message, delay = 2):
        # If the message is a string with multiple lines, split it into a list of lines
        if isinstance(message, str):
            message_lines = message.split("\n")
        elif isinstance(message, list):  # If it's already a list, use it directly
            message_lines = message
        else:
            raise ValueError("Message must be a string or a list of strings.")

        # Loop through each line and display it with a delay
        for line in message_lines:
            self.output_buffer.append(line)
            if self.mode =="manual":
              time.sleep(delay)
              print(line)
              #print(f"DEBUG: line = {line}, type = {type(line)}")  # Add this line to inspect the type
              for observer in self.observers:
                observer.add_log(line)
                observer.draw_game_log()
              #self.notify_observers()
            elif self.mode == "simulation":
              pass

    def display_status_updates(self, message, delay = 2):
        self.output_buffer.append(message)
        if self.mode =="manual":
          time.sleep(delay)
          print(message)
          for observer in self.observers:
                observer.add_log(message)
                observer.draw_game_log()
        elif self.mode == "simulation":
          pass

    def game_initialization(self):
       
        self.clear_screen()
        self.pass_game_instance(self.heroes)
        self.pass_interface_to_heroes()
        self.grouping()
        self.update_allies_opponents_list()
        self.display_manual(f"{MAGENTA}Welcome to Legends of Champions, Game Starts! {RESET}")
        self.display_manual(f"{ORANGE}Player Heroes:{RESET}")
        for hero in self.player_heroes:
            if hero.is_player_controlled == False:
              self.display_manual(f"{ORANGE}Name: {hero.name}(AI Player), Faculty: {hero.faculty}, HP: {hero.hp}{RESET}")
            else:
              self.display_manual(f"{ORANGE}Name: {hero.name}, Faculty: {hero.faculty}, HP: {hero.hp}{RESET}")
        self.display_manual(f"{BLUE}Opponent Heroes:{RESET}")
        for hero in self.opponent_heroes:
          self.display_manual(f"{BLUE}Name: {hero.name}, Faculty: {hero.faculty}, HP: {hero.hp}{RESET}")
        self.game_state = "round_start"

    def start_round(self): # Display Round count, HP, skill cool down, status information
        self.display_manual(f"{MAGENTA}---------------------------------------------------ROUND {self.round_counter}----------------------------------------------------{RESET}")
        self.display_manual_log(f"{MAGENTA} ---------------------------------------------------ROUND {self.round_counter}------------------------------------------------- {RESET}")
        player_heroes_info = []  # Initialize player heroes info as a list
        opponent_heroes_info = []  # Initialize opponent heroes info as a list

        # Clear up all defeated summoned units
        for hero in self.player_heroes:
          if hero.is_summoned == True and hero.hp <= 0:
            self.player_heroes.remove(hero)
        for hero in self.opponent_heroes:
          if hero.is_summoned == True and hero.hp <= 0:
            self.opponent_heroes.remove(hero)

        # Display hero information in the begining of each round
        for hero in self.player_heroes:
            player_hero_info = str(f"{ORANGE}Name: {hero.name}({hero.faculty}), HP: {hero.hp}/{hero.hp_max}{RESET}")
            player_heroes_info.append(player_hero_info)
        output = ' | '.join(player_heroes_info)
        output_with_color = output.replace('|', f' {MAGENTA}| ')
        self.display_manual(output_with_color)
        for hero in self.opponent_heroes:
            opponent_hero_info = str(f"{BLUE}Name: {hero.name}({hero.faculty}), HP: {hero.hp}/{hero.hp_max}{RESET}")
            opponent_heroes_info.append(opponent_hero_info)
        output = ' | '.join(opponent_heroes_info)
        output_with_color = output.replace('|', f' {MAGENTA}| ')
        self.display_manual(output_with_color)
        self.display_manual(f"{MAGENTA}---------------------------------------------------------------------------------------------------------------{RESET}")
        # Update allies opponents list
        self.update_allies_opponents_list()
        # Update skill cooldown, buff debuff status and effect in the begining of each round
        self.update_battle_information()
        # Check if game over
        if len(self.check_groups_status())  == 1 or len(self.check_groups_status()) == 0:
          self.game_state = "game_over"
          return

        # Remove any defeated heroes before the action phase begins
        self.heroes = [hero for hero in self.heroes if hero.hp > 0]
        # Sort heroes based on their agility, highest first
        self.sorted_heroes = sorted(self.heroes, key=lambda hero: hero.agility, reverse=True)
        # All hero unactioned in the begining of each round
        self.unactioned_sorted_heroes = self.sorted_heroes.copy()
        self.game_state = "hero_action"

      
    def hero_action(self): # Hero action: choose skill, choose target

        if not self.unactioned_sorted_heroes:
            self.game_state = "round_end"
            return

        hero = self.unactioned_sorted_heroes.pop(0)
        if hero.hp <= 0:
           return
        self.current_action_hero = hero
        self.selected_skill_index = 0
        self.valid_targets = hero.opponents  # Default to opponents
        self.selected_target_index = 0

        # Update allies and opponents list
        self.update_allies_opponents_list()

        if hero.status['shadow_word_insanity'] == True:
          hero_opponents = hero.allies
          hero_allies = hero.opponents
          if hero_opponents:  # Ensure there are opponents available
            self.display_battle_info(f"{hero.name} enters an insane state, unable to distinguish between friends and enemies.")
            result = hero.ai_action(hero_opponents, hero_allies)
            hero.status['shadow_word_insanity'] = False
            if result is not None:
              self.display_battle_info(result)
            if len(self.check_groups_status()) == 1 or len(self.check_groups_status()) == 0:
              self.game_state = "game_over"
              return
        else:
          if hero.is_player_controlled:
              self.skill_selection_active = True  # Activate skill selection
              result = hero.player_action(hero, hero.opponents, hero.allies)  # Execute the chosen skill and chosen target
              if result is not None:
                self.display_battle_info(result)
              if len(self.check_groups_status())  == 1 or len(self.check_groups_status()) == 0:
                self.game_state = "game_over"
                return
          else:
              if hero.opponents:  # Ensure there are opponents available
                  result = hero.ai_action(hero.opponents, hero.allies)
                  if result is not None:
                    self.display_battle_info(result)
                  if len(self.check_groups_status()) == 1 or len(self.check_groups_status()) == 0:
                    self.game_state = "game_over"
                    return
        hero.actioned = True
        self.sorted_heroes = sorted(self.heroes, key=lambda hero: hero.agility, reverse=True)
        #self.notify_observers()

    def end_round(self):
        self.round_counter += 1
        self.reset_hero_action_label()
        if self.round_counter >= self.round_counter_max or len(self.check_groups_status()) <= 1:
            self.game_state = "game_over"
        else:
            self.game_state = "round_start"

    def game_over(self):
        if self.round_counter == self.round_counter_max and len(self.check_groups_status()) > 1:
            self.display_manual(f"{MAGENTA}Max allowed round reached. Game Over! {RESET}")
        elif len(self.check_groups_status()) == 1:
            surviving_group = next(iter(self.check_groups_status()))
            self.display_manual(f"{MAGENTA}\nThe game is over. The winning group is: {surviving_group}{RESET}")
            surviving_heroes = [hero for hero in self.heroes if hero.hp > 0]
            if surviving_heroes:
                self.display_manual(f"{MAGENTA}The winning heroes are:{RESET}")
                for hero in surviving_heroes:
                    self.display_manual(f"{MAGENTA}{hero.name} with {hero.hp} HP left!{RESET}")
            else:
                self.display_manual("No heroes survived.")
        elif len(self.check_groups_status()) == 0:
            self.display_manual(f"{MAGENTA}\nThe game is over. Draw game! No heroes survived.{RESET}")
    '''
    def play_game(self):
        self.clear_screen()
        self.pass_game_instance(self.heroes)
        self.pass_interface_to_heroes()
        self.grouping()
        self.update_allies_opponents_list()
        self.display_manual(f"{MAGENTA}Welcome to Legends of Champions, Game Starts! {RESET}")

        self.display_manual(f"{ORANGE}Player Heroes:{RESET}")
        for hero in self.player_heroes:
            if hero.is_player_controlled == False:
              self.display_manual(f"{ORANGE}Name: {hero.name}(AI Player), Faculty: {hero.faculty}, HP: {hero.hp}{RESET}")
            else:
              self.display_manual(f"{ORANGE}Name: {hero.name}, Faculty: {hero.faculty}, HP: {hero.hp}{RESET}")
        self.display_manual(f"{BLUE}Opponent Heroes:{RESET}")
        for hero in self.opponent_heroes:
          self.display_manual(f"{BLUE}Name: {hero.name}, Faculty: {hero.faculty}, HP: {hero.hp}{RESET}")

        # Game continues until one hero's HP reaches 0 or less
        while len(self.check_groups_status()) > 1 and self.round_counter < self.round_counter_max:
            self.display_manual(f"{MAGENTA}---------------------------------------------------ROUND {self.round_counter} ----------------------------------------------------{RESET}")
            player_heroes_info = []  # Initialize player heroes info as a list
            opponent_heroes_info = []  # Initialize opponent heroes info as a list

            # Clear up all defeated summoned units
            for hero in self.player_heroes:
              if hero.is_summoned == True and hero.hp <= 0:
                self.player_heroes.remove(hero)
            for hero in self.opponent_heroes:
              if hero.is_summoned == True and hero.hp <= 0:
                self.opponent_heroes.remove(hero)

            # Display hero information in the begining of each round
            for hero in self.player_heroes:
                player_hero_info = str(f"{ORANGE}Name: {hero.name}({hero.faculty}), HP: {hero.hp}/{hero.hp_max}{RESET}")
                player_heroes_info.append(player_hero_info)
            output = ' | '.join(player_heroes_info)
            output_with_color = output.replace('|', f' {MAGENTA}| ')
            self.display_manual(output_with_color)
            for hero in self.opponent_heroes:
                opponent_hero_info = str(f"{BLUE}Name: {hero.name}({hero.faculty}), HP: {hero.hp}/{hero.hp_max}{RESET}")
                opponent_heroes_info.append(opponent_hero_info)
            output = ' | '.join(opponent_heroes_info)
            output_with_color = output.replace('|', f' {MAGENTA}| ')
            self.display_manual(output_with_color)
            self.display_manual(f"{MAGENTA}---------------------------------------------------------------------------------------------------------------{RESET}")

            self.update_allies_opponents_list()
            self.update_battle_information()
            if len(self.check_groups_status())  == 1 or len(self.check_groups_status()) == 0:
              return self.game_over()

            # Remove any defeated heroes before the action phase begins
            self.heroes = [hero for hero in self.heroes if hero.hp > 0]
            # Sort heroes based on their agility, highest first
            self.sorted_heroes = sorted(self.heroes, key=lambda hero: hero.agility, reverse=True)
            self.unactioned_sorted_heroes = self.sorted_heroes.copy()

            # Skip this hero's turn if they are defeated or they have already actioned
            i = 0
            while i < len(self.sorted_heroes):
                hero = self.sorted_heroes[i]
                if hero.hp <= 0 or hero.actioned == True:
                    i += 1
                    continue

                # Update allies and opponents list
                self.update_allies_opponents_list()

                if hero.status['shadow_word_insanity'] == True:
                  hero_opponents = hero.allies
                  hero_allies = hero.opponents
                  if hero_opponents:  # Ensure there are opponents available
                    self.display_battle_info(f"{hero.name} enters an insane state, unable to distinguish between friends and enemies.")
                    result = hero.ai_action(hero_opponents, hero_allies)
                    hero.status['shadow_word_insanity'] = False
                    if result is not None:
                      self.display_battle_info(result)
                    if len(self.check_groups_status()) == 1 or len(self.check_groups_status()) == 0:
                      return self.game_over()
                else:
                  if hero.is_player_controlled:
                      result = hero.player_action(hero, hero.opponents, hero.allies)  # Execute the chosen skill
                      if result is not None:
                        self.display_battle_info(result)
                      if len(self.check_groups_status())  == 1 or len(self.check_groups_status()) == 0:
                        return self.game_over()
                  else:
                      if hero.opponents:  # Ensure there are opponents available
                          result = hero.ai_action(hero.opponents, hero.allies)
                          if result is not None:
                            self.display_battle_info(result)
                          if len(self.check_groups_status()) == 1 or len(self.check_groups_status()) == 0:
                            return self.game_over()
                hero.actioned = True
                self.notify_observers()
                self.sorted_heroes = sorted(self.heroes, key=lambda hero: hero.agility, reverse=True)
                i = 0
            self.reset_hero_action_label()
            self.round_counter += 1

        return self.game_over()
        '''

    def display_hero_statuses(self):
            for hero in self.heroes:
                print(hero.show_info())
                print("------------------------------------------------")