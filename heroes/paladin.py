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

class Paladin_Retribution(Paladin):

    major = "Retribution"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Hammer of Anger", self.hammer_of_anger, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Crusader Strike", self.crusader_strike, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Flash of Light", self.flash_of_light, "single", skill_type= "healing"))

    def hammer_of_anger(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.defense
        damage_dealt = max(damage_dealt, 0)
        if self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 1:
          extra_holy_damage = random.randint(3, 5)
          damage_dealt += extra_holy_damage
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}, due to Shield of Righteous, this attack causes extra {extra_holy_damage} holy damage.")
        elif self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 2:
          extra_holy_damage = random.randint(6, 8)
          damage_dealt += extra_holy_damage
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}, due to Shield of Righteous, this attack causes extra {extra_holy_damage} holy damage.")
        else:
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def crusader_strike(self, other_hero):
        accuracy = 100  # Crusader strike has 100% chance to activate the wrath of crusader effect
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          if self.status['wrath_of_crusader'] == False:
            self.status['wrath_of_crusader'] = True
            agility_before_increasing = self.agility
            agility_increased_amount_by_wrath_of_crusader_single = math.ceil(self.original_agility * 0.75)  # Increase hero's agility by 75%
            self.agility_increased_amount_by_wrath_of_crusader = self.agility_increased_amount_by_wrath_of_crusader + agility_increased_amount_by_wrath_of_crusader_single  # Defense increase accumulated
            self.agility = self.agility + agility_increased_amount_by_wrath_of_crusader_single
            self.wrath_of_crusader_stacks += 1
            self.wrath_of_crusader_duration = 3  # Effect lasts for 2 rounds
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike, {self.name} is in Wrath of Crusader status, their agility has increased from {agility_before_increasing} to {self.agility}.")
          else:
            if self.wrath_of_crusader_stacks < 2: # wrath of crusader effect can stack for two times.
              agility_before_increasing = self.agility
              agility_increased_amount_by_wrath_of_crusader_single = math.ceil(self.original_agility * 0.75)  # Increase hero's agility by 75%
              self.agility_increased_amount_by_wrath_of_crusader = self.agility_increased_amount_by_wrath_of_crusader + agility_increased_amount_by_wrath_of_crusader_single  # Defense increase accumulated
              self.agility = self.agility + agility_increased_amount_by_wrath_of_crusader_single
              self.wrath_of_crusader_stacks += 1
              self.wrath_of_crusader_duration = 3  # Effect lasts for 2 rounds
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike, {self.name} is in Wrath of Crusader status, their agility has increased from {agility_before_increasing} to {self.agility}.")
            else:
              self.wrath_of_crusader_duration = 3
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike. Wrath of Crusader buff duration refreshed.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike.")
        basic_damage = 20
        variation = random.randint(-2, 2)
        damage_dealt = basic_damage + variation
        return other_hero.take_damage(damage_dealt)

    def flash_of_light(self, other_hero):
        variation = random.randint(0, 2)
        healing_amount_base = 19
        healing_amount = healing_amount_base + variation
        if self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 1:
          extra_healing = random.randint(5, 7)
          healing_amount = healing_amount_base + extra_healing
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}, due to Wrath of Crusader, this spell gains an additional {extra_healing} healing.")
        elif self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 2:
          extra_healing = random.randint(11, 13)
          healing_amount = healing_amount_base + extra_healing
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}, due to Wrath of Crusader, this spell gains an additional {extra_healing} healing.")
        else:
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}.")
        return other_hero.take_healing(healing_amount)

# Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_hammer_of_anger = 0.3
      self.probability_crusader_strike = 0.4
      self.probability_flash_of_light = 0.3

    def strategy_1(self):
      self.probability_hammer_of_anger = 1
      self.probability_crusader_strike = 0
      self.probability_flash_of_light = 0

    def strategy_2(self):
      self.probability_hammer_of_anger = 0
      self.probability_crusader_strike = 1
      self.probability_flash_of_light = 0

    def strategy_3(self):
      self.probability_hammer_of_anger = 0
      self.probability_crusader_strike = 0
      self.probability_flash_of_light = 1


    def battle_analysis(self, opponents, allies):
      # Sort hp from low to high
      sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
      sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
      sorted_allies_excludes_self = [ally for ally in sorted_allies if ally != self]

      # Priority targets tackling strategy--->
      # Prioritize keeping Shield of Righteous active
      if self.wrath_of_crusader_stacks < 1 or self.wrath_of_crusader_duration <= 1:
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
        skill_weights = [self.probability_hammer_of_anger, self.probability_crusader_strike, self.probability_flash_of_light]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent

