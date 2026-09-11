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

    def __init__(self, sys_init, name, group, is_player_controlled, major, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty, position=position)
            self.hero_damage_type = "physical"
            self.is_after_vanish = False

class Rogue_Comprehensiveness(Rogue):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
            self.preset_target = None
            self.add_skill(Skill(self, "Sharp Blade", self.sharp_blade, target_type = "single", skill_type= "damage",attack_type = "melee"))
            self.add_skill(Skill(self, "Poisoned Dagger", self.poisoned_dagger, target_type = "single", skill_type= "damage", attack_type = "ranged_instant"))
            self.add_skill(Skill(self, "Shadow Evasion", self.shadow_evasion, target_type = "single", skill_type= "buffs", target_qty= 0))

    @staticmethod
    def _sharp_blade_direct_damage(damage, defense, variation):
        """Pure direct damage shared by execution and audited preview."""
        return max(damage + variation - defense, 0)

    @staticmethod
    def _poisoned_dagger_direct_damage(damage, defense, variation):
        """Pure direct damage shared by execution and audited preview."""
        return max(int((damage + variation - defense) / 2), 0)

    def audited_direct_damage_range(self, skill_name, target):
        """Return the MVP Rogue skill's RNG-free immediate damage range.

        The legacy callbacks call ``take_damage`` without attack metadata, so
        their live damage does not receive a formation multiplier. Preview
        intentionally preserves that behavior rather than changing balance.
        """
        if skill_name == "Sharp Blade":
            calculate = self._sharp_blade_direct_damage
            variations = (-5, 0)
        elif skill_name == "Poisoned Dagger":
            calculate = self._poisoned_dagger_direct_damage
            variations = (-2, 2)
        else:
            return None
        values = [
            calculate(self.damage, target.defense, variation)
            for variation in variations
        ]
        return min(values), max(values)

    def sharp_blade(self, other_hero):
        variation = random.randint(-5, 0)
        damage_dealt = self._sharp_blade_direct_damage(
            self.damage, other_hero.defense, variation
        )
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
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def poisoned_dagger(self, other_hero): #poisoned dagger debuff can stack twice, and continuous damage is a poison damage
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = self._poisoned_dagger_direct_damage(
            self.damage, other_hero.defense, variation
        )
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

    # Battling Strategy_________________________________________________________

    # Part A — battle information collection ----------------------------------
    def _rogue_comprehensiveness_combatant_snapshot(self, hero):
        """Collect only the live combat facts used by this Rogue strategy."""
        active_statuses = {
            name for name, active in hero.status.items() if active
        }
        return {
            "hero": hero,
            "faculty": hero.faculty,
            "major": hero.major,
            "position": hero.position,
            "actioned": hero.actioned,
            "alive": hero.hp > 0,
            "hp": hero.hp,
            "hp_max": hero.hp_max,
            "hp_ratio": hero.hp / hero.hp_max if hero.hp_max else 0,
            "damage": hero.damage,
            "defense": hero.defense,
            "original_defense": hero.original_defense,
            "agility": hero.agility,
            "poison_resistance": hero.poison_resistance,
            "active_statuses": active_statuses,
            "poisoned_dagger_stacks": (
                getattr(hero, "poisoned_dagger_stacks", 0)
                if "poisoned_dagger" in active_statuses
                else 0
            ),
            "poisoned_dagger_duration": getattr(
                hero, "poisoned_dagger_debuff_duration", 0
            ),
            "sharp_blade_duration": getattr(
                hero, "sharp_blade_debuff_duration", 0
            ),
            "buffs": [
                {
                    "name": buff.name,
                    "duration": buff.duration,
                    "initiator": buff.initiator,
                }
                for buff in hero.buffs
            ],
            "debuffs": [
                {
                    "name": debuff.name,
                    "duration": debuff.duration,
                    "initiator": debuff.initiator,
                }
                for debuff in hero.debuffs
            ],
            "skill_cooldowns": {
                skill.name: {
                    "available": skill.is_available and not skill.if_cooldown,
                    "rounds_remaining": skill.cooldown,
                }
                for skill in hero.skills
            },
        }

    def collect_battle_information(self, opponents, allies):
        """Build the Rogue's current-turn view from engine-owned state."""
        opponent_snapshots = [
            self._rogue_comprehensiveness_combatant_snapshot(hero)
            for hero in opponents
        ]
        ally_snapshots = [
            self._rogue_comprehensiveness_combatant_snapshot(hero)
            for hero in allies
        ]
        alive_opponents = [item for item in opponent_snapshots if item["alive"]]
        living_front_opponents = [
            item for item in alive_opponents if item["position"] == "front"
        ]
        reachable_melee_opponents = living_front_opponents or alive_opponents
        damageable_opponents = [
            item
            for item in alive_opponents
            if not (
                item["active_statuses"]
                & {"shield_of_protection"}
            )
        ]
        damageable_melee_opponents = [
            item
            for item in reachable_melee_opponents
            if item in damageable_opponents
        ]
        return {
            "self": self._rogue_comprehensiveness_combatant_snapshot(self),
            "allies": [item for item in ally_snapshots if item["alive"]],
            "opponents": alive_opponents,
            "damageable_opponents": damageable_opponents,
            "reachable_melee_opponents": reachable_melee_opponents,
            "damageable_melee_opponents": damageable_melee_opponents,
            "unactioned_opponents": [
                item for item in alive_opponents if not item["actioned"]
            ],
            "formations": {
                "ally_positions": tuple(item["position"] for item in ally_snapshots),
                "opponent_positions": tuple(
                    item["position"] for item in opponent_snapshots
                ),
            },
            "skills": {
                skill.name: skill
                for skill in self.skills
                if skill.is_available and not skill.if_cooldown
            },
        }

    # Part B — battle analysis -------------------------------------------------
    @staticmethod
    def _rogue_priority_target(candidates):
        """Prefer kill pressure, then lower defence, agility, and stable name."""
        return min(
            candidates,
            key=lambda item: (
                item["hp_ratio"],
                item["defense"],
                -item["agility"],
                item["hero"].name,
            ),
        )

    @staticmethod
    def _rogue_poison_target(candidates):
        """Prefer targets where Poisoned Dagger has the best implemented value."""
        return min(
            candidates,
            key=lambda item: (
                item["poison_resistance"],
                item["hp_ratio"],
                -item["agility"],
                item["hero"].name,
            ),
        )

    def analyse_battle_strategy(self, battle_information):
        """Choose one legal Rogue action through a small ordered rule set."""
        skills = battle_information["skills"]
        opponents = battle_information["opponents"]
        damageable = battle_information["damageable_opponents"] or opponents
        reachable = battle_information["reachable_melee_opponents"]
        damageable_reachable = (
            battle_information["damageable_melee_opponents"] or reachable
        )
        self_state = battle_information["self"]

        sharp_blade = skills.get("Sharp Blade")
        poisoned_dagger = skills.get("Poisoned Dagger")
        shadow_evasion = skills.get("Shadow Evasion")

        # 1. Protect a critically injured Rogue while enemies still have actions.
        if (
            shadow_evasion
            and self_state["hp_ratio"] <= 0.35
            and battle_information["unactioned_opponents"]
        ):
            return shadow_evasion, None

        # 2. Finish a vulnerable target. Sharp Blade is the stronger direct hit;
        # Poisoned Dagger remains able to reach a screened rear target.
        low_health = [item for item in damageable if item["hp_ratio"] <= 0.25]
        low_health_melee = [item for item in low_health if item in damageable_reachable]
        if sharp_blade and low_health_melee:
            return sharp_blade, self._rogue_priority_target(low_health_melee)["hero"]
        if poisoned_dagger and low_health:
            return poisoned_dagger, self._rogue_priority_target(low_health)["hero"]

        # 3. Complete a useful second poison stack before the existing duration
        # expires. The implementation caps at two and does not refresh at cap.
        one_stack = [
            item
            for item in damageable
            if item["poisoned_dagger_stacks"] == 1
            and item["poisoned_dagger_duration"] > 0
            and self_state["damage"] > item["poison_resistance"]
        ]
        if poisoned_dagger and one_stack:
            return poisoned_dagger, self._rogue_poison_target(one_stack)["hero"]

        # 4. Establish poison only where its resistance-based periodic damage is
        # viable and no active stack would be wasted.
        unpoisoned = [
            item
            for item in damageable
            if item["poisoned_dagger_stacks"] == 0
            and self_state["damage"] > item["poison_resistance"]
        ]
        if poisoned_dagger and unpoisoned:
            return poisoned_dagger, self._rogue_poison_target(unpoisoned)["hero"]

        # 5. Open a bleeding wound on a reachable target. Recasts do not refresh
        # Sharp Blade, so already-bleeding targets are deliberately excluded.
        unbleeding = [
            item
            for item in damageable_reachable
            if "bleeding_sharp_blade" not in item["active_statuses"]
            and self_state["hero"].damage > item["defense"]
        ]
        if sharp_blade and unbleeding:
            return sharp_blade, self._rogue_priority_target(unbleeding)["hero"]

        # 6. Evasion remains useful at moderate health when at least one enemy
        # can still act this round, after higher-value pressure has been checked.
        if (
            shadow_evasion
            and self_state["hp_ratio"] <= 0.55
            and battle_information["unactioned_opponents"]
        ):
            return shadow_evasion, None

        # 7. Deterministic direct-damage fallback. Capped poison and active bleed
        # are not treated as refresh opportunities.
        if sharp_blade and damageable_reachable:
            return sharp_blade, self._rogue_priority_target(damageable_reachable)["hero"]
        if poisoned_dagger and damageable:
            return poisoned_dagger, self._rogue_priority_target(damageable)["hero"]
        if shadow_evasion:
            return shadow_evasion, None
        if skills and opponents:
            skill = next(iter(skills.values()))
            target = None if skill.target_qty == 0 else self._rogue_priority_target(opponents)["hero"]
            return skill, target
        return None, None

    # Part C — return the chosen action to the live API adapter ----------------
    def ai_choose_skill(self, opponents, allies):
        self.rogue_comprehensiveness_battle_information = (
            self.collect_battle_information(opponents, allies)
        )
        skill, target = self.analyse_battle_strategy(
            self.rogue_comprehensiveness_battle_information
        )
        self.preset_target = target
        return skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        return self.preset_target

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
