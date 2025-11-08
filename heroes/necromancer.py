import math
import random
from heroes import *
from skills import *
from .summon_unit import SkeletonWarrior

ORANGE = "\033[38;5;208m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Necromancer(Hero):

    faculty = "Necromancer"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "death"

class Necromancer_Necromancy(Necromancer):

    major = "Necromancy"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.sys_init = sys_init
        self.add_skill(Skill(self, "Command Skeleton", self.command_skeleton, target_type="single", skill_type="summon", target_qty= 0))
        self.add_skill(Skill(self, "Death Bolt", self.death_bolt, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Unholy Frenzy", self.unholy_frenzy, "single", skill_type= "damage_healing"))

    def command_skeleton(self):
        skeleton_name = f"{self.name}'s Skeleton Warrior"
        skeleton_group = self.group
        skeleton_duration = 4  # The skeleton will last for 4 rounds
        skeleton_race = 'undead'
        skeleton = SkeletonWarrior(self.sys_init, skeleton_name, skeleton_group, self, skeleton_duration, skeleton_race, is_player_controlled=False)
        skeleton.take_game_instance(self.game)
        self.summoned_unit = skeleton
        for hero in self.game.player_heroes:
          if self.name == hero.name:
            self.game.player_heroes.append(skeleton)
            self.game.heroes.append(skeleton)
            self.game.unactioned_sorted_heroes.append(skeleton)
            break
        else:
          self.game.opponent_heroes.append(skeleton)
          self.game.heroes.append(skeleton)
          self.game.unactioned_sorted_heroes.append(skeleton)
        for skill in self.skills:
          if skill.name == "Command Skeleton":
            skill.if_cooldown = True
            skill.cooldown = 3
        return f"{self.name} uses Command Skeleton and summons a Skeleton Warrior in the battle field."

    def death_bolt(self, other_hero):
        variation = random.randint(-1, 1)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.death_resistance) * (4/5))
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

    def unholy_frenzy(self, other_hero, target_type):
        if other_hero.status['unholy_frenzy'] == False:
            other_hero.status['unholy_frenzy'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Unholy Frenzy" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 3   # Effect lasts for 2 rounds
                    other_hero.add_buff(buff)
                    damage_before_increasing = other_hero.damage # damage increase
                    other_hero.damage_increased_amount_by_unholy_frenzy = round(other_hero.original_damage * buff.effect)  # Increase hero's damage by 15%
                    other_hero.damage = other_hero.damage + other_hero.damage_increased_amount_by_unholy_frenzy
                    agility_before_increasing = other_hero.agility
                    other_hero.agility_increased_amount_by_unholy_frenzy = round(other_hero.original_agility * buff.effect * 13)  # Increase hero's agility by 200%
                    other_hero.agility = other_hero.agility + other_hero.agility_increased_amount_by_unholy_frenzy
                    damage_dealt = round(other_hero.hp_max * buff.effect) # Hero loose 15% of hp each round
                    other_hero.unholy_frenzy_continuous_damage = damage_dealt
                    self.game.display_battle_info(f"{self.name} uses Unholy Frenzy on {other_hero.name}. {other_hero.name}'s damage and agility has increased, but their life will be taken away.")
                    return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}. {other_hero.take_damage(damage_dealt)}"

            buff = Buff(
                name='Unholy Frenzy',
                duration = 3,
                initiator = self,
                effect = 0.15
            )
            other_hero.add_buff(buff)
            damage_before_increasing = other_hero.damage # damage increase
            other_hero.damage_increased_amount_by_unholy_frenzy = round(other_hero.original_damage * buff.effect)  # Increase hero's damage by 15%
            other_hero.damage = other_hero.damage + other_hero.damage_increased_amount_by_unholy_frenzy
            agility_before_increasing = other_hero.agility
            other_hero.agility_increased_amount_by_unholy_frenzy = round(other_hero.original_agility * buff.effect * 13)  # Increase hero's agility by 200%
            other_hero.agility = other_hero.agility + other_hero.agility_increased_amount_by_unholy_frenzy
            damage_dealt = round(other_hero.hp_max * buff.effect) # Hero loose 15% of hp each round
            other_hero.unholy_frenzy_continuous_damage = damage_dealt
            self.game.display_battle_info(f"{self.name} uses Unholy Frenzy on {other_hero.name}. {other_hero.name}'s damage and agility has increased, but will continuous loose HP.")
            return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}. {other_hero.take_damage(damage_dealt)}"
        else:
            return f"{self.name} tries to use Unholy Frenzy on {other_hero.name}. But {other_hero.name} has already been in frenzy"

