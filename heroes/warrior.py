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

class Warrior(Hero):
    
    faculty = "Warrior"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "physical"

class Warrior_Comprehensiveness(Warrior):
    
    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.damage_type = "physical"
            self.probability_armor_breaker = 0
            self.probability_shield_bash = 0
            self.probability_slash = 0
            self.preset_target = None
            self.add_skill(Skill(self, "Slash", self.slash, target_type = "single", skill_type= "damage",))
            self.add_skill(Skill(self, "Shield Bash", self.shield_bash, target_type = "single", skill_type= "damage", capable_interrupt_magic_casting = True))
            self.add_skill(Skill(self, "Armor Breaker", self.armor_breaker, target_type = "single", skill_type= "damage"))

    def slash(self, other_hero):
      variation = random.randint(-3, 3)
      actual_damage = self.damage + variation
      damage_dealt = actual_damage - other_hero.defense
      damage_dealt = max(damage_dealt, 0)
      # Consider different situations
      if other_hero.status['bleeding_slash'] == True:
        self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash.")
      else:
        if other_hero.status['armor_breaker'] == True:
          accuracy = 100  # Bleeding effect has a 85% chance to succeed
          roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
          if roll <= accuracy:
            other_hero.status['bleeding_slash'] = True
            other_hero.status['normal'] = False
            other_hero.bleeding_slash_duration = other_hero.armor_breaker_stacks + 1
            other_hero.bleeding_slash_continuous_damage = random.randint(8, 12)
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash, {other_hero.name} got injured and start bleeding because of their broken armor.")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash")
        else:
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash.")
      # apply damage
      return other_hero.take_damage(damage_dealt)

    def shield_bash(self, other_hero):
        accuracy = 70  # Shield Bash has a 70% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if other_hero.status['magic_casting'] == True:
          result = self.interrupt_magic_casting(other_hero)
          if roll <= accuracy:
              other_hero.status['stunned'] = True
              other_hero.status['normal'] = False
              other_hero.stun_duration += 1
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned. {result}")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash. {result}")
        else:
          if roll <= accuracy:
            other_hero.status['stunned'] = True
            other_hero.status['normal'] = False
            other_hero.stun_duration += 1
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned.")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash")
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/2)
            # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
          # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def armor_breaker(self, other_hero):
        damage_dealt = self.random_in_range((8, 14))  # Small damage
        if other_hero.status['armor_breaker'] == True:
          if other_hero.armor_breaker_stacks < 3:
              defense_before_reducing = other_hero.defense
              defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
              other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.armor_breaker_stacks += 1
              other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
              self.game.display_battle_info(f"{self.name} uses Armor Breaker on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")
          else:
              other_hero.armor_breaker_duration = 2  # Refresh armor breaker effect
              self.game.display_battle_info(f"{self.name} uses Armor Breaker on {other_hero.name}, but {other_hero.name}'s Armor Breaker effect cannot be further stacked. Armor Breaker duration refreshed")
        else:
          other_hero.status['armor_breaker'] = True
          defense_before_reducing = other_hero.defense
          defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
          other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.armor_breaker_stacks += 1
          other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
          self.game.display_battle_info(f"{self.name} uses Armor Breaker on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")

        return other_hero.take_damage(damage_dealt)

    # Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_armor_breaker = 0.25
      self.probability_shield_bash = 0.25
      self.probability_slash = 0.5

    def strategy_1(self):
      self.probability_armor_breaker = 0
      self.probability_shield_bash = 1
      self.probability_slash = 0

    def strategy_2(self):
      self.probability_armor_breaker = 0.9
      self.probability_shield_bash = 0
      self.probability_slash = 0.1

    def strategy_3(self):
      self.probability_armor_breaker = 0.5
      self.probability_shield_bash = 0
      self.probability_slash = 0.5

    def strategy_4(self):
      self.probability_armor_breaker = 0
      self.probability_shield_bash = 0
      self.probability_slash = 1

    def strategy_5(self):
      self.probability_armor_breaker = 0
      self.probability_shield_bash = 0.5
      self.probability_slash = 0.5

    def battle_analysis(self, opponents, allies):
      # Sort hp from low to high
      sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
      sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
      sorted_allies_excludes_self = sorted_allies.copy()
      for ally in sorted_allies_excludes_self:
        if ally == self:
          sorted_allies_excludes_self.remove(ally)

      # Priority targets tackling strategy
      # 1 Slash target hp < 35%
      for opponent in sorted_opponents:
        if opponent.hp <= 0.45 * opponent.hp_max and opponent.faculty != "Warrior" and opponent.faculty != "Paladin":
          self.strategy_4()
          return opponent
        elif opponent.hp <= 0.25 * opponent.hp_max and (opponent.faculty == "Warrior" or opponent.faculty == "Paladin"):
          self.strategy_4()
          return opponent
        elif opponent.hp <= 0.55 * opponent.hp_max:
          self.strategy_5()
          return opponent

      for opponent in opponents:
        if opponent.status['magic_casting'] == True:
          self.strategy_1()
          return opponent
      for opponent in opponents:
          if opponent.status['armor_breaker'] == True and opponent.armor_breaker_stacks < 2:
            if opponent.faculty == 'Mage' or opponent.faculty == 'Rogue':
              self.strategy_4()
              return opponent
            else:
              self.strategy_3()
              return opponent
          elif opponent.status['armor_breaker'] == True and opponent.armor_breaker_stacks >= 2:
            self.strategy_4()
            return opponent

      # If no priority targets, then random choose one target and utilize corresponding strategy
      opponent = random.choice(opponents)
      if opponent.faculty == 'Mage' or opponent.faculty == 'Rogue':
        self.strategy_2()
        return opponent
      if opponent.faculty == 'Warrior' or opponent.faculty == 'Paladin':
        self.strategy_2()
        return opponent

      return opponent


    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_slash, self.probability_shield_bash, self.probability_armor_breaker]
        #available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        #chosen_skill = random.choice(available_skills)
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent

    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])
    
