import math
import random
from heroes import *
from skills import *
from .summon_unit import WaterElemental

ORANGE = "\033[38;5;208m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Mage(Hero):

    faculty = "Mage"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "elemental"

class Mage_Comprehensiveness(Mage):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Fireball", self.fireball, target_type = "single", skill_type= "damage", damage_nature = "magical", damage_type = "fire"))
        self.add_skill(Skill(self, "Arcane Missiles", self.arcane_missiles, target_type = "multi", skill_type= "damage", target_qty= 2, damage_nature = "magical", damage_type = "arcane"))
        self.add_skill(Skill(self, "Frost Bolt", self.frost_bolt, target_type = "single", skill_type= "damage", damage_nature = "magical", damage_type = "frost"))

    def fireball(self, other_hero):
        variation = random.randint(-5, 5)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.fire_resistance
        damage_dealt = max(damage_dealt, 0)
        self.game.display_battle_info(f"{self.name} casts Fireball at {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def arcane_missiles(self, other_heros):
        if not isinstance(other_heros, list):
          other_heros = [other_heros]
        results = []
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        selected_opponents = other_heros
        for opponent in selected_opponents:
            damage_dealt = math.ceil((actual_damage - opponent.arcane_resistance) * 2/3)
            self.game.display_battle_info(f"{self.name} casts Arcane Missiles at {opponent.name}.")
            results.append(opponent.take_damage(damage_dealt))
        return "\n".join(results)

    def frost_bolt(self, other_hero):
        if other_hero.status['cold'] == False:
          agility_before_reducing = other_hero.agility
          other_hero.agility_reduced_amount_by_frost_bolt = math.ceil(other_hero.original_agility * 0.70)  # Reduce target's agility by 70%
          other_hero.agility = other_hero.agility - other_hero.agility_reduced_amount_by_frost_bolt
          other_hero.status['cold'] = True
          other_hero.status['normal'] = False
          other_hero.cold_duration = 2
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Frost Bolt, {other_hero.name} is feeling cold and their agility is reduced from {agility_before_reducing} to {other_hero.agility}.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Frost Bolt")
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.frost_resistance) * 4/5)
        damage_dealt = max(damage_dealt, 0)
        return other_hero.take_damage(damage_dealt)