# Battling Strategy_________________________________________________________

    def strategy_0(self):
        self.probability_command_skeleton = 0.85
        self.probability_death_bolt = 0.15
        self.probability_unholy_frenzy = 0

    def strategy_1(self):
        self.probability_command_skeleton = 0
        self.probability_death_bolt = 0.85
        self.probability_unholy_frenzy = 0.15

    def strategy_2(self):
        self.probability_command_skeleton = 0
        self.probability_death_bolt = 1
        self.probability_unholy_frenzy = 0

    def strategy_3(self):
        self.probability_command_skeleton = 0
        self.probability_death_bolt = 0
        self.probability_unholy_frenzy = 1

    def strategy_4(self):
        self.probability_command_skeleton = 0
        self.probability_death_bolt = 1
        self.probability_unholy_frenzy = 0

    def battle_analysis(self, opponents, allies):
        #print(f"Opponents: {[opponent.profession for opponent in opponents]}")
        #print(f"Allies: {[ally.profession for ally in allies]}")
        #print(f"Necromancer profession: {self.profession}")
        #if self not in allies:
          #print("Necromancer not in allies")

        # Define high-risk DPS hero list
        target_opponent_profession_list_for_frenzy = ['Priest_Comprehensiveness', 'Priest_Discipline', 'Prist_Shelter', 'Priest_Shadow', 'Priest_Devine']
        target_ally_profession_list_for_frenzy = ['Warrior_Comprehensiveness', 'Warrior_Skeleton', 'Paladin_Comprehensiveness', 'Necromancer_Comprehensiveness', 'Warlock_Comprehensiveness', 'Warlock_Affliction', 'Warlock_Destructive']
        #print(f"target_opponent_profession_list_for_frenzy: {target_opponent_profession_list_for_frenzy}")
        #print(f"target_ally_profession_list_for_frenzy: {target_ally_profession_list_for_frenzy}")

        # Sort hp and resistance from low to high
        sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
        sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
        sorted_opponents_resistance = sorted(opponents, key=lambda hero: hero.death_resistance, reverse=False)

        # Find heroes with unholy_frenzy debuffs
        opponents_with_frenzy = [opponent for opponent in opponents if opponent.status.get('unholy_frenzy', False)]
        opponents_without_frenzy = [opponent for opponent in opponents if not opponent.status.get('unholy_frenzy', False)]
        allies_with_frenzy = [ally for ally in allies if ally.status.get('unholy_frenzy', False)]
        allies_without_frenzy = [ally for ally in allies if not ally.status.get('unholy_frenzy', False)]

        # Find target_heroes for unholy_frenzy debuffs
        target_opponents_for_frenzy = [opponent for opponent in opponents if opponent.profession in target_opponent_profession_list_for_frenzy]
        target_opponents_for_frenzy_without_frenzy = [opponent for opponent in target_opponents_for_frenzy if opponent in opponents_without_frenzy]
        target_allies_for_frenzy = [ally for ally in allies if ally.profession in target_ally_profession_list_for_frenzy]
        target_allies_for_frenzy_without_frenzy = [ally for ally in target_allies_for_frenzy if ally in allies_without_frenzy]
        if not target_allies_for_frenzy:
          target_allies_for_frenzy.append(self)

        #print(f"target_opponents_for_frenzy: {target_opponents_for_frenzy}")
        #print(f"target_allies_for_frenzy: {target_allies_for_frenzy}")

        # Eliminate low hp hero
        if sorted_opponents[0].hp < round((self.damage - sorted_opponents[0].death_resistance) * (4/5)):
          self.strategy_2()
          return sorted_opponents[0]

        # High chance 85% summon skeleton warrior if not existed
        if self.summoned_unit is None:
          # Find the "Command Skeleton" skill in the list of skills
          summon_skill = next((skill for skill in self.skills if skill.name == "Command Skeleton"), None)
          # Check if the skill is off cooldown
          if summon_skill and not summon_skill.if_cooldown:
            self.strategy_0()
            return sorted_opponents[0]

        # Use death bolt if hp < 40%
        if self.hp <= self.hp_max * 0.4:
          self.strategy_2()
          return sorted_opponents[0]
        #"""
        # Strategically apply unholy frenzy
        if len(opponents_with_frenzy) == 0 and len(allies_with_frenzy) == 0:
          if len(target_opponents_for_frenzy) == 0:
            self.strategy_3()
            #print(f"1. target_allies_for_frenzy: {target_allies_for_frenzy}")
            return random.choice(target_allies_for_frenzy)
          else:
            target_combine_list_for_frenzy = target_opponents_for_frenzy + target_allies_for_frenzy
            self.strategy_3()
            #print(f"2. target_allies_for_frenzy: {target_combine_list_for_frenzy}")
            return random.choice(target_combine_list_for_frenzy)
        elif len(opponents_with_frenzy) < 2 and len(allies_with_frenzy) < 2:
          accuracy = 50
          roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
          if roll <= accuracy:
            target_combine_list_for_frenzy = target_opponents_for_frenzy_without_frenzy + target_allies_for_frenzy_without_frenzy
            if len(target_combine_list_for_frenzy) > 0:
              self.strategy_3()
              #print(f"3. target_allies_for_frenzy: {target_combine_list_for_frenzy}")
              return random.choice(target_combine_list_for_frenzy)
        #"""
        # Attack hero with less 50% hp
        if sorted_opponents[0].hp <= round(sorted_opponents[0].hp_max * 0.5):
          self.strategy_2()
          return sorted_opponents[0]

        # If no special conditions, attack the opponent with the lowest death resistance
        self.strategy_1()
        return sorted_opponents_resistance[0]

    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_command_skeleton, self.probability_death_bolt, self.probability_unholy_frenzy]
        chosen_skill = random.choices(self.skills, weights=skill_weights)[0]
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        chosen_opponent = self.preset_target
        return chosen_opponent