class Warrior_Defence(Warrior):
    
    major = "Defence"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.damage_type = "physical"
            self.probability_armor_breaker = 0
            self.probability_shield_bash = 0
            self.probability_slash = 0
            self.preset_target = None
            self.add_skill(Skill(self, "Devastate", self.devastate, target_type = "single", skill_type= "damage",))
            self.add_skill(Skill(self, "Shield Bash", self.shield_bash, target_type = "single", skill_type= "damage", capable_interrupt_magic_casting = True))
            self.add_skill(Skill(self, "Shield Lash", self.shield_lash, target_type = "single", skill_type= "damage"))

    def shield_bash(self, other_hero):
        accuracy = 100  # Shield Bash has a 100% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if other_hero.status['magic_casting'] == True:
          result = self.interrupt_magic_casting(other_hero)
          if roll <= accuracy:
              other_hero.status['stunned'] = True
              other_hero.status['normal'] = False
              other_hero.stun_duration += 1
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned. {result}")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash. {result}")
        else:
          if roll <= accuracy:
            other_hero.status['stunned'] = True
            other_hero.status['normal'] = False
            other_hero.stun_duration += 1
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned.")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash")
        for skill in self.skills:
            if skill.name == "Shield Bash":
              skill.if_cooldown = True
              skill.cooldown = 3
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/4)
        damage_dealt = max(damage_dealt, 0)
        return other_hero.take_damage(damage_dealt)

    def devastate(self, other_hero):
        variation = random.randint(-1, 1)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.75)
        damage_dealt = max(damage_dealt, 1)
        if other_hero.status['armor_breaker'] == True:
           other_hero.armor_breaker_duration = 2  # Refresh armor breaker effect
           self.game.display_battle_info(f"{self.name} uses Devastate on {other_hero.name}, refreshes their duration of Armor Breaker")
        else:
          other_hero.status['armor_breaker'] = True
          defense_before_reducing = other_hero.defense
          defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
          other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.armor_breaker_stacks += 1
          other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
          self.game.display_battle_info(f"{self.name} uses Devastate on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")

        return other_hero.take_damage(damage_dealt)

    def shield_lash(self, other_hero):
        other_hero.status['scoff'] = True
        self.status['shield_lash'] = True
        self.fire_resistance_boost_amount['shield_lash'] = 45
        self.frost_resistance_boost_amount['shield_lash'] = 45
        self.death_resistance_boost_amount['shield_lash'] = 45
        self.nature_resistance_boost_amount['shield_lash'] = 45
        basic_damage = round((self.damage - other_hero.defense) * 1/3)
        variation = random.randint(-1, 1)
        actual_damage = max(1, basic_damage + variation)

        fire_resistance_before_increasing = other_hero.fire_resistance
        frost_resistance_before_increasing = other_hero.frost_resistance 
        death_resistance_before_increasing = other_hero.death_resistance
        nature_resistance_before_increasing = other_hero.nature_resistance
        self.fire_resistance = self.fire_resistance + self.fire_resistance_boost_amount['shield_lash']
        self.frost_resistance = self.frost_resistance + self.frost_resistance_boost_amount['shield_lash']
        self.death_resistance = self.death_resistance + self.death_resistance_boost_amount['shield_lash']
        self.nature_resistance = self.nature_resistance + self.nature_resistance_boost_amount['shield_lash']
        
        for skill in self.skills:
            if skill.name == "Shield Lash":
              skill.if_cooldown = True
              skill.cooldown = 3
        for debuff in other_hero.debuffs:
          if debuff.name == "Scoff":
            other_hero.debuffs.remove(debuff)
            other_hero.buffs_debuffs_recycle_pool.add(debuff)
        for debuff in other_hero.buffs_debuffs_recycle_pool:
          if debuff.name == "Scoff" and debuff.initiator == self:
              other_hero.buffs_debuffs_recycle_pool.remove(debuff)
              debuff.duration = 1
              other_hero.add_debuff(debuff)
              break   
        else:
            debuff = Debuff(
                name='Scoff',
                duration=1,
                initiator=self,
                effect=1
            )
            other_hero.add_debuff(debuff)

        for buff in self.buffs_debuffs_recycle_pool:
                if buff.name == "Shield Lash" and buff.initiator == self:
                    self.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 2
                    self.add_buff(buff)   
                    break
        else:
            buff = Buff(
                name='Shield Lash',
                duration=2,
                initiator=self,
                effect=1
            )
            self.add_buff(buff)

        if other_hero.status['magic_casting'] == True:
          result = self.interrupt_magic_casting(other_hero)
          other_hero.scoff_shield_lash_duration = 2
          return f"{self.name} casts Shield Lash on {other_hero.name}. {result}. {other_hero.take_damage(actual_damage)}. {self.name}'s resistance is boost. {other_hero.name} developed a deep hatred toward {self.name}."
        else:
          other_hero.scoff_shield_lash_duration = 2
          return f"{self.name} casts Shield Lash on {other_hero.name}. {other_hero.take_damage(actual_damage)}. {self.name}'s resistance is boost. {other_hero.name} developed a deep hatred toward {self.name}."

    # Battling Strategy_________________________________________________________