class Paladin_Protection(Paladin):

    major = "Protection"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Hammer of Revenge", self.hammer_of_revenge, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shield of Righteous", self.shield_of_righteous, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Heroric Charge", self.heroric_charge, target_type = "single", skill_type= "damage", is_control_skill = True))

    def hammer_of_revenge(self, other_hero):
        variation = random.randint(-4, -1)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.defense
        damage_dealt = max(damage_dealt, 0)

        # Check if there is debuff on self
        hero_status_activated = [key for key, value in self.status.items() if value == True]
        set_comb = set(self.list_status_debuff_magic) | set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) | set(self.list_status_debuff_physical)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        #print(f"{RED}DEBUG Message: status_list_for_action = {status_list_for_action}{RESET}")
        if len(status_list_for_action) == 0:
          extra_holy_damage = 0
        elif len(status_list_for_action) == 1:
          extra_holy_damage = random.randint(3, 5)
          self.game.display_battle_info(f"{self.name} is furying due to the debuff they suffered, Hammer of Revenge will have a higher damage.")
        elif len(status_list_for_action) == 2:
          extra_holy_damage = random.randint(6, 8)
          self.game.display_battle_info(f"{self.name} is highly furying due to the debuff they suffered, Hammer of Revenge will have a higher damage.")
        elif len(status_list_for_action) >= 3:
          extra_holy_damage = random.randint(9, 11)
          self.game.display_battle_info(f"{self.name} is extremly furying due to the debuff they suffered, Hammer of Revenge will have a higher damage.")
        damage_dealt += extra_holy_damage 

        if self.status['shield_of_righteous'] == True and other_hero.status['hammer_of_revenge'] == False:
          other_hero.status['hammer_of_revenge'] = True
          other_hero.hammer_of_revenge_duration = 3   # Effect lasts for 2 rounds
          damage_before_reducing = other_hero.damage
          other_hero.damage_reduced_amount_by_hammer_of_revenge = round(other_hero.original_damage * 0.2)  # Reduce target's damage by 20%
          other_hero.damage = other_hero.damage - other_hero.damage_reduced_amount_by_hammer_of_revenge
          self.game.display_battle_info(f"{self.name} uses Hammer of Revenge on {other_hero.name}, due to Shield of Righteous, {other_hero.name}'s damage is reduced from {damage_before_reducing} to {other_hero.damage}.")
        else:
          self.game.display_battle_info(f"{self.name} uses Hammer of Revenge on {other_hero.name}.")
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

    def heroric_charge(self, other_hero):
        basic_damage = round((self.damage - other_hero.defense) * 1)
        variation = random.randint(-1, 1)
        actual_damage = max(1, basic_damage + variation)
        basic_healing_heroric_charge = 22
        variation = random.randint(-2, 2)
        actual_healing = basic_healing_heroric_charge + variation
        if other_hero.is_immunity_condition_control == True:
           if other_hero.status['magic_casting'] == True:
             result = self.interrupt_magic_casting(other_hero)
             return f"{result}. {other_hero.take_damage(actual_damage)}."
           else:
             return f"{other_hero.take_damage(actual_damage)}."
        else:
          other_hero.status['scoff'] = True
          for debuff in other_hero.debuffs:
            if debuff.name == "Scoff":
              other_hero.debuffs.remove(debuff)
              other_hero.buffs_debuffs_recycle_pool.append(debuff)
          for debuff in other_hero.buffs_debuffs_recycle_pool:
            if debuff.name == "Scoff" and debuff.initiator == self:
                other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                debuff.duration = 1
                other_hero.add_debuff(debuff)   
          else:
              debuff = Debuff(
                  name='Scoff',
                  duration=1,
                  initiator=self,
                  effect=1
              )
              other_hero.add_debuff(debuff)

          if other_hero.status['magic_casting'] == True:
            result = self.interrupt_magic_casting(other_hero)
            for skill in self.skills:
              if skill.name == "Heroric Charge":
                skill.if_cooldown = True
                skill.cooldown = 3
            return f"Holy light showers {self.name}. {self.take_healing(actual_healing)}. {self.name} casts Heroric Charge on {other_hero.name}. {result}. {other_hero.take_damage(actual_damage)}. {other_hero.name} developed a deep hatred toward {self.name}."
          else:
            for skill in self.skills:
              if skill.name == "Heroric Charge":
                skill.if_cooldown = True
                skill.cooldown = 3
            return f"Holy light showers {self.name}. {self.take_healing(actual_healing)}. {self.name} casts Heroric Charge on {other_hero.name}. {other_hero.take_damage(actual_damage)}. {other_hero.name} developed a deep hatred toward {self.name}."

