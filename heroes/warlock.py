import math
import random
from heroes import *
from skills import *
from .summon_unit import VoidRambler

ORANGE = "\033[38;5;208m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Warlock(Hero):

    faculty = "Warlock"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "fire_shadow"

class Warlock_Comprehensiveness(Warlock):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.sys_init = sys_init
        self.add_skill(Skill(self, "Shadow Bolt", self.shadow_bolt, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Corrosion", self.corrosion, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Summon Void Rambler", self.summon_void_rambler, target_type="single", skill_type="summon", target_qty= 0))

    def shadow_bolt(self, other_hero):
        #variation = random.randint(-3, 3)
        variation = 0
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.shadow_resistance) * (4/5))
        damage_dealt = max(damage_dealt, 0)
        if other_hero.status['shadow_bolt'] == False:
          shadow_resistance_before_reducing = other_hero.shadow_resistance
          other_hero.shadow_resistance_reduced_amount_by_shadow_bolt = round(other_hero.original_shadow_resistance * 0.20)  # Reduce target's magic resisance by 20%
          other_hero.shadow_resistance = other_hero.shadow_resistance - other_hero.shadow_resistance_reduced_amount_by_shadow_bolt
          other_hero.status['shadow_bolt'] = True
          other_hero.status['normal'] = False
          other_hero.shadow_bolt_duration = 2
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shadow Bolt, {other_hero.name} is vulnerable towards shadow attack, their shadow resistance is reduced from {shadow_resistance_before_reducing} to {other_hero.shadow_resistance}.")
        else:
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shadow Bolt")
        return other_hero.take_damage(damage_dealt)

    def corrosion(self, other_hero):
        variation = random.randint(-2, 2)
        variation = 0
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.poison_resistance)*(1/2))
        damage_dealt = max(damage_dealt, 0)
        if damage_dealt > 0:
          other_hero.corrosion_continuous_damage = round((actual_damage - other_hero.poison_resistance)*(1/3))
        else:
          other_hero.corrosion_continuous_damage = random.randint(3, 8)
        if other_hero.status['corrosion'] == False:
          other_hero.status['corrosion'] = True
          other_hero.corrosion_duration = 4  # Effect lasts for 3 rounds
          defense_before_reducing = other_hero.defense
          other_hero.defense_reduced_amount_by_corrosion = round(other_hero.original_defense * 0.20)  # Reduce target's defense by 20%
          #print(f"{RED} {other_hero.name}'s defense_reduced_amount_by_corrosion is {other_hero.defense_reduced_amount_by_corrosion}{RESET}")
          other_hero.defense = other_hero.defense - other_hero.defense_reduced_amount_by_corrosion
          self.game.display_battle_info(f"{self.name} casts Corrosion on {other_hero.name}. {other_hero.name}'s armor has corroded, their defense is reduced from {defense_before_reducing} to {other_hero.defense}.")
        else:
          self.game.display_battle_info(f"{self.name} casts Corrosion on {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)


    def summon_void_rambler(self):
        unit_name = f"{self.name}'s Void Rambler"
        unit_group = self.group
        unit_duration = 4  # The skeleton will last for 4 rounds
        unit_race = 'devil'
        voidrambler = VoidRambler(self.sys_init, unit_name, unit_group, self, unit_duration, unit_race, is_player_controlled=False)
        voidrambler.take_game_instance(self.game)
        self.summoned_unit = voidrambler
        for hero in self.game.player_heroes:
          if self.name == hero.name:
            self.game.player_heroes.append(voidrambler)
            self.game.heroes.append(voidrambler)
            break
        else:
          self.game.opponent_heroes.append(voidrambler)
          self.game.heroes.append(voidrambler)
        for skill in self.skills:
          if skill.name == "Summon Void Rambler":
            skill.if_cooldown = True
            skill.cooldown = 3
        return f"{self.name} uses Summon Void Rambler and summons a Void Rambler in the battle field."

class Warlock_Affliction(Warlock):

    major = "Affliction"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major = self.__class__.major)
        self.add_skill(Skill(self, "Curse of Agony", self.curse_of_agony, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Soul Siphon", self.soul_siphon, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Curse of Fear", self.curse_of_fear, "single", skill_type= "damage"))

    def curse_of_agony(self, other_hero):
        initial_damage = random.randint(3, 8)
        basic_damage = self.damage - other_hero.shadow_resistance
        if other_hero.status['curse_of_agony'] == False:
            other_hero.status['curse_of_agony'] = True
            other_hero.curse_of_agony_duration = 5  # Effect lasts for 4 rounds
            other_hero.curse_of_agony_continuous_damage = [round(basic_damage * 1/4), round(basic_damage * 2/4), round(basic_damage * 3/4), basic_damage]
            self.game.display_battle_info(f"{self.name} casts Curse of Agony on {other_hero.name}.")
        else:
          if other_hero.curse_of_agony_duration > 1:
            sublist = other_hero.curse_of_agony_continuous_damage[abs(other_hero.curse_of_agony_duration-5):]
            self.definite_shuffle(sublist)
            other_hero.curse_of_agony_continuous_damage[abs(other_hero.curse_of_agony_duration-5):] = sublist
            self.game.display_battle_info(f"{self.name} casts Curse of Agony on {other_hero.name} again. {other_hero.name}'s Agony is unpredicted")
          else:
            self.game.display_battle_info(f"{self.name} casts Curse of Agony on {other_hero.name} again.")
        return other_hero.take_damage(initial_damage)

    def soul_siphon(self, other_hero):
        initial_damage = random.randint(9, 15)
        basic_damage = self.damage - other_hero.death_resistance
        variation = random.randint(-1, 1)
        actual_damage = max(1, basic_damage + variation)
        if other_hero.status['soul_siphon'] == False:
            other_hero.status['soul_siphon'] = True
            other_hero.soul_siphon_healing_amount = round(initial_damage * 3/4)
            for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Soul Siphon" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = 3
                    other_hero.add_debuff(debuff)
                    other_hero.soul_siphon_continuous_damage = round(actual_damage * debuff.effect)
                    self.game.display_battle_info(f"{self.name} casts Soul Siphon on {other_hero.name}. {other_hero.name}'s soul hurts")
                    return other_hero.take_damage(initial_damage)
            debuff = Debuff(
                name='Soul Siphon',
                duration = 3, # fear lasts for 1-3 rounds
                initiator = self,
                effect = 0.4
            )
            other_hero.add_debuff(debuff)
            other_hero.soul_siphon_continuous_damage = round(actual_damage * debuff.effect)
            self.game.display_battle_info(f"{self.name} casts Soul Siphon on {other_hero.name}. {other_hero.name}'s soul hurts")
            return other_hero.take_damage(initial_damage)
        else:
            self.game.display_battle_info(f"{self.name} casts Soul Siphon on {other_hero.name}.")
        return other_hero.take_damage(initial_damage)

    def curse_of_fear(self, other_hero):
        #accuracy = 70  # Shield Bash has a 70% chance to succeed
        #roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
          #if roll <= accuracy:
        roll = random.randint(1,3)
        if other_hero.status['fear'] == False:
          if other_hero.status['magic_casting'] == True:
            result = self.interrupt_magic_casting(other_hero)
            other_hero.status['fear'] = True
            for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Curse of Fear" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = roll   # fear lasts for 1-3 rounds
                    other_hero.add_debuff(debuff)
                    for skill in self.skills:
                      if skill.name == "Curse of Fear":
                        skill.is_available = False
                        skill.if_cooldown = True
                        skill.cooldown = 3
                    return f"{self.name} casts Curse of Fear on {other_hero.name}, {other_hero.name} feels a deep sense of fear. {result}"
            debuff = Debuff(
                name='Curse of Fear',
                duration = roll, # fear lasts for 1-3 rounds
                initiator = self,
                effect = 0
            )
            other_hero.add_debuff(debuff)
            for skill in self.skills:
                      if skill.name == "Curse of Fear":
                        skill.is_available = False
                        skill.if_cooldown = True
                        skill.cooldown = 3
            return f"{self.name} casts Curse of Fear on {other_hero.name}, {other_hero.name} feels a deep sense of fear. {result}"
          else:
            other_hero.status['fear'] = True
            for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Curse of Fear" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = roll   # fear lasts for 1-3 rounds
                    other_hero.add_debuff(debuff)
                    for skill in self.skills:
                      if skill.name == "Curse of Fear":
                        skill.is_available = False
                        skill.if_cooldown = True
                        skill.cooldown = 3
                    return f"{self.name} casts Curse of Fear on {other_hero.name}, {other_hero.name} feels a deep sense of fear."
            debuff = Debuff(
                name='Curse of Fear',
                duration = roll, # fear lasts for 1-3 rounds
                initiator = self,
                effect = 0
            )
            other_hero.add_debuff(debuff)
            for skill in self.skills:
              if skill.name == "Curse of Fear":
                skill.is_available = False
                skill.if_cooldown = True
                skill.cooldown = 3
            return f"{self.name} casts Curse of Fear on {other_hero.name}, {other_hero.name} feels a deep sense of fear"
        else:
          return f"{self.name} tries to cast Curse of Fear on {other_hero.name}. But {other_hero.name} is already in fear."

