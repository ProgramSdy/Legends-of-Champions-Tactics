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

class Death_Knight(Hero):

    faculty = "Death Knight"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "hybrid"

class Death_Knight_Frost(Death_Knight):

    major = "Frost"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Frost Fever", self.frost_fever, target_type = "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Icy Squall", self.icy_squall, target_type = "multi", skill_type= "damage", target_qty= 2))
        self.add_skill(Skill(self, "Winty Strike", self.winty_strike, target_type = "single", skill_type= "damage"))

    def frost_fever(self, other_hero):
        basic_damage = round((self.damage - other_hero.frost_resistance) * 1/3)
        variation = random.randint(-1, 1)
        actual_damage = max(1, basic_damage + variation)
        if other_hero.status['frost_fever'] == False:
            other_hero.status['frost_fever'] = True
            agility_before_reducing = other_hero.agility
            other_hero.agility_reduced_amount_by_frost_fever = round(other_hero.original_agility * 0.30)  # Reduce target's agility by 30%
            other_hero.agility = other_hero.agility - other_hero.agility_reduced_amount_by_frost_fever
            for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Frost Fever" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = 4 
                    other_hero.add_debuff(debuff)
                    other_hero.frost_fever_continuous_damage = round(actual_damage * debuff.effect)
                    self.game.display_battle_info(f"{self.name} casts Frost Fever on {other_hero.name}. {other_hero.name} is feeling cold and their agility is reduced from {agility_before_reducing} to {other_hero.agility}.")
                    return other_hero.take_damage(actual_damage)
            debuff = Debuff(
                name='Frost Fever',
                duration = 4, # frost fever lasts for 3 rounds
                initiator = self,
                effect = 0.8
                )
            other_hero.add_debuff(debuff)
            other_hero.frost_fever_continuous_damage = round(actual_damage * debuff.effect)
            self.game.display_battle_info(f"{self.name} casts Frost Fever on {other_hero.name}. {other_hero.name} is feeling cold and their agility is reduced from {agility_before_reducing} to {other_hero.agility}.")
            return other_hero.take_damage(actual_damage)
        else:
            self.game.display_battle_info(f"{self.name} casts Frost Fever on {other_hero.name}.")
        return other_hero.take_damage(actual_damage)

    def icy_squall(self, other_heros):
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

    def winty_strike(self, other_hero):
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