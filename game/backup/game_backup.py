import math
import random
import os
from heroes import *
from skills.skill import Skill

RED = "\033[91m"
ORANGE = "\033[38;5;208m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Game:


    def __init__(self, player_heroes, opponent_heroes):
        self.player_heroes = player_heroes
        self.opponent_heroes = opponent_heroes
        self.heroes = self.player_heroes + self.opponent_heroes
        self.winner = []
        self.groups_hero = {}
        self.winner = []
        self.round_counter = 1
        self.round_counter_max = 30

    def clear_screen(self):
        os.system('cls')

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

    def check_groups_status(self):
        alive_groups = set(hero.group for hero in self.heroes if hero.hp > 0)
        return alive_groups

    def update_battle_information(self):
      for hero in self.heroes:
        self.check_heroes_skill_cooldown(hero)
      for hero in self.heroes:
        self.check_heroes_status_effects(hero)

    def check_heroes_skill_cooldown(self, hero):
      if hero.hp > 0:
        for skill in hero.skills:
            if skill.if_cooldown == True:
               if skill.cooldown > 0:
                skill.cooldown -=1
                print(f"{GREEN}{hero.name}'s {skill.name} skill is cooling down. It will be usable after {skill.cooldown + 1} rounds.{RESET}")
               elif skill.cooldown == 0:
                print(f"{GREEN}{hero.name}'s {skill.name} skill has finished cooldown. It can be used now.{RESET}")
                skill.if_cooldown = False

    def check_heroes_status_effects(self, hero):
        if hero.hp > 0: # Only process heroes who are not defeated
            # Handle Stun Duration
            if hero.status['stunned'] and hero.hp > 0:
                if hero.stun_duration > 0:
                    hero.stun_duration -= 1
                    print(f"{BLUE}{hero.name} is stunned and can't move.{RESET}")
                    #return f"{hero.name} remains stunned for {hero.stun_duration} more rounds."
                elif hero.stun_duration == 0:
                    hero.status['stunned'] = False
                    print(f"{BLUE}{hero.name} is no longer stunned.{RESET}")

            # Handle Frost Bolt Cold Debuff Duration
            if hero.status['cold'] and hero.hp > 0:
                hero.cold_duration -=1
                if hero.cold_duration > 0:
                    print(f"{BLUE}{hero.name} is feeling cold and moving slowly. {hero.name}'s Frost Bolt debuff duration is {hero.cold_duration} rounds{RESET}")
                elif hero.cold_duration == 0:
                    hero.agility = hero.agility + hero.agility_reduced_amount_by_frost_bolt  # Restore original agility
                    hero.agility_reduced_amount_by_frost_bolt = 0 # Reset the amount of agility reduced by frost bolt
                    hero.status['cold'] = False
                    print(f"{BLUE}{hero.name} is no longer feeling cold. {hero.name}'s agility has returned to {hero.agility}.{RESET}")

            # Handle Armor Breaker Debuff
            if hero.defense_debuff_duration > 0 and hero.hp > 0:
                hero.defense_debuff_duration -= 1
                print(f"{BLUE}{hero.name}'s Armor Breaker debuff duration is {hero.defense_debuff_duration} rounds.{RESET}")
                if hero.defense_debuff_duration == 0:
                    hero.defense = hero.defense + hero.defense_reduced_amount_by_armor_breaker  # Add back the reduce amount of defense by armor breaker
                    #print(f"{RED}{hero.name}'s defense returned to:' {hero.defense}, defense reduced amount: {hero.defense_reduced_amount_by_armor_breaker}{RESET}")
                    hero.defense_reduced_amount_by_armor_breaker = 0 # Reset the amount of defense reduced by armor breaker
                    hero.armor_breaker_stacks = 0 # Reset stack count
                    print(f"{BLUE}Armor Breaker effect has faded away from {hero.name}. {hero.name}'s defense has returned to {hero.defense}{RESET}")

            # Handle Shield of Righteous Buff
            #print(hero.defense_buff_duration)
            if hero.defense_buff_duration > 0 and hero.hp > 0:
                hero.defense_buff_duration -= 1
                print(f"{BLUE}{hero.name}'s Shield of Righteous effect duration is {hero.defense_buff_duration} rounds{RESET}")
                if hero.defense_buff_duration == 0:
                    hero.defense = hero.defense - hero.defense_increased_amount_by_shield_of_righteous  # Restore original defense
                    hero.defense_increased_amount_by_shield_of_righteous = 0 # Reset the amount of defense increased by shield of righteous
                    hero.shield_of_righteous_stacks = 0 # Reset stack count
                    print(f"{BLUE}Shield of Righteous effect has faded away from {hero.name}. {hero.name}'s defense has returned to {hero.defense}{RESET}")

            # Handle Shadow Word Pain Debuff Duration
            if hero.status['shadow_word_pain'] and hero.hp > 0:
                hero.shadow_word_pain_debuff_duration -=1
                if hero.shadow_word_pain_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    print(f"{BLUE}{hero.name}'s Shadow Word Pain debuff duration is {hero.shadow_word_pain_debuff_duration} rounds. {hero.take_damage(hero.shadow_word_pain_continuous_damage + variation)}{RESET}")
                    if hero.hp <=0:
                      print(f"{RED}{hero.name} has been defeated!{RESET}")
                      #if len(self.check_groups_status()) == 1:
                                  #return self.game_over()
                elif hero.shadow_word_pain_debuff_duration == 0:
                    hero.shadow_word_pain_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['shadow_word_pain'] = False
                    print(f"{BLUE}{hero.name} is no longer feeling pain. Shadow Word Pain effect has faded away from {hero.name}.{RESET}")

            # Handle Poison Dagger Debuff Duration
            if hero.status['poisoned_dagger'] and hero.hp > 0:
                hero.poisoned_dagger_debuff_duration -=1
                if hero.poisoned_dagger_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    print(f"{BLUE}{hero.name}'s Poisoned Dagger duration is {hero.poisoned_dagger_debuff_duration} rounds. {hero.take_damage(hero.poisoned_dagger_continuous_damage + variation)}{RESET}")
                    if hero.hp <=0:
                      print(f"{RED}{hero.name} has been defeated!{RESET}")
                      #if len(self.check_groups_status()) == 1:
                                  #return self.game_over()
                elif hero.poisoned_dagger_debuff_duration == 0:
                    hero.poisoned_dagger_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['poisoned_dagger'] = False
                    hero.poisoned_dagger_stacks = 0
                    print(f"{BLUE}{hero.name} is no longer poisoned.{RESET}")

            # Handle Sharp Blade Debuff Duration
            if hero.status['bleeding_sharp_blade'] and hero.hp > 0:
                hero.sharp_blade_debuff_duration -=1
                if hero.sharp_blade_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    print(f"{BLUE}{hero.name}'s bleeding effect from Sharp Blade is {hero.sharp_blade_debuff_duration} rounds. {hero.take_damage(hero.sharp_blade_continuous_damage + variation)}{RESET}")
                    if hero.hp <=0:
                      print(f"{RED}{hero.name} has been defeated!{RESET}")
                      #if len(self.check_groups_status()) == 1:
                                  #return self.game_over()
                elif hero.sharp_blade_debuff_duration == 0:
                    hero.sharp_blade_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['bleeding_sharp_blade'] = False
                    print(f"{BLUE}{hero.name} is no longer bleeding.{RESET}")

            # Shadow Evasion Buff Duration
            if hero.status['shadow_evasion'] and hero.hp > 0:
                hero.shadow_evasion_buff_duration -=1
                if hero.shadow_evasion_buff_duration > 0:
                    print(f"{BLUE}{hero.name} is hiding in shadow. {RESET}")
                elif hero.shadow_evasion_buff_duration == 0:
                    hero.status['shadow_evasion'] = False
                    hero.evasion_capability = 0
                    print(f"{BLUE}{hero.name}'s figure slowly emerged from the darkness.{RESET}")


    def play_game(self):
        self.clear_screen()
        print(f"{MAGENTA}Welcome to Dungeon Heros, Game Starts!{RESET}")
        #Grouping all heroes
        self.grouping()
        print("\n")
        print(f"{ORANGE}Player Heroes:{RESET}")
        for hero in self.player_heroes:
            if hero.is_player_controlled == False:
              print(f"{ORANGE}Name: {hero.name}(AI Player), Profession: {hero.profession}, HP: {hero.hp}{RESET}")
            else:
              print(f"{ORANGE}Name: {hero.name}, Profession: {hero.profession}, HP: {hero.hp}{RESET}")
        print("\n")
        print(f"{BLUE}Opponent Heroes:{RESET}")
        for hero in self.opponent_heroes:
          print(f"{BLUE}Name: {hero.name}, Profession: {hero.profession}, HP: {hero.hp}{RESET}")
        print("\n")
        # Game continues until one hero's HP reaches 0 or less
        while len(self.check_groups_status()) > 1 and self.round_counter < self.round_counter_max:
            print(f"{MAGENTA}-----------------------------------------ROUND {self.round_counter} ------------------------------------------{RESET}")

            self.update_allies_opponents_list()
            self.update_battle_information()
            if len(self.check_groups_status())  == 1:
              return self.game_over()

            # Remove any defeated heroes before the action phase begins
            self.heroes = [hero for hero in self.heroes if hero.hp > 0]
            # Sort heroes based on their agility, highest first
            self.sorted_heroes = sorted(self.heroes, key=lambda hero: hero.agility, reverse=True)

            for hero in self.sorted_heroes:

                if hero.hp <= 0:
                    continue # Skip this hero's turn if they are defeated

                # Update allies and opponents list
                self.update_allies_opponents_list()
                #opponents = [h for h in self.sorted_heroes if h != hero and h.hp > 0]
                #allies = [h for h in self.sorted_heroes if h != hero and h.hp > 0]
                if hero.is_player_controlled:
                    #print(hero.show_info())  # Show player hero status
                    result = hero.player_action(hero, hero.opponents, hero.allies)  # Execute the chosen skill
                    print(result)
                    for opponent in hero.opponents:
                            if opponent.hp <=0:
                                print(f"{RED}{opponent.name} has been defeated!{RESET}")
                                if len(self.check_groups_status())  == 1:
                                  return self.game_over()
                else:
                    if hero.opponents:  # Ensure there are opponents available
                        result = hero.ai_action(hero.opponents, hero.allies)
                        print(result)
                        # Check if any opponent has zero or less HP after action
                        for opponent in hero.opponents:
                            if opponent.hp <=0:
                                print(f"{RED}{opponent.name} has been defeated!{RESET}")
                                if len(self.check_groups_status()) == 1:
                                  return self.game_over()
                        #defeated_heroes = [h for h in opponents if h.hp <= 0]
                        #for defeated_hero in defeated_heroes:
                            #print(f"{defeated_hero.name} has been defeated!")
            self.round_counter += 1

        return self.game_over()


    def game_over(self):
        if self.round_counter == self.round_counter_max and len(self.check_groups_status()) > 1:
            print(f"{MAGENTA}Max allowed round reached. Game Over! {RESET}")
        else:
            surviving_group = next(iter(self.check_groups_status()))
            print(f"{MAGENTA}\nThe game is over. The winning group is: {surviving_group}{RESET}")
            surviving_heroes = [hero for hero in self.heroes if hero.hp > 0]
            if surviving_heroes:
                print(f"{MAGENTA}The winning heroes are:{RESET}")
                for hero in surviving_heroes:
                    print(f"{MAGENTA}{hero.name} with {hero.hp} HP left!{RESET}")
            else:
                print("No heroes survived.")


    def display_hero_statuses(self):
            for hero in self.heroes:
                print(hero.show_info())
                print("------------------------------------------------")