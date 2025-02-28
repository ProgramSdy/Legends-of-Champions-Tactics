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
        basic_damage = round((self.damage - other_hero.frost_resistance) * 1/5)
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
            debuff.type = ['Disease']
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
                            effect = 0.8
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
    

class Death_Knight_Plague(Death_Knight):

    major = "Plague"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Necrotic Decay", self.necrotic_decay, target_type = "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Plague Strike", self.plague_strike, target_type = "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Pestilence", self.pestilence, target_type = "single", skill_type= "damage"))

    def necrotic_decay(self, other_hero):
        basic_damage = round((self.damage - other_hero.death_resistance) * 1/5)
        variation = random.randint(-1, 1)
        actual_damage = max(1, basic_damage + variation)
        
        if not other_hero.status['necrotic_decay']:
            other_hero.status['necrotic_decay'] = True
            other_hero.healing_reduction_effects['necrotic_decay'] = 0.3 
            for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Necrotic Decay" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = 4
                    other_hero.add_debuff(debuff)
                    other_hero.necrotic_decay_continuous_damage = round(actual_damage * debuff.effect)
                    self.game.display_battle_info(f"{self.name} casts Necrotic Decay on {other_hero.name}. Their healing is reduced and they take continuous damage.")
                    return other_hero.take_damage(actual_damage)
            
            debuff = Debuff(
                name='Necrotic Decay',
                duration=4,
                initiator=self,
                effect=0.8
            )
            debuff.type = ['Disease']
            other_hero.add_debuff(debuff)
            other_hero.necrotic_decay_continuous_damage = round(actual_damage * debuff.effect)
            self.game.display_battle_info(f"{self.name} casts Necrotic Decay on {other_hero.name}. Their healing is reduced and they take continuous damage.")
            return other_hero.take_damage(actual_damage)
        else:
            self.game.display_battle_info(f"{self.name} casts Necrotic Decay on {other_hero.name}.")
        return other_hero.take_damage(actual_damage)
    
    def plague_strike(self, other_hero):
        basic_damage = round((self.damage - other_hero.defense) * 1/2)
        variation = random.randint(-1, 1)
        poison_bonus = 0
        if other_hero.status['poisoned_dagger'] or other_hero.status['virulent_infection']:
            poison_bonus = round((self.damage - other_hero.poison_resistance) * 1/2)  # Extra poison damage if already infected
        total_damage = basic_damage + poison_bonus
        actual_damage = max(1, total_damage + variation)

        # Apply Virulent Infection if not already present
        if not other_hero.status['virulent_infection']:
            other_hero.status['virulent_infection'] = True
            for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Virulent Infection" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = 4  # Reset duration
                    other_hero.add_debuff(debuff)
                    other_hero.virulent_infection_continuous_damage = round((self.damage - other_hero.poison_resistance) * debuff.effect)
                    break
            # Apply new debuff
            else:
                debuff = Debuff(
                    name='Virulent Infection',
                    duration=4,
                    initiator=self,
                    effect=0.25  
                )
                debuff.type = ['Disease']
                other_hero.add_debuff(debuff)
                other_hero.virulent_infection_continuous_damage = round((self.damage - other_hero.poison_resistance) * debuff.effect)
            if poison_bonus == 0:
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Plague Strike, infecting them with Virulent Infection!")
                return other_hero.take_damage(actual_damage)
            elif poison_bonus > 0:
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Plague Strike, infecting them with Virulent Infection! This attack cause extra {poison_bonus} poison damage due to {other_hero.name} is in poison status")
                return other_hero.take_damage(actual_damage)
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Plague Strike, this attack cause extra {poison_bonus} poison damage due to {other_hero.name} is in poison status")
        return other_hero.take_damage(actual_damage)

    def pestilence(self, other_hero):
        # Calculate total continuous damage from existing diseases
        total_continuous_damage = sum([
            getattr(other_hero, "frost_fever_continuous_damage", 0),
            getattr(other_hero, "necrotic_decay_continuous_damage", 0),
            getattr(other_hero, "virulent_infection_continuous_damage", 0),
            getattr(other_hero, "blood_plague_continuous_damage", 0)  # Placeholder for future design
        ])

        # Shadow damage calculation based on disease damage
        coefficient = 1.0  # Balance coefficient
        actual_damage = round(total_continuous_damage * coefficient)
        actual_damage = max(1, actual_damage + random.randint(-2, 2))  # Small variation

        results = []

        # add cool down
        for skill in self.skills:
            if skill.name == "Pestilence":
              skill.if_cooldown = True
              skill.cooldown = 2

        results.append((f"{self.name} unleashes Pestilence on {other_hero.name}, and spreads their diseases!"))
        results.append(other_hero.take_damage(actual_damage))

        # List of diseases and their corresponding resistance types
        disease_resistance_map = {
            "Frost Fever": "frost_resistance",
            "Necrotic Decay": "death_resistance",
            "Virulent Infection": "poison_resistance",
            "Blood Plague": "shadow_resistance"
        }

        # Disease Spread Mechanic
        for disease_name, resistance_type in disease_resistance_map.items():
            if disease_name in [debuff.name for debuff in other_hero.debuffs]:  # If the target has this disease
                for enemy_ally in other_hero.allies_self_excluded:
                    if disease_name not in [debuff.name for debuff in enemy_ally.debuffs]:  # Avoid duplicate spreading
                        # Spread chance based on target's resistance
                        spread_success_rate = max(50, 90 - getattr(enemy_ally, resistance_type) / 2)

                        if random.randint(1, 100) <= spread_success_rate:
                            enemy_ally.status[disease_name.lower().replace(" ", "_")] = True
                            if disease_name == "Frost Fever":
                                new_debuff = Debuff(
                                    name='Frost Fever',
                                    duration = 4, 
                                    initiator = self,
                                    effect = 0.8
                                )
                                enemy_ally.add_debuff(new_debuff)
                                agility_before_reducing = enemy_ally.agility
                                enemy_ally.agility_reduced_amount_by_frost_fever = round(enemy_ally.original_agility * 0.30)  # Reduce target's agility by 30%
                                enemy_ally.agility = enemy_ally.agility - enemy_ally.agility_reduced_amount_by_frost_fever
                                basic_damage = round((self.damage - enemy_ally.frost_resistance) * 1/5)
                                variation = random.randint(-1, 1)
                                actual_damage = max(1, basic_damage + variation)
                                enemy_ally.frost_fever_continuous_damage = round(actual_damage * new_debuff.effect)
                                results.append((f"{enemy_ally.name} is infected with {disease_name}! {enemy_ally.name}'s agility is reduced from {agility_before_reducing} to {enemy_ally.agility}"))

                            elif disease_name == "Necrotic Decay":
                                new_debuff = Debuff(
                                    name='Necrotic Decay',
                                    duration=4,
                                    initiator=self,
                                    effect=0.8
                                )
                                enemy_ally.add_debuff(new_debuff)
                                enemy_ally.healing_reduction_effects['necrotic_decay'] = 0.3
                                basic_damage = round((self.damage - enemy_ally.death_resistance) * 1/5)
                                variation = random.randint(-1, 1)
                                actual_damage = max(1, basic_damage + variation)
                                enemy_ally.necrotic_decay_continuous_damage = round(actual_damage * new_debuff.effect)
                                results.append((f"{enemy_ally.name} is infected with {disease_name}! Their healing is reduced and they take continuous damage."))

                            elif disease_name == "Virulent Infection":
                                new_debuff = Debuff(
                                    name='Virulent Infection',
                                    duration=4,
                                    initiator=self,
                                    effect=0.25  
                                )
                                enemy_ally.add_debuff(new_debuff)
                                variation = random.randint(-1, 1)
                                other_hero.virulent_infection_continuous_damage = round((self.damage - other_hero.poison_resistance + variation) * new_debuff.effect)

                                results.append((f"{enemy_ally.name} is infected with {disease_name}!"))

                            elif disease_name == "Blood Plague":
                                new_debuff = Debuff(
                                    name=disease_name,
                                    duration=4,
                                    initiator=self,
                                    effect=0.8 
                                )
                            
        return "\n".join(results)
    