class Necromancer_Necromancy(Necromancer):

    major = "Bone_Master"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.sys_init = sys_init
        self.add_skill(Skill(self, "Command Skeleton", self.command_skeleton, target_type="single", skill_type="summon", target_qty= 0))
        self.add_skill(Skill(self, "Death Bolt", self.death_bolt, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Unholy Frenzy", self.unholy_frenzy, "single", skill_type= "damage_healing"))

    def command_skeleton_mage(self):
        skeleton_name = f"{self.name}'s Skeleton Mage"
        skeleton_group = self.group
        skeleton_duration = 4  # The skeleton will last for 4 rounds
        skeleton_race = 'undead'
        skeleton_mage = SkeletonMage(self.sys_init, skeleton_name, skeleton_group, self, skeleton_duration, skeleton_race, is_player_controlled=False)
        skeleton_mage.take_game_instance(self.game)
        self.summoned_unit = skeleton_mage
        for hero in self.game.player_heroes:
          if self.name == hero.name:
            self.game.player_heroes.append(skeleton_mage)
            self.game.heroes.append(skeleton_mage)
            self.game.unactioned_sorted_heroes.append(skeleton_mage)
            break
        else:
          self.game.opponent_heroes.append(skeleton_mage)
          self.game.heroes.append(skeleton_mage)
          self.game.unactioned_sorted_heroes.append(skeleton_mage)
        for skill in self.skills:
          if skill.name == "Command Skeleton Mage":
            skill.if_cooldown = True
            skill.cooldown = 3
        return f"{self.name} uses Command Skeleton Mage and summons a Skeleton Mage in the battle field."

    def bone_sword(self, other_hero):
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        damage_dealt_pysical = round((actual_damage - other_hero.defence) * (1/2))
        damage_dealt_death = round((actual_damage - other_hero.death_resistance) * (1/2))
        damage_dealt = max(damage_dealt_pysical + damage_dealt_death, 0)
        self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Bone Sword.")
        return other_hero.take_damage(damage_dealt)

    def bone_armor(self, other_hero, target_type):
        if other_hero.status['bone_armor'] == False:
            other_hero.status['bone_armor'] = True
            variation = random.randint(0, 5)
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Bone Armor" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 3   # Effect lasts for 3 rounds
                    other_hero.add_buff(buff)
                    defence_before_increasing = other_hero.defence # defence increase
                    other_hero.defence_increased_amount_by_bone_armor = 70 - defence_before_increasing + variation  # Increase hero's defence till 70
                    other_hero.defence = other_hero.defence + other_hero.defence_increased_amount_by_bone_armor
                    agility_before_reducing = other_hero.agility
                    other_hero.agility_reduced_amount_by_bone_armor =  agility_before_reducing - (variation + 1) # reducing hero's agility till 5
                    other_hero.agility = other_hero.agility - other_hero.agility_reduced_amount_by_bone_armor
                    self.game.display_battle_info(f"{self.name} applies Bone Armor on {other_hero.name}.")
                    return f"{other_hero.name}'s defence has increased from {defence_before_increasing} to {other_hero.defence}, agility has reduced from {agility_before_reducing} to {other_hero.agility}."

            buff = Buff(
                name='Bone Armor',
                duration = 3,
                initiator = self,
                effect = 0.15
            )
            other_hero.add_buff(buff)
            defence_before_increasing = other_hero.defence # defence increase
            other_hero.defence_increased_amount_by_bone_armor = 70 - defence_before_increasing + variation  # Increase hero's defence till 70
            other_hero.defence = other_hero.defence + other_hero.defence_increased_amount_by_bone_armor
            agility_before_reducing = other_hero.agility
            other_hero.agility_reduced_amount_by_bone_armor =  agility_before_reducing - (variation + 1) # reducing hero's agility till 5
            other_hero.agility = other_hero.agility - other_hero.agility_reduced_amount_by_bone_armor
            self.game.display_battle_info(f"{self.name} applies Bone Armor on {other_hero.name}.")
            return f"{other_hero.name}'s defence has increased from {defence_before_increasing} to {other_hero.defence}, agility has reduced from {agility_before_reducing} to {other_hero.agility}."
        else:
            return f"{self.name} tries to use Bone Armor on {other_hero.name}. But {other_hero.name} has already gotten Bone Armor effect"

# Battling Strategy_________________________________________________________


class Necromancer_Comprehensiveness(Necromancer):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.sys_init = sys_init
        self.add_skill(Skill(self, "Command Skeleton", self.command_skeleton, target_type="single", skill_type="summon", target_qty= 0))
        self.add_skill(Skill(self, "Life Drain", self.life_drain, "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Unholy Frenzy", self.unholy_frenzy, "single", skill_type= "damage_healing"))

    def command_skeleton(self):
        skeleton_name = f"{self.name}'s Skeleton Warrior"
        skeleton_group = self.group
        skeleton_duration = 4  # The skeleton will last for 4 rounds
        skeleton_race = 'undead'
        skeleton = SkeletonWarrior(self.sys_init, skeleton_name, skeleton_group, self, skeleton_duration, skeleton_race, is_player_controlled=False)
        skeleton.take_game_instance(self.game)
        self.summoned_unit = skeleton
        for hero in self.game.player_heroes:
          if self.name == hero.name:
            self.game.player_heroes.append(skeleton)
            self.game.heroes.append(skeleton)
            self.game.unactioned_sorted_heroes.append(skeleton)
            break
        else:
          self.game.opponent_heroes.append(skeleton)
          self.game.heroes.append(skeleton)
          self.game.unactioned_sorted_heroes.append(skeleton)
        for skill in self.skills:
          if skill.name == "Command Skeleton":
            skill.if_cooldown = True
            skill.cooldown = 3
        return f"{self.name} uses Command Skeleton and summons a Skeleton Warrior in the battle field."

    def life_drain(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.death_resistance) * 3/4)
        damage_dealt = max(damage_dealt, 0)

        if other_hero.status['holy_word_shell'] == True:
          if damage_dealt <= other_hero.holy_word_shell_absorption:
           healing_amount = 0
           healing_amount_extra_hero = 0
          else:
            healing_amount = round((damage_dealt - other_hero.holy_word_shell_absorption) * 0.45)
            healing_amount_extra_hero = round((damage_dealt - other_hero.holy_word_shell_absorption) * 0.35)
        else:
          healing_amount = round(damage_dealt * 0.45)
          healing_amount_extra_hero = round(damage_dealt * 0.35)
        self.game.display_battle_info(f"{self.name} casts Life Drain at {other_hero.name}.")
        self.game.display_battle_info(f"{other_hero.take_damage(damage_dealt)}")

        for hero in self.allies_self_excluded:
          if hero.is_summoned == True and hero.master == self:
            self.game.display_battle_info(f"{hero.take_healing(healing_amount_extra_hero)}")
        else:
          return self.take_healing(healing_amount)

    def unholy_frenzy(self, other_hero, target_type):
        if other_hero.status['unholy_frenzy'] == False:
            other_hero.status['unholy_frenzy'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Unholy Frenzy" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 3   # Effect lasts for 2 rounds
                    other_hero.add_buff(buff)
                    damage_before_increasing = other_hero.damage # damage increase
                    other_hero.damage_increased_amount_by_unholy_frenzy = round(other_hero.original_damage * buff.effect)  # Increase hero's damage by 15%
                    other_hero.damage = other_hero.damage + other_hero.damage_increased_amount_by_unholy_frenzy
                    agility_before_increasing = other_hero.agility
                    other_hero.agility_increased_amount_by_unholy_frenzy = round(other_hero.original_agility * buff.effect * 13)  # Increase hero's agility by 200%
                    other_hero.agility = other_hero.agility + other_hero.agility_increased_amount_by_unholy_frenzy
                    damage_dealt = round(other_hero.hp_max * buff.effect) # Hero loose 15% of hp each round
                    other_hero.unholy_frenzy_continuous_damage = damage_dealt
                    self.game.display_battle_info(f"{self.name} uses Unholy Frenzy on {other_hero.name}. {other_hero.name}'s damage and agility has increased, but their life will be taken away.")
                    return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}. {other_hero.take_damage(damage_dealt)}"

            buff = Buff(
                name='Unholy Frenzy',
                duration = 3,
                initiator = self,
                effect = 0.15
            )
            other_hero.add_buff(buff)
            damage_before_increasing = other_hero.damage # damage increase
            other_hero.damage_increased_amount_by_unholy_frenzy = round(other_hero.original_damage * buff.effect)  # Increase hero's damage by 15%
            other_hero.damage = other_hero.damage + other_hero.damage_increased_amount_by_unholy_frenzy
            agility_before_increasing = other_hero.agility
            other_hero.agility_increased_amount_by_unholy_frenzy = round(other_hero.original_agility * buff.effect * 13)  # Increase hero's agility by 200%
            other_hero.agility = other_hero.agility + other_hero.agility_increased_amount_by_unholy_frenzy
            damage_dealt = round(other_hero.hp_max * buff.effect) # Hero loose 15% of hp each round
            other_hero.unholy_frenzy_continuous_damage = damage_dealt
            self.game.display_battle_info(f"{self.name} uses Unholy Frenzy on {other_hero.name}. {other_hero.name}'s damage and agility has increased, but will continuous loose HP.")
            return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}. {other_hero.take_damage(damage_dealt)}"
        else:
            return f"{self.name} tries to use Unholy Frenzy on {other_hero.name}. But {other_hero.name} has already been in frenzy"

# Battling Strategy_________________________________________________________