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

class Rogue(Hero):

    faculty = "Rogue"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "physical"
            self.is_after_vanish = False

class Rogue_Comprehensiveness(Rogue):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Sharp Blade", self.sharp_blade, target_type = "single", skill_type= "damage",))
            self.add_skill(Skill(self, "Poisoned Dagger", self.poisoned_dagger, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shadow Evasion", self.shadow_evasion, target_type = "single", skill_type= "buffs", target_qty= 0))

    def sharp_blade(self, other_hero):
        variation = random.randint(-5, 0)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.defense
        accuracy = 50  # Bleeding effect has a 50% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy and other_hero.status['bleeding_sharp_blade'] == False:
            other_hero.status['bleeding_sharp_blade'] = True
            other_hero.status['normal'] = False
            other_hero.sharp_blade_debuff_duration = 3
            if damage_dealt > 20:
              other_hero.sharp_blade_continuous_damage = random.randint(9, 14)
            else:
              other_hero.sharp_blade_continuous_damage = random.randint(5, 8)
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Sharp Blade, {other_hero.name} is bleeding.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Sharp Blade")
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def poisoned_dagger(self, other_hero): #poisoned dagger debuff can stack twice, and continuous damage is a poison damage
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/2)
        other_hero.poisoned_dagger_applier_damage = self.damage
        accuracy = 85  # Poinsed effect has a 85% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy: # attach poisoned_dagger effect
          if other_hero.status['poisoned_dagger'] == False:
              other_hero.status['poisoned_dagger'] = True
              other_hero.status['normal'] = False
              other_hero.poisoned_dagger_debuff_duration = 4
              other_hero.poisoned_dagger_stacks += 1
              other_hero.poisoned_dagger_continuous_damage = math.ceil((actual_damage - other_hero.poison_resistance)/4)
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger, {other_hero.name} is poisoned.")
          elif other_hero.status['poisoned_dagger'] == True and other_hero.poisoned_dagger_stacks == 1:
              other_hero.poisoned_dagger_stacks += 1
              other_hero.poisoned_dagger_continuous_damage += math.ceil((actual_damage - other_hero.poison_resistance)/4)
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger again, {other_hero.name}'s poisnoning has worsened.")
          else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger, but the venom failed to take effect.")
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def shadow_evasion(self):
        self.evasion_capability = 100
        self.status['shadow_evasion'] = True
        self.shadow_evasion_buff_duration = 1
        for skill in self.skills:
            if skill.name == "Shadow Evasion":
              skill.if_cooldown = True
              skill.cooldown = 2
        return f"{self.name} has used Shadow Evasion. {self.name}'s figure vanished on the battlefield"

class Rogue_Assassination(Rogue):

    major = "Assassination"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Ambush", self.ambush, target_type = "single", skill_type= "damage",))
            self.add_skill(Skill(self, "backstab", self.backstab, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Vanish", self.vanish, target_type = "single", skill_type= "buffs", target_qty= 0))

    def ambush(self, other_hero):
        # High damage when enemy is hp 90% or above, high damage after Vanish
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = (actual_damage - other_hero.defense) * 4/5
        multiplier = 1.2
        if other_hero.hp >= other_hero.hp_max * 0.9 or self.is_after_vanish:
            damage_dealt *= multiplier
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Ambush, causing high damage.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Ambush")
        
        # Ensure damage dealt is at least 0
        damage_dealt = int(max(damage_dealt, 0))
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def backstab(self, other_hero):
        # Causeing wound debuff with 85% chance, wound debuff have effect of bleeding and agility reduction, can stack twice
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        if self.is_after_vanish:
          damage_dealt = int((actual_damage - other_hero.defense) * 2/3)
          accuracy = 100
        else:
          damage_dealt = int((actual_damage - other_hero.defense) * 1/3)
          accuracy = 85
        roll = random.randint(1, 100)
        if roll <= accuracy:
            if other_hero.status['wound_backstab'] == False:
                other_hero.status['wound_backstab'] = True
                other_hero.wound_backstab_debuff_duration = 3
                other_hero.wound_backstab_continuous_damage = random.randint(8, 10)
                agility_before_reduce = other_hero.agility
                other_hero.agility_reduced_amount_by_wound_backstab = int(other_hero.agility * 0.1)
                other_hero.agility -= other_hero.agility_reduced_amount_by_wound_backstab
                other_hero.wound_backstab_stacks += 1
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Backstab, causing wound. {other_hero.name}'s agility has reduced from {agility_before_reduce} to {other_hero.agility}.")
            elif other_hero.status['wound_backstab'] == True and other_hero.wound_backstab_stacks == 1:
                other_hero.wound_backstab_continuous_damage += random.randint(8, 10)
                other_hero.agility_reduced_amount_by_wound_backstab = int(other_hero.agility * 0.1)
                other_hero.agility -= other_hero.agility_reduced_amount_by_wound_backstab
                other_hero.wound_backstab_stacks += 1
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Backstab again, causing more wound.")
            else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Backstab")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Backstab")

        damage_dealt = max(damage_dealt, 0)
        return other_hero.take_damage(damage_dealt)

    def vanish(self):
        # Vanish: 100% evasion for 2 turn, 2nd turn will recover 10% hp but cannot do anything.
        self.evasion_capability = 100
        self.status['vanish'] = True
        self.vanish_duration = 2
        for skill in self.skills:
            if skill.name == "Vanish":
              skill.if_cooldown = True
              skill.cooldown = 3
        return f"{self.name} has used Vanish. {self.name}'s figure vanished on the battlefield"

class Rogue_Toxicology(Rogue):

    major = "Toxicology"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Poisoned Dagger", self.poisoned_dagger, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Paralyze Blade", self.paralyze_blade, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Acid Bomb", self.acid_bomb, target_type = "single", skill_type= "damage"))


    def poisoned_dagger(self, other_hero): #poisoned dagger debuff can stack twice, and continuous damage is a poison damage
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/2)
        other_hero.poisoned_dagger_applier_damage = self.damage
        accuracy = 95  # Poinsed effect has a 95% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy: # attach poisoned_dagger effect
          if other_hero.status['poisoned_dagger'] == False:
              other_hero.status['poisoned_dagger'] = True
              other_hero.poisoned_dagger_debuff_duration = 4
              other_hero.poisoned_dagger_stacks += 1
              other_hero.poisoned_dagger_continuous_damage = math.ceil((actual_damage - other_hero.poison_resistance)/4)
              if other_hero.status['paralyze_blade'] == True and other_hero.status['mixed_venom'] == False:
                other_hero.status['mixed_venom'] = True
                other_hero.mixed_venom_debuff_duration = 3
                poison_resistance_before_reduce = other_hero.poison_resistance
                other_hero.poison_resistance_reduced_amount_by_mixed_venom = int(other_hero.poison_resistance * 0.3)
                other_hero.poison_resistance -= other_hero.poison_resistance_reduced_amount_by_mixed_venom
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger, {other_hero.name} is poisoned.")
                self.game.display_battle_info(f"{other_hero.name} is suffering from a mix of two venom inside. {other_hero.name}'s poison resistance has reduced from {poison_resistance_before_reduce} to {other_hero.poison_resistance}.")
              else:
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger, {other_hero.name} is poisoned.")
          elif other_hero.status['poisoned_dagger'] == True and other_hero.poisoned_dagger_stacks == 1:
              other_hero.poisoned_dagger_stacks += 1
              other_hero.poisoned_dagger_continuous_damage = math.ceil((actual_damage - other_hero.poison_resistance)/2)
              if other_hero.status['paralyze_blade'] == True and other_hero.status['mixed_venom'] == False:
                other_hero.status['mixed_venom'] = True
                other_hero.mixed_venom_debuff_duration = 3
                poison_resistance_before_reduce = other_hero.poison_resistance
                other_hero.poison_resistance_reduced_amount_by_mixed_venom = int(other_hero.poison_resistance * 0.3)
                other_hero.poison_resistance -= other_hero.poison_resistance_reduced_amount_by_mixed_venom
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger again, {other_hero.name}'s poisnoning has worsened.")
                self.game.display_battle_info(f"{other_hero.name} is suffering from a mix of two venom inside. {other_hero.name}'s poison resistance has reduced from {poison_resistance_before_reduce} to {other_hero.poison_resistance}.")
              else:
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger again, {other_hero.name}'s poisnoning has worsened.")
          else:
              if other_hero.status['paralyze_blade'] == True and other_hero.status['mixed_venom'] == False:
                other_hero.status['mixed_venom'] = True
                other_hero.mixed_venom_debuff_duration = 3
                poison_resistance_before_reduce = other_hero.poison_resistance
                other_hero.poison_resistance_reduced_amount_by_mixed_venom = int(other_hero.poison_resistance * 0.3)
                other_hero.poison_resistance -= other_hero.poison_resistance_reduced_amount_by_mixed_venom
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger.")
                self.game.display_battle_info(f"{other_hero.name} is suffering from a mix of two venom inside. {other_hero.name}'s poison resistance has reduced from {poison_resistance_before_reduce} to {other_hero.poison_resistance}.")
              else:
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger, but the venom failed to take effect.")
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def paralyze_blade(self, other_hero): 
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/3)
        other_hero.paralyze_blade_applier_damage = self.damage
        accuracy = 90 # Paralyze venom has a 90% chance to succeed
        roll = random.randint(1, 100)
        if roll <= accuracy:
            if other_hero.status['paralyze_blade'] == False:
              other_hero.status['paralyze_blade'] = True
              other_hero.paralyze_blade_debuff_duration = 3
              other_hero.paralyze_blade_continuous_damage = math.ceil((actual_damage - other_hero.poison_resistance)/6)
              agility_before_reduce = other_hero.agility
              other_hero.agility_reduced_amount_by_paralyze_blade = int(other_hero.agility * 0.5)
              other_hero.agility -= other_hero.agility_reduced_amount_by_paralyze_blade
              other_hero.paralyze_blade_stacks += 1
              if other_hero.status['poisoned_dagger'] == True and other_hero.status['mixed_venom'] == False:
                other_hero.status['mixed_venom'] = True
                other_hero.mixed_venom_debuff_duration = 3
                poison_resistance_before_reduce = other_hero.poison_resistance
                other_hero.poison_resistance_reduced_amount_by_mixed_venom = int(other_hero.poison_resistance * 0.3)
                other_hero.poison_resistance -= other_hero.poison_resistance_reduced_amount_by_mixed_venom
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade. {other_hero.name}'s agility has reduced from {agility_before_reduce} to {other_hero.agility}.")
                self.game.display_battle_info(f"{other_hero.name} is suffering from a mix of two venom inside. {other_hero.name}'s poison resistance has reduced from {poison_resistance_before_reduce} to {other_hero.poison_resistance}.")
              else:
                self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade. {other_hero.name}'s agility has reduced from {agility_before_reduce} to {other_hero.agility}.")
            elif other_hero.status['paralyze_blade'] == True and other_hero.paralyze_blade_stacks == 1:
              other_hero.status['paralyzed'] = True
              accuracy = 80
              roll = random.randint(1, 100)
              if roll <= accuracy:
                other_hero.paralyzed_duration = 1
              else:
                other_hero.paralyzed_duration = 2
              other_hero.paralyze_blade_stacks += 1
              if other_hero.status['magic_casting'] == True:
                result = self.interrupt_magic_casting(other_hero)
                if other_hero.status['poisoned_dagger'] == True and other_hero.status['mixed_venom'] == False:
                  other_hero.status['mixed_venom'] = True
                  other_hero.mixed_venom_debuff_duration = 3
                  poison_resistance_before_reduce = other_hero.poison_resistance
                  other_hero.poison_resistance_reduced_amount_by_mixed_venom = int(other_hero.poison_resistance * 0.3)
                  other_hero.poison_resistance -= other_hero.poison_resistance_reduced_amount_by_mixed_venom
                  self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade again, {other_hero.name} is paralyzed and cannot move. {result}")
                  self.game.display_battle_info(f"{other_hero.name} is suffering from a mix of two venom inside. {other_hero.name}'s poison resistance has reduced from {poison_resistance_before_reduce} to {other_hero.poison_resistance}.")
                else:
                  self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade again, {other_hero.name} is paralyzed and cannot move. {result}")
              else:
                if other_hero.status['poisoned_dagger'] == True and other_hero.status['mixed_venom'] == False:
                  other_hero.status['mixed_venom'] = True
                  other_hero.mixed_venom_debuff_duration = 3
                  poison_resistance_before_reduce = other_hero.poison_resistance
                  other_hero.poison_resistance_reduced_amount_by_mixed_venom = int(other_hero.poison_resistance * 0.3)
                  other_hero.poison_resistance -= other_hero.poison_resistance_reduced_amount_by_mixed_venom
                  self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade again, {other_hero.name} is paralyzed and cannot move.")
                  self.game.display_battle_info(f"{other_hero.name} is suffering from a mix of two venom inside. {other_hero.name}'s poison resistance has reduced from {poison_resistance_before_reduce} to {other_hero.poison_resistance}.")
                else:
                  self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade again, {other_hero.name} is paralyzed and cannot move.")
            else:
                if other_hero.status['poisoned_dagger'] == True and other_hero.status['mixed_venom'] == False:
                  other_hero.status['mixed_venom'] = True
                  other_hero.mixed_venom_debuff_duration = 3
                  poison_resistance_before_reduce = other_hero.poison_resistance
                  other_hero.poison_resistance_reduced_amount_by_mixed_venom = int(other_hero.poison_resistance * 0.3)
                  other_hero.poison_resistance -= other_hero.poison_resistance_reduced_amount_by_mixed_venom
                  self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade.")
                  self.game.display_battle_info(f"{other_hero.name} is suffering from a mix of two venom inside. {other_hero.name}'s poison resistance has reduced from {poison_resistance_before_reduce} to {other_hero.poison_resistance}.")
                else:
                  self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade again.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Paralyze Blade, but the venom failed to take effect.")
        damage_dealt = max(damage_dealt, 0)
        return other_hero.take_damage(damage_dealt)

    def acid_bomb(self, other_hero): 
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.poison_resistance)* 1/2)
        if other_hero.status['acid_bomb'] == False:
          other_hero.status['acid_bomb'] = True
          other_hero.acid_bomb_debuff_duration = 1
          damage_before_reduce = other_hero.damage
          other_hero.damage_reduced_amount_by_acid_bomb = int(other_hero.damage * 0.5)
          other_hero.damage -= other_hero.damage_reduced_amount_by_acid_bomb
          if other_hero.status['mixed_venom'] == True and other_hero.status['unstable_compound'] == False:
            other_hero.status['unstable_compound'] = True
            other_hero.unstable_compound_debuff_duration = 3
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Acid Bomb, {other_hero.name}'s weapon is melting. {other_hero.name}'s damage has reduced from {damage_before_reduce} to {other_hero.damage}.")
            self.game.display_battle_info(f"All venom on {other_hero.name} has formed an unstable compound.")
          else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Acid Bomb, {other_hero.name}'s weapon is melting. {other_hero.name}'s damage has reduced from {damage_before_reduce} to {other_hero.damage}.")
        else:
          if other_hero.status['mixed_venom'] == True and other_hero.status['unstable_compound'] == False:
            other_hero.status['unstable_compound'] = True
            other_hero.unstable_compound_debuff_duration = 3
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Acid Bomb.")
            self.game.display_battle_info(f"All venom on {other_hero.name} has formed an unstable compound.")
          else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Acid Bomb.")
        for skill in self.skills:
            if skill.name == "Acid Bomb":
              skill.if_cooldown = True
              skill.cooldown = 3
        damage_dealt = max(damage_dealt, 0)
        return other_hero.take_damage(damage_dealt)