class Warrior_Weapon_Master(Warrior):
    
    major = "Weapon_Master"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.damage_type = "physical"
            self.probability_armor_breaker = 0
            self.probability_shield_bash = 0
            self.probability_slash = 0
            self.preset_target = None
            self.add_skill(Skill(self, "Fatal Strike", self.fatal_strike, target_type = "single", skill_type= "damage",))
            #self.add_skill(Skill(self, "Shield Bash", self.shield_bash, target_type = "single", skill_type= "damage", capable_interrupt_magic_casting = True))
            self.add_skill(Skill(self, "Armor Crush", self.armor_crush, target_type = "single", skill_type= "damage"))

    def fatal_strike(self, other_hero):
      variation = random.randint(-3, 3)
      actual_damage = self.damage + variation
      damage_dealt = actual_damage - other_hero.defense
      damage_dealt = max(damage_dealt, 1)
      if not other_hero.status['fatal_strike']:
          other_hero.status['fatal_strike'] = True
          other_hero.healing_reduction_effects['fatal_strike'] = 0.7
          for debuff in other_hero.buffs_debuffs_recycle_pool:
              if debuff.name == "Fatal Strike" and debuff.initiator == self:
                  other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                  debuff.duration = 2
                  other_hero.add_debuff(debuff)
                  self.game.display_battle_info(f"{self.name} uses Fatal Strike on {other_hero.name}. The healing they receive will be reduced sharply.")
                  return other_hero.take_damage(damage_dealt)
          
          debuff = Debuff(
              name='Fatal Strike',
              duration=2,
              initiator=self,
              effect=0.8
          )
          other_hero.add_debuff(debuff)
          self.game.display_battle_info(f"{self.name} uses Fatal Strike on {other_hero.name}. The healing they receive will be reduced sharply.")
          return other_hero.take_damage(damage_dealt)
      else:
          self.game.display_battle_info(f"{self.name} uses Fatal Strike on {other_hero.name}.")
      return other_hero.take_damage(damage_dealt)

    def armor_crush(self, other_hero):
        #damage_dealt_stack_0 = self.random_in_range((6, 10))  # Small damage
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.55) 
        damage_dealt = max(damage_dealt, 1) # damage dealt stack 0
        
        if other_hero.status['armor_breaker'] == True:
          if other_hero.armor_breaker_stacks == 1:
              damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.65)
              damage_dealt = max(damage_dealt, 1) # damage dealt stack 1
              defense_before_reducing = other_hero.defense
              defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
              other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.armor_breaker_stacks += 1
              other_hero.armor_breaker_duration = 2  # armor breaker Effect lasts for 2 rounds
              other_hero.status['bleeding_armor_crush'] = True
              other_hero.bleeding_armor_crush_duration = 3
              other_hero.bleeding_armor_crush_continuous_damage = random.randint(8, 12)
              self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}. {other_hero.name} got injured and start bleeding.")
          elif other_hero.armor_breaker_stacks == 2:
              damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.75)
              damage_dealt = max(damage_dealt, 1) # damage dealt stack 2
              defense_before_reducing = other_hero.defense
              defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
              other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.armor_breaker_stacks += 1
              other_hero.armor_breaker_duration = 2  # armor breaker Effect lasts for 2 rounds
              other_hero.status['wound_armor_crush'] = True
              other_hero.wound_armor_crush_duration = 2
              agility_before_reduce = other_hero.agility
              other_hero.agility_reduced_amount_by_wound_armor_crush = int(other_hero.agility * 0.2)
              other_hero.agility -= other_hero.agility_reduced_amount_by_wound_armor_crush
              self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}. This attack causes wound. {other_hero.name}'s agility has reduced from {agility_before_reduce} to {other_hero.agility}.")
          else:
              damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.95)
              damage_dealt = max(damage_dealt, 1) # damage dealt stack >= 3
              other_hero.armor_breaker_duration = 2  # Refresh armor breaker effect
              self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, but {other_hero.name}'s Armor Breaker effect cannot be further stacked. Armor Breaker duration refreshed")
        else:
          other_hero.status['armor_breaker'] = True
          defense_before_reducing = other_hero.defense
          defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
          other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.armor_breaker_stacks += 1
          other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
          self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")
        return other_hero.take_damage(damage_dealt)

    # Battling Strategy_________________________________________________________