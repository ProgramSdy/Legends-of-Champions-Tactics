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
        for skill in self.skills:
            if skill.name == "Icy Squall":
              skill.if_cooldown = True
              skill.cooldown = 2
        variation = random.randint(-2, 2)
        selected_opponents = other_heros
        for opponent in selected_opponents:
            basic_damage = round((self.damage - opponent.frost_resistance) * 2/3)
            actual_damage = max(1, basic_damage + variation)
            if opponent.status['frost_fever'] == True:
                if opponent.status['icy_squall'] == False:
                    opponent.status['icy_squall'] = True
                    frost_resistance_before_reducing = opponent.frost_resistance
                    opponent.frost_resistance_reduced_amount_by_icy_squall = round(opponent.original_frost_resistance * 0.20)  # Reduce target's frost resistance by 20%
                    opponent.frost_resistance = opponent.frost_resistance - opponent.frost_resistance_reduced_amount_by_icy_squall
                    for debuff in opponent.buffs_debuffs_recycle_pool:
                        if debuff.name == "Icy Squall" and debuff.initiator == self:
                            opponent.buffs_debuffs_recycle_pool.remove(debuff)
                            debuff.duration = 3 
                            opponent.add_debuff(debuff)
                            self.game.display_battle_info(f"{self.name} casts Icy Squall at {opponent.name}. Due to Frost Fever, {opponent.name}'s frost resistance has been reduced from {frost_resistance_before_reducing} to {opponent.frost_resistance}. ")
                            results.append(opponent.take_damage(actual_damage))
                            break
                    else:
                        debuff = Debuff(
                            name='Icy Squall',
                            duration = 3, # icy squall lasts for 2 rounds
                            initiator = self,
                            #effect = 0.8
                            )
                        opponent.add_debuff(debuff)
                        self.game.display_battle_info(f"{self.name} casts Icy Squall at {opponent.name}. Due to Frost Fever, {opponent.name}'s frost resistance has been reduced from {frost_resistance_before_reducing} to {opponent.frost_resistance}. ")
                        results.append(opponent.take_damage(actual_damage))
                else:
                    self.game.display_battle_info(f"{self.name} casts Icy Squall at {opponent.name}.")
                    results.append(opponent.take_damage(actual_damage))
            else:
                self.game.display_battle_info(f"{self.name} casts Icy Squall at {opponent.name}.")
                results.append(opponent.take_damage(actual_damage))
        return "\n".join(results)

    def winty_strike(self, other_hero):
        variation = random.randint(-2, 2)
        basic_damage_weapon = round((self.damage - other_hero.defense) * 1/2)
        basic_damage_frost = round((self.damage - other_hero.frost_resistance) * 1/2)
        basic_damage = basic_damage_weapon + basic_damage_frost
        actual_damage = max(1, basic_damage + variation)
        if other_hero.status['frost_fever'] == True:
          extra_frost_damage = random.randint(3, 5)
          actual_damage += extra_frost_damage
          self.game.display_battle_info(f"{self.name} uses Winty Strike on {other_hero.name}, due to {other_hero.name} is infected by Frost Fever, this attack causes extra {extra_frost_damage} frost damage.")
        else:
          self.game.display_battle_info(f"{self.name} uses Winty Strike on {other_hero.name}.")
        return other_hero.take_damage(actual_damage)