class Mage_Water(Mage):

    major = "Water"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Summon Water Elemental", self.summon_water_elemental, target_type="single", skill_type="summon", target_qty= 0, damage_nature = "magical", damage_type = "water"))
        self.add_skill(Skill(self, "Water Arrow", self.water_arrow, target_type = "single", skill_type= "damage_healing", damage_nature = "magical", damage_type = "water"))
        #self.add_skill(Skill(self, "Frost Bolt", self.frost_bolt, target_type = "single", skill_type= "damage"))

    def summon_water_elemental(self):
        unit_name = f"{self.name}'s Water Elemental"
        unit_group = self.group
        unit_duration = 3  # The summoning unit will last for 3 rounds
        unit_race = 'element'
        waterelemental = WaterElemental(self.sys_init, unit_name, unit_group, self, unit_duration, unit_race, is_player_controlled=False)
        waterelemental.take_game_instance(self.game)
        self.summoned_unit = waterelemental
        for hero in self.game.player_heroes:
          if self.name == hero.name:
            self.game.player_heroes.append(waterelemental)
            self.game.heroes.append(waterelemental)
            self.game.unactioned_sorted_heroes.append(waterelemental)
            break
        else:
          self.game.opponent_heroes.append(waterelemental)
          self.game.heroes.append(waterelemental)
          self.game.unactioned_sorted_heroes.append(waterelemental)
        for skill in self.skills:
          if skill.name == "Summon Water Elemental":
            skill.if_cooldown = True
            skill.cooldown = 3
        return f"{self.name} summons a Water Elemental in the battle field."
    
    def water_arrow(self, other_hero, target_type):
      healing_amount_base = 15
      duration_sustainable = 1
      if target_type == "ally": # boost effect
        variation = random.randint(-2, 2)
        other_hero.duration += duration_sustainable

        if other_hero.status['water_arrow'] == False:
            other_hero.status['water_arrow'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Water Arrow" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 3   # Effect lasts for 2 rounds
                    other_hero.water_arrow_stacks += 1
                    other_hero.add_buff(buff)
                    damage_before_increasing = other_hero.damage # damage increase
                    damage_increased_amount_by_water_arrow_single = round(other_hero.original_damage * buff.effect)  # Increase hero's damage by 10%
                    other_hero.damage_increased_amount_by_water_arrow = other_hero.damage_increased_amount_by_water_arrow + damage_increased_amount_by_water_arrow_single
                    other_hero.damage = other_hero.damage + other_hero.damage_increased_amount_by_water_arrow
                    agility_before_increasing = other_hero.agility
                    agility_increased_amount_by_water_arrow_single = round(other_hero.original_agility * buff.effect * 10)  # Increase hero's agility by 100%
                    other_hero.agility_increased_amount_by_water_arrow = other_hero.agility_increased_amount_by_water_arrow + agility_increased_amount_by_water_arrow_single
                    other_hero.agility = other_hero.agility + agility_increased_amount_by_water_arrow_single
                    self.game.display_battle_info(f"{self.name} uses Water Arrow on {other_hero.name}, {other_hero.name} has received energy from water. {other_hero.name}'s damage and agility has increased, {other_hero.name} will stay one more round in the battle field.")
                    return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}."

            buff = Buff(
                name='Water Arrow',
                duration = 3,
                initiator = self,
                effect = 0.10
            )
            other_hero.water_arrow_stacks += 1
            other_hero.add_buff(buff)
            damage_before_increasing = other_hero.damage # damage increase
            damage_increased_amount_by_water_arrow_single = round(other_hero.original_damage * buff.effect)  # Increase hero's damage by 10%
            other_hero.damage_increased_amount_by_water_arrow = other_hero.damage_increased_amount_by_water_arrow + damage_increased_amount_by_water_arrow_single
            other_hero.damage = other_hero.damage + other_hero.damage_increased_amount_by_water_arrow
            agility_before_increasing = other_hero.agility
            agility_increased_amount_by_water_arrow_single = round(other_hero.original_agility * buff.effect * 10)  # Increase hero's agility by 100%
            other_hero.agility_increased_amount_by_water_arrow = other_hero.agility_increased_amount_by_water_arrow + agility_increased_amount_by_water_arrow_single
            other_hero.agility = other_hero.agility + agility_increased_amount_by_water_arrow_single
            self.game.display_battle_info(f"{self.name} uses Water Arrow on {other_hero.name}, {other_hero.name} has received energy from water. {other_hero.name}'s damage and agility has increased, {other_hero.name} will stay one more round in the battle field.")
            return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}."
        elif other_hero.status['water_arrow'] == True and other_hero.water_arrow_stacks == 1:
            other_hero.water_arrow_stacks += 1
            damage_before_increasing = other_hero.damage # damage increase
            for buff in other_hero.buffs:
                if buff.name == "Water Arrow" and buff.initiator == self:
                  damage_increased_amount_by_water_arrow_single = round(other_hero.original_damage * buff.effect)  # Increase hero's damage by 10%
                  other_hero.damage_increased_amount_by_water_arrow = other_hero.damage_increased_amount_by_water_arrow + damage_increased_amount_by_water_arrow_single
                  other_hero.damage = other_hero.damage + other_hero.damage_increased_amount_by_water_arrow
                  agility_before_increasing = other_hero.agility
                  agility_increased_amount_by_water_arrow_single = round(other_hero.original_agility * buff.effect * 10)  # Increase hero's agility by 100%
                  other_hero.agility_increased_amount_by_water_arrow = other_hero.agility_increased_amount_by_water_arrow + agility_increased_amount_by_water_arrow_single
                  other_hero.agility = other_hero.agility + other_hero.agility_increased_amount_by_water_arrow
                  self.game.display_battle_info(f"{self.name} uses Water Arrow on {other_hero.name} again, {other_hero.name} has received energy from water. {other_hero.name}'s damage and agility has increased, {other_hero.name} will stay one more round in the battle field.")
                  return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}."
        else:
           return f"{self.name} uses Water Arrow on {other_hero.name} again, but {other_hero.name} cannot be futher strenthened, {other_hero.name} will stay one more round in the battle field."

      elif target_type =="opponent": # damage effect
        variation = random.randint(-2, -2)
        actual_damage = healing_amount_base + variation
        damage_dealt = actual_damage #damage discard opponent's defense
        damage_dealt = max(damage_dealt, 0) # Ensure damage dealt is at least 0
        self.game.display_battle_info(f"{self.name} casts Water Arrow at {other_hero.name}.")
        return f"{other_hero.take_damage(damage_dealt)}"

    def frost_bolt(self, other_hero):
        if other_hero.status['cold'] == False:
          agility_before_reducing = other_hero.agility
          other_hero.agility_reduced_amount_by_frost_bolt = math.ceil(other_hero.original_agility * 0.70)  # Reduce target's agility by 70%
          other_hero.agility = other_hero.agility - other_hero.agility_reduced_amount_by_frost_bolt
          other_hero.status['cold'] = True
          other_hero.status['normal'] = False
          other_hero.cold_duration = 2
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Frost Bolt, {other_hero.name} is feeling cold and their agility is reduced from {agility_before_reducing} to {other_hero.agility}.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Frost Bolt")
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.frost_resistance) * 4/5)
        damage_dealt = max(damage_dealt, 0)
        return other_hero.take_damage(damage_dealt)