class Death_Knight_Blood(Death_Knight):

    major = "Blood"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Blood Plague", self.blood_plague, target_type = "single", skill_type= "damage"))
        #self.add_skill(Skill(self, "Crimson Cleave", self.icy_squall, target_type = "single", skill_type= "damage"))
        #self.add_skill(Skill(self, "Cumbrous Axe", self.winty_strike, target_type = "single", skill_type= "damage"))

    def blood_plague(self, other_hero):
        basic_damage = round((self.damage - other_hero.shadow_resistance) * 1/5)
        variation = random.randint(-1, 1)
        actual_damage = max(1, basic_damage + variation)
        blood_drain = round(actual_damage * 0.8)
        results = []
        
        if not other_hero.status['blood_plague']:
            other_hero.status['blood_plague'] = True
            for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Blood Plague" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = 4
                    other_hero.add_debuff(debuff)
                    other_hero.blood_plague_continuous_damage = round(actual_damage * debuff.effect)
                    other_hero.blood_plague_blood_drain = other_hero.blood_plague_continuous_damage * debuff.effect
                    results.append(f"{self.name} casts Blood Plague on {other_hero.name}. {other_hero.name} is taking continuous damage.")
                    results.append(other_hero.take_damage(actual_damage))
                    results.append(f"{self.name} is draining blood. {self.take_healing(blood_drain)}")
            
            debuff = Debuff(
                name='Blood Plague',
                duration=4,
                initiator=self,
                effect=0.8
            )
            debuff.type = ['Disease']
            other_hero.add_debuff(debuff)
            other_hero.blood_plague_continuous_damage = round(actual_damage * debuff.effect)
            other_hero.blood_plague_blood_drain = other_hero.blood_plague_continuous_damage * debuff.effect
            results.append(f"{self.name} casts Blood Plague on {other_hero.name}. {other_hero.name} is taking continuous damage.")
            results.append(other_hero.take_damage(actual_damage))
            results.append(f"{self.name} is draining blood. {self.take_healing(blood_drain)}")
        else:
            results.append(f"{self.name} casts Blood Plague on {other_hero.name}.")
            results.append(other_hero.take_damage(actual_damage))
            results.append(f"{self.name} is draining blood. {self.take_healing(blood_drain)}")
    
        return "\n".join(results)