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
            if damage_dealt > 0:
              other_hero.sharp_blade_continuous_damage = random.randint(8, 14)
            else:
              other_hero.sharp_blade_continuous_damage = random.randint(5, 10)
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Sharp Blade, {other_hero.name} is bleeding.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Sharp Blade")
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def poisoned_dagger(self, other_hero): #poisoned dagger debuff can stack twice, and continuous damage from poison is a magial damage
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/2)
        accuracy = 85  # Poinsed effect has a 85% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy: # attach poisoned_dagger effect
          if other_hero.status['poisoned_dagger'] == False:
              other_hero.status['poisoned_dagger'] = True
              other_hero.status['normal'] = False
              other_hero.poisoned_dagger_debuff_duration = 4
              other_hero.poisoned_dagger_stacks += 1
              if damage_dealt > 0:
                other_hero.poisoned_dagger_continuous_damage = math.ceil((actual_damage - other_hero.poison_resistance)/4)
              else:
                other_hero.poisoned_dagger_continuous_damage = random.randint(1, 10)
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger, {other_hero.name} is poisoned.")
          elif other_hero.status['poisoned_dagger'] == True and other_hero.poisoned_dagger_stacks == 1:
              other_hero.poisoned_dagger_stacks += 1
              if damage_dealt > 0:
                other_hero.poisoned_dagger_continuous_damage += math.ceil((actual_damage - other_hero.poison_resistance)/4)
              else:
                other_hero.poisoned_dagger_continuous_damage += random.randint(1, 10)
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger again, {other_hero.name}'s poisnoning has worsened.")
          else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Poisoned Dagger")
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