# Battling Strategy_________________________________________________________
'''
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
'''

class Paladin_Holy(Paladin):

    major = "Holy"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Purify Healing", self.purify_healing, target_type = "single", skill_type= "healing"))
            self.add_skill(Skill(self, "Holy Blast", self.holy_blast, target_type = "multi", skill_type= "damage", target_qty= 2))
            self.add_skill(Skill(self, "Shield of Protection", self.shield_of_protection, target_type = "single", skill_type= "buffs", target_qty= 0))

    def purify_healing(self, other_hero):
        variation = random.randint(-2, 2)
        basic_healing = 25
        actual_healing = basic_healing + variation
        hero_status_activated = [key for key, value in other_hero.status.items() if value == True]
        set_comb = set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) | set(self.list_status_debuff_toxic)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        #print(status_list_for_action)

        if other_hero.status['purify_healing'] == False:
            other_hero.status['purify_healing'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Purify Healing" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 2   # Effect lasts for 2 rounds
                    other_hero.add_buff(buff)
                    break
            else:        
              buff = Buff(
                  name='Purify Healing',
                  duration = 2,
                  initiator = self,
                  effect = 1.0
              )
              other_hero.add_buff(buff)
            
        else:
            for buff in other_hero.buffs:
                if buff.name == "Purify Healing" and buff.initiator == self:
                    buff.duration = 2   # Refresh effect
        
        self.game.display_battle_info(f"{self.name} uses Purify Healing on {other_hero.name}.")
        if status_list_for_action:
          random.shuffle(status_list_for_action)
          self.game.status_dispeller.dispell_status([status_list_for_action[0]], other_hero)
        return other_hero.take_healing(actual_healing)

    def holy_blast(self, other_heros):
        if not isinstance(other_heros, list):
          other_heros = [other_heros]
        results = []
        basic_damage = 22
        variation = random.randint(-2, 3)
        actual_damage = basic_damage + variation
        for i, opponent in enumerate(other_heros):
          #print(f"i = {i}")
          if i == 0:
              damage_multiplier = 3 / 3  # 100% damage for the first target
          else:
              damage_multiplier = 2 / 3  # 66.67% damage for subsequent targets
          damage = math.ceil(actual_damage * damage_multiplier)
          #print(f"damage = {damage}")
          self.game.display_battle_info(f"{self.name} casts Holy Blast at {opponent.name}.")
          results.append(opponent.take_damage(damage))
        return "\n".join(results)

    def shield_of_protection(self):
        hero_status_activated = [key for key, value in self.status.items() if value == True]
        set_comb = set(self.list_status_debuff_magic)  | set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) |set(self.list_status_debuff_physical)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        self.game.display_battle_info(f"{self.name} uses Shield of Protection.")
        self.game.status_dispeller.dispell_status(status_list_for_action, self)

        if self.status['shield_of_protection'] == False:
            self.status['shield_of_protection'] = True
        self.shield_of_protection_duration = 2
        for skill in self.skills:
            if skill.name == "Shield of Protection":
              skill.if_cooldown = True
              skill.cooldown = 3
        return f"{YELLOW}{self.name} is immune towards all damage.{RESET}"


# Battling Strategy_________________________________________________________
'''
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
'''