class Warlock_Destruction(Warlock):

    major = "Destruction"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major = self.__class__.major)
        self.add_skill(Skill(self, "Shadow Bolt", self.shadow_bolt, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Immolate", self.immolate, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Rain of Fire", self.rain_of_fire, "multi", skill_type= "damage", target_qty=3, is_instant_skill = False))
        self.immolate_accumulate_damage = 0
        self.hell_flame_threshold = round(self.hp_max * 0.4)

    def shadow_bolt(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.shadow_resistance) * (4/5))
        damage_dealt = max(damage_dealt, 0)
        if other_hero.status['shadow_bolt'] == False:
          shadow_resistance_before_reducing = other_hero.shadow_resistance
          other_hero.shadow_resistance_reduced_amount_by_shadow_bolt = round(other_hero.original_shadow_resistance * 0.20)  # Reduce target's magic resisance by 20%
          other_hero.shadow_resistance = other_hero.shadow_resistance - other_hero.shadow_resistance_reduced_amount_by_shadow_bolt
          other_hero.status['shadow_bolt'] = True
          other_hero.status['normal'] = False
          other_hero.shadow_bolt_duration = 2
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shadow Bolt, {other_hero.name} is vulnerable towards shadow attack, their shadow resistance is reduced from {shadow_resistance_before_reducing} to {other_hero.shadow_resistance}.")
        else:
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shadow Bolt")
        return other_hero.take_damage(damage_dealt)

    def immolate(self, other_hero):
        variation = random.randint(-2, 2)
        variation = 0
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.fire_resistance)*(1/2))
        damage_dealt = max(damage_dealt, 0)
        self.immolate_accumulate_damage += damage_dealt
        if damage_dealt > 0:
          other_hero.immolate_continuous_damage = round((actual_damage - other_hero.fire_resistance)*(1/3))
        else:
          other_hero.immolate_continuous_damage = random.randint(3, 8)
        if other_hero.status['immolate'] == False:
          other_hero.status['immolate'] = True
          for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Immolate" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = 3   # Effect lasts for 2 rounds
                    other_hero.add_debuff(debuff)
                    damage_before_reducing = other_hero.damage
                    other_hero.damage_reduced_amount_by_immolate = round(other_hero.original_damage * debuff.effect)  # Reduce target's damage by 17%
                    other_hero.damage = other_hero.damage - other_hero.damage_reduced_amount_by_immolate
                    self.game.display_battle_info(f"{self.name} casts Immolate on {other_hero.name}. {other_hero.name} is burned and their damage is reduced from {damage_before_reducing} to {other_hero.damage}.")
                    if self.immolate_accumulate_damage > self.hell_flame_threshold:
                      self.status['hell_flame'] = True
                      self.immolate_accumulate_damage = 0
                      self.game.display_battle_info(f"{YELLOW}{self.name} gains the power from hell flame through Immolate. Their next Rain of Fire becomes instant{RESET}")
                      return other_hero.take_damage(damage_dealt)
                    else:
                      return other_hero.take_damage(damage_dealt)
          debuff = Debuff(
                name='Immolate',
                duration = 3, # Effect lasts for 1-3 rounds
                initiator = self,
                effect = 0.17
            )
          other_hero.add_debuff(debuff)
          damage_before_reducing = other_hero.damage
          other_hero.damage_reduced_amount_by_immolate = round(other_hero.original_damage * debuff.effect)  # Reduce target's damage by 17%
          other_hero.damage = other_hero.damage - other_hero.damage_reduced_amount_by_immolate
          self.game.display_battle_info(f"{self.name} casts Immolate on {other_hero.name}. {other_hero.name} is burned and their damage is reduced from {damage_before_reducing} to {other_hero.damage}.")
          if self.immolate_accumulate_damage > self.hell_flame_threshold:
            self.status['hell_flame'] = True
            self.immolate_accumulate_damage = 0
            self.game.display_battle_info(f"{YELLOW}{self.name} gains the power from hell flame through Immolate. Their next Rain of Fire becomes instant{RESET}")
            return other_hero.take_damage(damage_dealt)
          else:
            return other_hero.take_damage(damage_dealt)
        else:
          self.game.display_battle_info(f"{self.name} casts Immolate on {other_hero.name}.")
          if self.immolate_accumulate_damage > self.hell_flame_threshold:
            self.status['hell_flame'] = True
            self.immolate_accumulate_damage = 0
            self.game.display_battle_info(f"{YELLOW}{self.name} gains the power from hell flame through Immolate. Their next Rain of Fire becomes instant{RESET}")
            return other_hero.take_damage(damage_dealt)
          else:
            return other_hero.take_damage(damage_dealt)

    def rain_of_fire(self, other_heroes):
        if not isinstance(other_heroes, list):
          other_heroes = [other_heroes]

        # If in Hell Flame status, cast instantly
        if self.status['hell_flame']:
          if self.status['magic_casting'] == False:
            self.game.display_battle_info(f"{self.name} receives power from hell flame and casts Rain of Fire instantly!")
            self.status['hell_flame'] = False  # Reset the status after use
            results = []
            variation = random.randint(-2, 2)
            actual_damage = self.damage + variation
            selected_opponents = other_heroes
            for opponent in selected_opponents:
              if opponent.hp > 0:
                damage_dealt = round((actual_damage - opponent.fire_resistance) * 2/3)
                self.game.display_battle_info(f"{self.name} casts Rain of Fire at {opponent.name}.")
                results.append(opponent.take_damage(damage_dealt))
            return "\n".join(results)
          elif self.status['magic_casting'] == True:
            self.status['magic_casting'] = False
            self.game.display_battle_info(f"From hell flame, {self.name} casts a much powerful Rain of Fire!")
            self.status['hell_flame'] = False  # Reset the status after use
            results = []
            variation = random.randint(-2, 2)
            actual_damage = self.damage + variation
            selected_opponents = other_heroes
            for opponent in selected_opponents:
              if opponent.hp > 0:
                damage_dealt = actual_damage - opponent.fire_resistance
                self.game.display_battle_info(f"{self.name} casts Rain of Fire at {opponent.name}.")
                results.append(opponent.take_damage(damage_dealt))
            return "\n".join(results)

        if self.status['magic_casting'] == False:
          self.status['magic_casting'] = True
          self.game.display_battle_info(f"{self.name} is casting Rain of Fire.")
          self.magic_casting_duration = 1
          for skill in self.skills:
            if skill.name == "Rain of Fire":
              return self.magic_casting(skill, other_heroes)

        elif self.status['magic_casting'] == True:
          self.status['magic_casting'] = False
          results = []
          variation = random.randint(-2, 2)
          actual_damage = self.damage + variation
          selected_opponents = other_heroes
          for opponent in selected_opponents:
            if opponent.hp > 0:
              damage_dealt = round((actual_damage - opponent.fire_resistance) * 2/3)
              self.game.display_battle_info(f"{self.name} casts Rain of Fire at {opponent.name}.")
              results.append(opponent.take_damage(damage_dealt))
          return "\n".join(results)