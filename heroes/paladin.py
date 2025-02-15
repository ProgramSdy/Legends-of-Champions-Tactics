import math
import random
from heroes import *
from skills import *

ORANGE = "\033[38;5;208m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Paladin(Hero):

    faculty = "Paladin"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "hybrid"

class Paladin_Comprehensiveness(Paladin):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Hammer of Anger", self.hammer_of_anger, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shield of Righteous", self.shield_of_righteous, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Flash of Light", self.flash_of_light, "single", skill_type= "healing"))

    def hammer_of_anger(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.defense
        damage_dealt = max(damage_dealt, 0)
        if self.status['shield_of_righteous'] == True and self.shield_of_righteous_stacks == 1:
          extra_holy_damage = random.randint(3, 5)
          damage_dealt += extra_holy_damage
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}, due to Shield of Righteous, this attack causes extra {extra_holy_damage} holy damage.")
        elif self.status['shield_of_righteous'] == True and self.shield_of_righteous_stacks == 2:
          extra_holy_damage = random.randint(6, 8)
          damage_dealt += extra_holy_damage
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}, due to Shield of Righteous, this attack causes extra {extra_holy_damage} holy damage.")
        else:
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def shield_of_righteous(self, other_hero):
        accuracy = 100  # Shield of Righteous has a 100% chance to activate the defense increasing effect
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          if self.status['shield_of_righteous'] == False:
            self.status['shield_of_righteous'] = True
            defense_before_increasing = self.defense
            defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.original_defense * 0.15)  # Increase hero's defense by 15%
            self.defense_increased_amount_by_shield_of_righteous = self.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
            self.defense = self.defense + defense_increased_amount_by_shield_of_righteous_single
            self.shield_of_righteous_stacks += 1
            self.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous, defense of {self.name} has increased from {defense_before_increasing} to {self.defense}.")
          else:
            if self.shield_of_righteous_stacks < 2: #shield of righteous effect can stack for two times.
              defense_before_increasing = self.defense
              defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.original_defense * 0.15)  # Increase hero's defense by 15%
              self.defense_increased_amount_by_shield_of_righteous = self.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
              self.defense = self.defense + defense_increased_amount_by_shield_of_righteous_single
              self.shield_of_righteous_stacks += 1
              self.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous, defense of {self.name} has increased from {defense_before_increasing} to {self.defense}.")
            else:
              self.shield_of_righteous_duration = 3
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous. Shield of Righteous buff duration refreshed")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous.")
        basic_damage = 20
        variation = random.randint(-2, 2)
        damage_dealt = basic_damage + variation
        return other_hero.take_damage(damage_dealt)

    def flash_of_light(self, other_hero):
        variation = random.randint(0, 2)
        healing_amount_base = 19
        healing_amount = healing_amount_base + variation
        if self.status['shield_of_righteous'] == True and self.shield_of_righteous_stacks == 1:
          extra_healing = random.randint(5, 7)
          healing_amount = healing_amount_base + extra_healing
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}, due to Shield of Righteous, this spell gains an additional {extra_healing} healing.")
        elif self.status['shield_of_righteous'] == True and self.shield_of_righteous_stacks == 2:
          extra_healing = random.randint(11, 13)
          healing_amount = healing_amount_base + extra_healing
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}, due to Shield of Righteous, this spell gains an additional {extra_healing} healing.")
        else:
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}.")
        return other_hero.take_healing(healing_amount)

# Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_hammer_of_anger = 0.3
      self.probability_shield_of_righteous = 0.4
      self.probability_flash_of_light = 0.3

    def strategy_1(self):
      self.probability_hammer_of_anger = 1
      self.probability_shield_of_righteous = 0
      self.probability_flash_of_light = 0

    def strategy_2(self):
      self.probability_hammer_of_anger = 0
      self.probability_shield_of_righteous = 1
      self.probability_flash_of_light = 0

    def strategy_3(self):
      self.probability_hammer_of_anger = 0
      self.probability_shield_of_righteous = 0
      self.probability_flash_of_light = 1


    def battle_analysis(self, opponents, allies):
      # Sort hp from low to high
      sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
      sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
      sorted_allies_excludes_self = [ally for ally in sorted_allies if ally != self]

      # Priority targets tackling strategy--->
      # Prioritize keeping Shield of Righteous active
      if self.shield_of_righteous_stacks < 1 or self.shield_of_righteous_duration <= 1:
        self.strategy_2()  # Focus on casting Shield of Righteous if not activated
        return sorted_opponents[0]  # Attack to keep the buff up
      # Decide if damage or healing
      if sorted_allies[0].hp <= round(0.35 * sorted_allies[0].hp_max):
        if sorted_opponents[0].hp <= round(0.25 * sorted_opponents[0].hp_max):
          accuracy = 50 # When there is an low hp ally and a low hp opponent, there is 50-50 chance to damage or to heal
          roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
          if roll <= accuracy:
            if sorted_opponents[0].faculty == "Warrior" or sorted_opponents[0].faculty == "Paladin": # eliminate low hp high defense target
              self.strategy_2()
              opponent = sorted_opponents[0]
              return opponent
            else: # eliminate low hp low defense target
              self.strategy_1()
              opponent = sorted_opponents[0]
              return opponent
          else:
            self.strategy_3()
            ally = sorted_allies[0]
            return ally
        else:
          self.strategy_3()
          ally = sorted_allies[0]
          return ally

      # Cast damage to low defense high threat target
      valid_classes = ["Mage", "Warlock", "Necromancer", "Rogue"]
      # Filter opponents to only include those from valid_classes
      sorted_opponents_high_threat = [opponent for opponent in opponents if opponent.faculty in valid_classes]
      if sorted_opponents_high_threat:
        sorted_opponents_high_threat = sorted(sorted_opponents_high_threat, key=lambda hero: hero.hp, reverse=False)
        opponent = sorted_opponents_high_threat[0]
        self.strategy_1()
        return opponent
      else:
        opponent = sorted_opponents[0]
        if opponent.faculty == "Warrior" or opponent.faculty == "Paladin":
          self.strategy_2()
          return opponent
        else: # conduct damage to priest
          self.strategy_1()
          return opponent

    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_hammer_of_anger, self.probability_shield_of_righteous, self.probability_flash_of_light]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent