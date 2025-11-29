import math
import random
from skills import *
from heroes.warrior import Warrior
from heroes.mage_summon import Mage_Summon


ORANGE = "\033[38;5;208m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Summonable:
  def __init__(self, master, duration, summon_unit_race):
    self.master = master
    self.duration = duration
    self.is_summoned = True
    self.summoned_skills = []
    self.summon_unit_race = summon_unit_race

  def decrement_duration(self):
      self.duration -= 1

  def add_summoned_skill(self, skill):
    self.summoned_skills.append(skill)

  def show_summon_info(self):
    summoned_skill_names = [skill.name for skill in self.summoned_skills]
    return (f"Summon Unit: {self.name}\n"
            f"Master: {self.master.name}\n"
            f"Duration: {self.duration} rounds\n"
            f"Summoned Skills: {', '.join(summoned_skill_names)}")

class SummonableWarrior(Warrior, Summonable):
    def __init__(self, sys_init, name, group, master, duration, summon_unit_race, is_player_controlled, major):
        Warrior.__init__(self, sys_init, name, group, is_player_controlled, major)
        Summonable.__init__(self, master, duration, summon_unit_race)

    def show_info(self):
        base_info = super().show_info()
        summon_info = self.show_summon_info()
        return base_info + "\n" + summon_info
    
class SummonableMage(Mage_Summon, Summonable):
    def __init__(self, sys_init, name, group, master, duration, summon_unit_race, is_player_controlled, major):
        Mage_Summon.__init__(self, sys_init, name, group, is_player_controlled, major)
        Summonable.__init__(self, master, duration, summon_unit_race)

    def show_info(self):
        base_info = super().show_info()
        summon_info = self.show_summon_info()
        return base_info + "\n" + summon_info

class SkeletonWarrior(SummonableWarrior):

    major = "Skeleton"

    def __init__(self, sys_init, name, group, master, duration, summon_unit_race, is_player_controlled=False):
        super().__init__(sys_init, name, group, master, duration, summon_unit_race, is_player_controlled, major = self.__class__.major)
        self.probability_corroded_blade = 0.5
        self.probability_devastate = 0.5
        self.preset_target = None
        self.summon_unit_race = summon_unit_race
        self.add_skill(Skill(self, "Devastate", self.devastate, target_type = "single", skill_type= "damage",))
        self.add_skill(Skill(self, "Corroded Blade", self.corroded_blade, target_type = "single", skill_type= "damage"))

    def show_info(self):
        base_info = super().show_info()
        summon_info = self.show_summon_info()
        return base_info + "\n" + summon_info

    def devastate(self, other_hero):
        variation = random.randint(-1, 1)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.55)
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

    def corroded_blade(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.45)
        damage_dealt = max(damage_dealt, 1)
        accuracy = 95  # Bleeding effect has a 95% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy and other_hero.status['bleeding_corroded_blade'] == False:
            other_hero.status['bleeding_corroded_blade'] = True
            other_hero.status['normal'] = False
            other_hero.corroded_blade_debuff_duration = 3
            if damage_dealt > 10:
              other_hero.corroded_blade_continuous_damage = random.randint(9, 12)
            else:
              other_hero.corroded_blade_continuous_damage = random.randint(5, 7)
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Corroded Blade, {other_hero.name} is bleeding.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Corroded Blade")
        # Ensure damage dealt is at least 1
        damage_dealt = max(damage_dealt, 1)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)
    # Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_corroded_blade = 0.5
      self.probability_devastate = 0.5

    def strategy_1(self):
      self.probability_corroded_blade = 0.9
      self.probability_devastate = 0.1

    def strategy_2(self):
      self.probability_corroded_blade = 0.1
      self.probability_devastate = 0.9

    def battle_analysis(self, opponents, allies):

      # Priority targets tackling strategy

      for opponent in opponents:
          if opponent.faculty == 'Mage' or opponent.faculty == 'Rogue' or opponent.faculty == 'Warlock' or opponent.faculty == 'Necromancer':
            if opponent.status['armor_breaker'] == True:
              self.strategy_2()
              return opponent
            if opponent.status['bleeding_corroded_blade'] == False:
              self.strategy_1()
              return opponent
            else:
                self.strategy_2()
            return opponent
          else:
            if opponent.status['armor_breaker'] == True:
              self.strategy_2()
              return opponent
            if opponent.status['bleeding_corroded_blade'] == False:
              self.strategy_1()
              return opponent
            else:
                self.strategy_2()
            return opponent

    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_devastate, self.probability_corroded_blade]
        #available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        #chosen_skill = random.choice(available_skills)
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent

class SkeletonMage(SummonableMage):

    major = "Skeleton"

    def __init__(self, sys_init, name, group, master, duration, summon_unit_race, is_player_controlled=False):
        super().__init__(sys_init, name, group, master, duration, summon_unit_race, is_player_controlled, major = self.__class__.major)
        self.probability_armor_breaker = 0.25
        self.probability_slash = 0.5
        self.preset_target = None
        self.summon_unit_race = summon_unit_race
        self.add_skill(Skill(self, "Arcane Bolt", self.arcane_bolt, target_type = "single", skill_type= "damage",))
        self.add_skill(Skill(self, "Death Bolt", self.death_bolt, target_type = "single", skill_type= "damage"))

    def show_info(self):
        base_info = super().show_info()
        summon_info = self.show_summon_info()
        return base_info + "\n" + summon_info

    def arcane_bolt(self, other_hero):
        variation = random.randint(-1, 1)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.arcane_resistance) * (1/2))
        damage_dealt = max(damage_dealt, 1)
        if other_hero.status['arcane_bolt'] == False:
          arcane_resistance_before_reducing = other_hero.arcane_resistance
          other_hero.arcane_resistance_reduced_amount_by_arcane_bolt = round(other_hero.original_arcane_resistance * 0.20)  # Reduce target's magic resisance by 20%
          other_hero.arcane_resistance = other_hero.arcane_resistance - other_hero.arcane_resistance_reduced_amount_by_arcane_bolt
          other_hero.status['arcane_bolt'] = True
          other_hero.status['normal'] = False
          other_hero.arcane_bolt_duration = 2
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Arcane Bolt, {other_hero.name} is vulnerable towards arcane attack, their arcane resistance is reduced from {arcane_resistance_before_reducing} to {other_hero.arcane_resistance}.")
        else:
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Arcane Bolt.")
        return other_hero.take_damage(damage_dealt)

    def death_bolt(self, other_hero):
        variation = random.randint(-1, 1)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.death_resistance) * (1/2))
        damage_dealt = max(damage_dealt, 0)
        if other_hero.status['death_bolt'] == False:
          death_resistance_before_reducing = other_hero.death_resistance
          other_hero.death_resistance_reduced_amount_by_death_bolt = round(other_hero.original_death_resistance * 0.20)  # Reduce target's magic resisance by 20%
          other_hero.death_resistance = other_hero.death_resistance - other_hero.death_resistance_reduced_amount_by_death_bolt
          other_hero.status['death_bolt'] = True
          other_hero.status['normal'] = False
          other_hero.death_bolt_duration = 2
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with death Bolt, {other_hero.name} is vulnerable towards death attack, their death resistance is reduced from {death_resistance_before_reducing} to {other_hero.death_resistance}.")
        else:
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with death Bolt.")
        return other_hero.take_damage(damage_dealt)
    # Battling Strategy_________________________________________________________

class FleshPuppet(SummonableWarrior):

    major = "FleshPuppet"

    def __init__(self, sys_init, name, group, master, duration, summon_unit_race, is_player_controlled=False):
        super().__init__(sys_init, name, group, master, duration, summon_unit_race, is_player_controlled, major = self.__class__.major)
        self.probability_corroded_blade = 0.5
        self.probability_devastate = 0.5
        self.preset_target = None
        self.summon_unit_race = summon_unit_race
        self.add_skill(Skill(self, "Devastate", self.devastate, target_type = "single", skill_type= "damage",))
        self.add_skill(Skill(self, "Corroded Blade", self.corroded_blade, target_type = "single", skill_type= "damage"))

    def show_info(self):
        base_info = super().show_info()
        summon_info = self.show_summon_info()
        return base_info + "\n" + summon_info

    def devastate(self, other_hero):
        variation = random.randint(-1, 1)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.55)
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

    def corroded_blade(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.45)
        damage_dealt = max(damage_dealt, 1)
        accuracy = 95  # Bleeding effect has a 95% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy and other_hero.status['bleeding_corroded_blade'] == False:
            other_hero.status['bleeding_corroded_blade'] = True
            other_hero.status['normal'] = False
            other_hero.corroded_blade_debuff_duration = 3
            if damage_dealt > 10:
              other_hero.corroded_blade_continuous_damage = random.randint(9, 12)
            else:
              other_hero.corroded_blade_continuous_damage = random.randint(5, 7)
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Corroded Blade, {other_hero.name} is bleeding.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Corroded Blade")
        # Ensure damage dealt is at least 1
        damage_dealt = max(damage_dealt, 1)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)
    # Battling Strategy_________________________________________________________

class VoidRambler(SummonableWarrior):

    major = "Void_Rambler"

    def __init__(self, sys_init, name, group, master, duration, summon_unit_race, is_player_controlled=False):
        super().__init__(sys_init, name, group, master, duration, summon_unit_race, is_player_controlled, major = self.__class__.major)
        self.probability_void_punch = 0.5
        self.probability_void_connection = 0.5
        self.preset_target = None
        self.summon_unit_race = summon_unit_race
        self.add_skill(Skill(self, "Void Punch", self.void_punch, target_type = "single", skill_type= "damage",))
        self.add_skill(Skill(self, "Void Connection", self.void_connection, target_type = "single", skill_type= "buffs"))

    def show_info(self):
        base_info = super().show_info()
        summon_info = self.show_summon_info()
        return base_info + "\n" + summon_info

    def void_punch(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.shadow_resistance)/2)
        damage_dealt = max(damage_dealt, 0)
        self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Void Punch.")
        return other_hero.take_damage(damage_dealt)

    def void_connection(self, other_hero):
        if other_hero.status['void_connection'] == False:
            other_hero.status['void_connection'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Void Connection" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 3   # Effect lasts for 2 rounds
                    buff.effect = 0.5
                    other_hero.add_buff(buff)
                    for skill in self.skills:
                      if skill.name == "Void Connection":
                        skill.if_cooldown = True
                        skill.cooldown = 2
                    return f"{self.name} casts Void Connection on {other_hero.name}. {self.name} shares the damage from {other_hero.name}"

            buff = Buff(
                name='Void Connection',
                duration = 3,
                initiator = self,
                effect = 0.5
            )
            other_hero.add_buff(buff)
            for skill in self.skills:
              if skill.name == "Void Connection":
                skill.if_cooldown = True
                skill.cooldown = 2
            return f"{self.name} casts Void Connection on {other_hero.name}. {self.name} shares the damage from {other_hero.name}"
        else:
            return f"{self.name} tries to cast Void Connection on {other_hero.name}. But {other_hero.name} has already been connected"

 # Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_void_punch = 1
      self.probability_void_connection = 0

    def strategy_1(self):
      self.probability_void_punch = 0
      self.probability_void_connection = 1

    def battle_analysis(self, opponents, allies):
      targets = []
      for skill in self.skills:
        if skill.name == "Void Connection":
          if self.master.hp <= self.master.hp_max * 0.99 and skill.if_cooldown == False:
            self.strategy_1()
            return self.master

      for opponent in opponents:
        if opponent.faculty == 'Warrior' or opponent.faculty == 'Rogue':
          targets.append(opponent)
      if len(targets) > 0:
          opponent = random.choice(targets)
          self.strategy_0()
          return opponent
      opponent = random.choice(opponents)
      self.strategy_0()
      return opponent


    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_void_punch, self.probability_void_connection]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent
    
class WaterElemental(SummonableWarrior):

    major = "Water_Elemental"

    def __init__(self, sys_init, name, group, master, duration, summon_unit_race, is_player_controlled=False):
        super().__init__(sys_init, name, group, master, duration, summon_unit_race, is_player_controlled, major = self.__class__.major)
        self.probability_void_punch = 0.5
        self.probability_void_connection = 0.5
        self.preset_target = None
        self.summon_unit_race = summon_unit_race
        self.add_skill(Skill(self, "Tide Slam", self.tide_slam, target_type = "single", skill_type= "damage", damage_nature = "magical", damage_type = "water"))
        self.add_skill(Skill(self, "Crushing Wave", self.crushing_wave, target_type = "multi", skill_type= "damage", target_qty= 2, damage_nature = "magical", damage_type = "water"))

    def show_info(self):
        base_info = super().show_info()
        summon_info = self.show_summon_info()
        return base_info + "\n" + summon_info

    def tide_slam(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.nature_resistance))
        damage_dealt = max(damage_dealt, 0)
        self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Tide Slam.")
        return other_hero.take_damage(damage_dealt)
    
    def crushing_wave(self, other_heros): # Cause damage to self.
        if not isinstance(other_heros, list):
          other_heros = [other_heros]
        results = []
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        self_damage = math.ceil(self.hp_max * 0.2) + variation
        selected_opponents = other_heros
        for skill in self.skills:
          if skill.name == "Crushing Wave":
            skill.if_cooldown = True
            skill.cooldown = 2
        for opponent in selected_opponents:
            damage_dealt = math.ceil((actual_damage - opponent.nature_resistance) * 2/3)
            self.game.display_battle_info(f"{self.name} casts Crushing Wave at {opponent.name}.")
            results.append(opponent.take_damage(damage_dealt))
        self.game.display_battle_info(f"{self.name} will loose Hp for casting Crushing Wave")
        results.append(self.take_damage(self_damage))
        return "\n".join(results)
    
 # Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_tide_slam = 1
      self.probability_crushing_wave = 0

    def strategy_1(self):
      self.probability_tide_slam = 0
      self.probability_crushing_wave = 1

    def battle_analysis(self, opponents, allies):
      for skill in self.skills:
        if skill.name == "Crushing Wave":
          if skill.if_cooldown == False:
            self.strategy_1()
            chosen_opponent = random.sample(opponents, skill.target_qty) if len(opponents) > skill.target_qty else opponents
            return chosen_opponent
      opponent = random.choice(opponents)
      #self.strategy_0()
      return opponent
    
    def ai_choose_skill(self, opponents, allies):
      self.strategy_0()
      self.preset_target = self.battle_analysis(opponents, allies)
      skill_weights = [self.probability_tide_slam, self.probability_crushing_wave]
      chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
      return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
      chosen_opponent = self.preset_target
      return chosen_opponent