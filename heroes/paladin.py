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

class Paladin(Hero):

    faculty = "Paladin"

    def __init__(self, sys_init, name, group, is_player_controlled, major, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty, position=position)
            self.hero_damage_type = "hybrid"

    # Part A — battle information collection -------------------------------
    # These mirror the adapter's target contract.  Strategy may rank every
    # live enemy for ranged skills, but a melee skill must never nominate a
    # rear hero while a living front hero protects that side.
    def collect_battle_information(self, opponents, allies):
        live_opponents = [hero for hero in opponents if hero.hp > 0]
        live_allies = [hero for hero in allies if hero.hp > 0]

        def combatant(hero):
            return {
                "hero": hero,
                "hp_ratio": hero.hp / hero.hp_max if hero.hp_max else 0,
                "position": hero.position,
                "faculty": hero.faculty,
                "major": hero.major,
                "defense": hero.defense,
                "damage": hero.damage,
                "active_statuses": {
                    name for name, active in hero.status.items() if active
                },
            }

        return {
            "self": combatant(self),
            "allies": [combatant(hero) for hero in live_allies],
            "opponents": [combatant(hero) for hero in live_opponents],
            "skills": {
                skill.name: skill
                for skill in self.skills
                if not skill.is_passive and skill.is_available and not skill.if_cooldown
            },
            "formations": {
                "ally_positions": tuple(hero.position for hero in live_allies),
                "opponent_positions": tuple(hero.position for hero in live_opponents),
            },
        }

    def _paladin_legal_targets(self, skill, opponents, allies):
        if skill is None or skill.target_qty == 0:
            return []
        if skill.skill_type in {"healing", "buffs"}:
            pool = [hero for hero in allies if hero.hp > 0]
        elif skill.skill_type == "damage_healing":
            pool = [hero for hero in opponents + allies if hero.hp > 0]
        else:
            pool = [hero for hero in opponents if hero.hp > 0]
        if skill.skill_type == "damage" and skill.attack_type == "melee":
            front = [hero for hero in pool if hero.position == "front"]
            if front:
                pool = front
        return pool

    @staticmethod
    def _paladin_lowest_health(combatants):
        return min(
            combatants,
            key=lambda item: (item["hp_ratio"], item["hero"].name),
        ) if combatants else None

    @staticmethod
    def _paladin_priority_enemy(combatants):
        threat = {"Mage": 0, "Rogue": 0, "Priest": 1, "Paladin": 2, "Warrior": 2}
        return min(
            combatants,
            key=lambda item: (
                threat.get(item["faculty"], 1),
                item["hp_ratio"],
                item["hero"].name,
            ),
        ) if combatants else None

    def _paladin_choose(self, skill, target=None):
        self.preset_target = target
        return skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        return getattr(self, "preset_target", None)

class Paladin_Retribution(Paladin):

    major = "Retribution"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
            self.add_skill(Skill(self, "Hammer of Anger", self.hammer_of_anger, target_type = "single", skill_type= "damage", attack_type = "ranged_projectile"))
            self.add_skill(Skill(self, "Crusader Strike", self.crusader_strike, target_type = "single", skill_type= "damage", attack_type = "melee", independent_effect_action=self.independent_crusader_strike))
            self.add_skill(Skill(self, "Flash of Light", self.flash_of_light, "single", skill_type= "healing"))

    def hammer_of_anger(self, other_hero, attack_type="NA"):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.defense
        damage_dealt = max(damage_dealt, 0)
        if self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 1:
          extra_holy_damage = random.randint(3, 5)
          damage_dealt += extra_holy_damage
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}, due to Shield of Righteous, this attack causes extra {extra_holy_damage} holy damage.")
        elif self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 2:
          extra_holy_damage = random.randint(6, 8)
          damage_dealt += extra_holy_damage
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}, due to Shield of Righteous, this attack causes extra {extra_holy_damage} holy damage.")
        else:
          self.game.display_battle_info(f"{self.name} uses Hammer of Anger on {other_hero.name}.")
        return other_hero.take_damage(damage_dealt, attack_type, self)

    def crusader_strike(self, other_hero, attack_type="NA"):
        accuracy = 100  # Crusader strike has 100% chance to activate the wrath of crusader effect
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          if self.status['wrath_of_crusader'] == False:
            self.status['wrath_of_crusader'] = True
            agility_before_increasing = self.agility
            agility_increased_amount_by_wrath_of_crusader_single = math.ceil(self.original_agility * 0.75)  # Increase hero's agility by 75%
            self.agility_increased_amount_by_wrath_of_crusader = self.agility_increased_amount_by_wrath_of_crusader + agility_increased_amount_by_wrath_of_crusader_single  # Defense increase accumulated
            self.agility = self.agility + agility_increased_amount_by_wrath_of_crusader_single
            self.wrath_of_crusader_stacks += 1
            self.wrath_of_crusader_duration = 3  # Effect lasts for 2 rounds
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike, {self.name} is in Wrath of Crusader status, their agility has increased from {agility_before_increasing} to {self.agility}.")
          else:
            if self.wrath_of_crusader_stacks < 2: # wrath of crusader effect can stack for two times.
              agility_before_increasing = self.agility
              agility_increased_amount_by_wrath_of_crusader_single = math.ceil(self.original_agility * 0.75)  # Increase hero's agility by 75%
              self.agility_increased_amount_by_wrath_of_crusader = self.agility_increased_amount_by_wrath_of_crusader + agility_increased_amount_by_wrath_of_crusader_single  # Defense increase accumulated
              self.agility = self.agility + agility_increased_amount_by_wrath_of_crusader_single
              self.wrath_of_crusader_stacks += 1
              self.wrath_of_crusader_duration = 3  # Effect lasts for 2 rounds
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike, {self.name} is in Wrath of Crusader status, their agility has increased from {agility_before_increasing} to {self.agility}.")
            else:
              self.wrath_of_crusader_duration = 3
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike. Wrath of Crusader buff duration refreshed.")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Crusader Strike.")
        basic_damage = 20
        variation = random.randint(-2, 2)
        damage_dealt = basic_damage + variation
        return other_hero.take_damage(damage_dealt, attack_type, self)

    def flash_of_light(self, other_hero):
        variation = random.randint(0, 2)
        healing_amount_base = 19
        healing_amount = healing_amount_base + variation
        if self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 1:
          extra_healing = random.randint(5, 7)
          healing_amount = healing_amount_base + extra_healing
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}, due to Wrath of Crusader, this spell gains an additional {extra_healing} healing.")
        elif self.status['wrath_of_crusader'] == True and self.wrath_of_crusader_stacks == 2:
          extra_healing = random.randint(11, 13)
          healing_amount = healing_amount_base + extra_healing
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}, due to Wrath of Crusader, this spell gains an additional {extra_healing} healing.")
        else:
          self.game.display_battle_info(f"{self.name} casts Flash of Light on {other_hero.name}.")
        return other_hero.take_healing(healing_amount)


    # Part B — battle analysis -------------------------------------------------
    def analyse_battle_strategy(self, battle_information, opponents, allies):
        """Choose Retribution's action around a two-stack Wrath rhythm.

        Crusader Strike is the dependable anti-armour attack and the only way
        to build Wrath.  At two stacks, Wrath makes Flash of Light markedly
        stronger and can make Hammer of Anger worthwhile despite defence.
        """
        skills = battle_information["skills"]
        hammer = skills.get("Hammer of Anger")
        strike = skills.get("Crusader Strike")
        heal = skills.get("Flash of Light")
        ranged = self._paladin_legal_targets(hammer, opponents, allies)
        melee = self._paladin_legal_targets(strike, opponents, allies)
        heal_targets = self._paladin_legal_targets(heal, opponents, allies)
        ally_info = [item for item in battle_information["allies"] if item["hero"] in heal_targets]
        enemy_info = [item for item in battle_information["opponents"] if item["hero"] in ranged]
        melee_info = [item for item in battle_information["opponents"] if item["hero"] in melee]
        weakest_ally = self._paladin_lowest_health(ally_info)
        priority_enemy = self._paladin_priority_enemy(enemy_info)
        weakest_enemy = self._paladin_lowest_health(enemy_info)
        wrath_stacks = self.wrath_of_crusader_stacks
        wrath_needs_refresh = self.wrath_of_crusader_duration <= 1

        # 1. Execute a softer high-threat Mage, Rogue, or Priest at or below
        # 20% HP with ranged Hammer of Anger.
        soft_finisher = [
            item for item in enemy_info
            if item["faculty"] in {"Mage", "Rogue", "Priest"}
            and item["hp_ratio"] <= 0.20
            and item["defense"] <= self.damage
        ]
        if hammer and soft_finisher:
            return self._paladin_choose(
                hammer, self._paladin_priority_enemy(soft_finisher)["hero"]
            )

        # 2. Emergency healing is the only priority that interrupts the
        # build-up rhythm before two Wrath stacks are ready.
        if heal and weakest_ally and weakest_ally["hp_ratio"] <= 0.28:
            return self._paladin_choose(heal, weakest_ally["hero"])

        # 3. Build the first and second Wrath stacks, or refresh their short
        # duration, using stable ~20 damage that ignores target defence.
        if strike and melee_info and (wrath_stacks < 2 or wrath_needs_refresh):
            tank = max(melee_info, key=lambda item: (item["defense"], item["hero"].name))
            return self._paladin_choose(strike, tank["hero"])

        # 4. At two stacks, use the greatly strengthened Flash of Light to
        # recover a wounded ally before the buff expires.
        if heal and wrath_stacks >= 2 and weakest_ally and weakest_ally["hp_ratio"] <= 0.60:
            return self._paladin_choose(heal, weakest_ally["hero"])

        # 5. At two stacks, finish a vulnerable opponent with the strengthened
        # ranged Hammer, including a reachable rear target.
        if hammer and wrath_stacks >= 2 and weakest_enemy and weakest_enemy["hp_ratio"] <= 0.42:
            return self._paladin_choose(hammer, weakest_enemy["hero"])

        # 6. A two-stack Hammer is also preferred when its expected post-defence
        # damage matches Crusader Strike's stable output against a priority foe.
        if hammer and wrath_stacks >= 2 and priority_enemy:
            expected_hammer = max(0, self.damage - priority_enemy["defense"]) + 7
            if expected_hammer >= 20:
                return self._paladin_choose(hammer, priority_enemy["hero"])

        # 7. Otherwise Crusader Strike remains the best answer to an armoured
        # Warrior or Paladin in the legal melee lane.
        armoured = [item for item in melee_info if item["faculty"] in {"Warrior", "Paladin"}]
        if strike and armoured:
            return self._paladin_choose(strike, max(armoured, key=lambda item: item["defense"])["hero"])

        # Deterministic fallback when none of the seven priorities apply.
        if strike and melee_info:
            return self._paladin_choose(strike, self._paladin_priority_enemy(melee_info)["hero"])
        if hammer and weakest_enemy:
            return self._paladin_choose(hammer, weakest_enemy["hero"])
        return self._paladin_choose(next(iter(skills.values()), None))

    # Part C — return the chosen action to the live API adapter ----------------
    def ai_choose_skill(self, opponents, allies):
        information = self.collect_battle_information(opponents, allies)
        return self.analyse_battle_strategy(information, opponents, allies)

    def ai_choose_target(self, chosen_skill, opponents, allies):
        return self.preset_target

class Paladin_Protection(Paladin):

    major = "Protection"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
            self.provides_holy_aura = True
            self.add_skill(Skill(self, "Hammer of Revenge", self.hammer_of_revenge, target_type = "single", skill_type= "damage", attack_type = "ranged_instant"))
            self.add_skill(Skill(self, "Shield of Righteous", self.shield_of_righteous, target_type = "single", skill_type= "damage", attack_type = "melee", independent_effect_action=self.independent_shield_of_righteous))
            self.add_skill(Skill(self, "Heroric Charge", self.heroric_charge, target_type = "single", skill_type= "damage", attack_type = "ranged_instant", is_control_skill = True, independent_effect_action=self.independent_heroric_charge))
            self.add_skill(Skill(self, "Holy Aura", self.holy_aura, target_type = "self", skill_type= "effect", target_qty=0, is_passive=True))

    def holy_aura(self):
        """Passive marker for the round-start aura handled by Game/status effects."""
        return None

    def hammer_of_revenge(self, other_hero, attack_type="NA"):
        variation = random.randint(-4, -1)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.defense
        damage_dealt = max(damage_dealt, 0)

        # Check if there is debuff on self
        hero_status_activated = [key for key, value in self.status.items() if value == True]
        set_comb = set(self.list_status_debuff_magic) | set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) | set(self.list_status_debuff_physical)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        #print(f"{RED}DEBUG Message: status_list_for_action = {status_list_for_action}{RESET}")
        if len(status_list_for_action) == 0:
          extra_holy_damage = 0
        elif len(status_list_for_action) == 1:
          extra_holy_damage = random.randint(3, 5)
          self.game.display_battle_info(f"{self.name} is furying due to the debuff they suffered, Hammer of Revenge will have a higher damage.")
        elif len(status_list_for_action) == 2:
          extra_holy_damage = random.randint(6, 8)
          self.game.display_battle_info(f"{self.name} is highly furying due to the debuff they suffered, Hammer of Revenge will have a higher damage.")
        elif len(status_list_for_action) >= 3:
          extra_holy_damage = random.randint(9, 11)
          self.game.display_battle_info(f"{self.name} is extremly furying due to the debuff they suffered, Hammer of Revenge will have a higher damage.")
        damage_dealt += extra_holy_damage 

        if self.status['shield_of_righteous'] == True and other_hero.status['hammer_of_revenge'] == False:
          other_hero.status['hammer_of_revenge'] = True
          other_hero.hammer_of_revenge_duration = 3   # Effect lasts for 2 rounds
          damage_before_reducing = other_hero.damage
          other_hero.damage_reduced_amount_by_hammer_of_revenge = round(other_hero.original_damage * 0.2)  # Reduce target's damage by 20%
          other_hero.damage = other_hero.damage - other_hero.damage_reduced_amount_by_hammer_of_revenge
          self.game.display_battle_info(f"{self.name} uses Hammer of Revenge on {other_hero.name}, due to Shield of Righteous, {other_hero.name}'s damage is reduced from {damage_before_reducing} to {other_hero.damage}.")
        else:
          self.game.display_battle_info(f"{self.name} uses Hammer of Revenge on {other_hero.name}.")
        return other_hero.take_damage(damage_dealt, attack_type, self)

    def shield_of_righteous(self, other_hero, attack_type="NA"):
        accuracy = 100  # Shield of Righteous has a 100% chance to activate the defense increasing effect
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          if self.status['shield_of_righteous'] == False:
            self.status['shield_of_righteous'] = True
            defense_before_increasing = self.defense
            defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.original_defense * 0.15)  # Increase hero's defense by 15%
            self.defense_increased_amount_by_shield_of_righteous = self.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
            self.defense = self.defense + defense_increased_amount_by_shield_of_righteous_single
            self.shield_of_righteous_stacks += 1
            self.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous, defense of {self.name} has increased from {defense_before_increasing} to {self.defense}.")
          else:
            if self.shield_of_righteous_stacks < 2: #shield of righteous effect can stack for two times.
              defense_before_increasing = self.defense
              defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.original_defense * 0.15)  # Increase hero's defense by 15%
              self.defense_increased_amount_by_shield_of_righteous = self.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
              self.defense = self.defense + defense_increased_amount_by_shield_of_righteous_single
              self.shield_of_righteous_stacks += 1
              self.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous, defense of {self.name} has increased from {defense_before_increasing} to {self.defense}.")
            else:
              self.shield_of_righteous_duration = 3
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous. Shield of Righteous buff duration refreshed")
        else:
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield of Righteous.")
        basic_damage = 20
        variation = random.randint(-2, 2)
        damage_dealt = basic_damage + variation
        return other_hero.take_damage(damage_dealt, attack_type, self)

    def heroric_charge(self, other_hero, attack_type="NA"):
        basic_damage = round((self.damage - other_hero.defense) * 1)
        variation = random.randint(-1, 1)
        actual_damage = max(1, basic_damage + variation)
        basic_healing_heroric_charge = 32
        variation = random.randint(-2, 2)
        actual_healing = basic_healing_heroric_charge + variation

        if other_hero.is_immunity_condition_control == True:
           if other_hero.status['magic_casting'] == True:
             result = self.interrupt_magic_casting(other_hero)
             return f"{result}. {other_hero.take_damage(actual_damage, attack_type, self)}."
           else:
             return f"{other_hero.take_damage(actual_damage, attack_type, self)}."
        else:
          other_hero.status['scoff'] = True
          for debuff in other_hero.debuffs:
            if debuff.name == "Scoff":
              other_hero.debuffs.remove(debuff)
              other_hero.buffs_debuffs_recycle_pool.append(debuff)
          for debuff in other_hero.buffs_debuffs_recycle_pool:
            if debuff.name == "Scoff" and debuff.initiator == self:
                other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                debuff.duration = 1
                other_hero.add_debuff(debuff)   
          else:
              debuff = Debuff(
                  name='Scoff',
                  duration=1,
                  initiator=self,
                  effect=1
              )
              other_hero.add_debuff(debuff)

          if other_hero.status['magic_casting'] == True:
            result = self.interrupt_magic_casting(other_hero)
            for skill in self.skills:
              if skill.name == "Heroric Charge":
                skill.if_cooldown = True
                skill.cooldown = 3
            return f"Holy light showers {self.name}. {self.take_healing(actual_healing)}. {self.name} casts Heroric Charge on {other_hero.name}. {result}. {other_hero.take_damage(actual_damage, attack_type, self)}. {other_hero.name} developed a deep hatred toward {self.name}."
          else:
            for skill in self.skills:
              if skill.name == "Heroric Charge":
                skill.if_cooldown = True
                skill.cooldown = 3
            return f"Holy light showers {self.name}. {self.take_healing(actual_healing)}. {self.name} casts Heroric Charge on {other_hero.name}. {other_hero.take_damage(actual_damage, attack_type, self)}. {other_hero.name} developed a deep hatred toward {self.name}."

    def analyse_battle_strategy(self, battle_information, opponents, allies):
        skills = battle_information["skills"]
        hammer, shield, charge = (
            skills.get("Hammer of Revenge"), skills.get("Shield of Righteous"), skills.get("Heroric Charge")
        )
        enemies = battle_information["opponents"]
        melee = [item for item in enemies if item["hero"] in self._paladin_legal_targets(shield, opponents, allies)]
        charge_targets = [item for item in enemies if item["hero"] in self._paladin_legal_targets(charge, opponents, allies)]
        weakest = self._paladin_lowest_health(enemies)
        priority = self._paladin_priority_enemy(enemies)
        casters = [item for item in charge_targets if "magic_casting" in item["active_statuses"]]
        revenge_debuffs = (
            set(self.list_status_debuff_magic)
            | set(self.list_status_debuff_bleeding)
            | set(self.list_status_debuff_disease)
            | set(self.list_status_debuff_toxic)
            | set(self.list_status_debuff_physical)
        )
        revenge_debuff_count = len(
            battle_information["self"]["active_statuses"] & revenge_debuffs
        )

        # 1. Interrupt casting before any other priority.
        if charge and casters:
            return self._paladin_choose(charge, self._paladin_priority_enemy(casters)["hero"])

        # 2. At three self-debuffs, Hammer of Revenge reaches its strongest
        # damage band; convert that pressure into an aggressive ranged hit.
        if hammer and priority and revenge_debuff_count >= 3:
            return self._paladin_choose(hammer, priority["hero"])

        # 3. At two debuffs, use the growing Hammer bonus to finish or pressure
        # a vulnerable high-priority foe rather than spending another tank turn.
        if hammer and priority and revenge_debuff_count >= 2 and priority["hp_ratio"] <= .55:
            return self._paladin_choose(hammer, priority["hero"])

        # 4. Heal and apply Scoff when the tank is threatened.
        if charge and battle_information["self"]["hp_ratio"] <= .42 and charge_targets:
            return self._paladin_choose(charge, self._paladin_priority_enemy(charge_targets)["hero"])

        # 5. Establish or refresh the defensive shield through legal melee.
        if shield and melee and (self.shield_of_righteous_stacks < 2 or self.shield_of_righteous_duration <= 1):
            return self._paladin_choose(shield, max(melee, key=lambda item: (item["defense"], item["damage"]))["hero"])

        # 6. While shielded, Revenge also reduces a priority enemy's damage.
        if hammer and priority and self.status["shield_of_righteous"]:
            return self._paladin_choose(hammer, priority["hero"])

        # 7. Control threats, then retain defence and ranged revenge fallback.
        if charge and charge_targets:
            return self._paladin_choose(charge, self._paladin_priority_enemy(charge_targets)["hero"])
        if shield and melee:
            return self._paladin_choose(shield, max(melee, key=lambda item: item["defense"])["hero"])
        if hammer and weakest:
            return self._paladin_choose(hammer, weakest["hero"])
        return self._paladin_choose(next(iter(skills.values()), None))

    def ai_choose_skill(self, opponents, allies):
        return self.analyse_battle_strategy(self.collect_battle_information(opponents, allies), opponents, allies)

        heal, blast, protection = (
            skills.get("Purify Healing"), skills.get("Holy Blast"), skills.get("Shield of Protection")
        )
        allies_info, enemies = battle_information["allies"], battle_information["opponents"]
        weakest_ally = self._paladin_lowest_health(allies_info)
        curable = set(self.list_status_debuff_magic) | set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) | set(self.list_status_debuff_physical) | set(self.list_status_debuff_toxic)
        afflicted = [item for item in allies_info if item["active_statuses"] & curable]
        self_afflicted = bool(battle_information["self"]["active_statuses"] & curable)
        # 1. Cleanse/protect self; 2. save critical allies; 3. remove ally debuffs.
        if protection and (battle_information["self"]["hp_ratio"] <= .40 or self_afflicted):
            return self._paladin_choose(protection)
        if heal and weakest_ally and weakest_ally["hp_ratio"] <= .38:
            return self._paladin_choose(heal, weakest_ally["hero"])
        if heal and afflicted:
            return self._paladin_choose(heal, self._paladin_lowest_health(afflicted)["hero"])
        # 4. Prefer Holy Blast's two-target value; 5. sustain an injured ally.
        if blast and len(enemies) >= 2:
            ordered = sorted(enemies, key=lambda item: ({"Mage": 0, "Rogue": 0, "Priest": 1}.get(item["faculty"], 2), item["hp_ratio"], item["hero"].name))
            return self._paladin_choose(blast, [item["hero"] for item in ordered[:2]])
        if heal and weakest_ally and weakest_ally["hp_ratio"] <= .62:
            return self._paladin_choose(heal, weakest_ally["hero"])
        # 6. Ranged pressure; 7. protection when no viable target remains.
        if blast and enemies:
            return self._paladin_choose(blast, [self._paladin_priority_enemy(enemies)["hero"]])
        if protection:
            return self._paladin_choose(protection)
        return self._paladin_choose(next(iter(skills.values()), None))

    def ai_choose_skill(self, opponents, allies):
        return self.analyse_battle_strategy(self.collect_battle_information(opponents, allies), opponents, allies)


class Paladin_Holy(Paladin):

    major = "Holy"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
            self.add_skill(Skill(self, "Purify Healing", self.purify_healing, target_type = "single", skill_type= "healing"))
            self.add_skill(Skill(self, "Holy Blast", self.holy_blast, target_type = "multi", skill_type= "damage", attack_type = "ranged_projectile", target_qty= 2))
            self.add_skill(Skill(self, "Shield of Protection", self.shield_of_protection, target_type = "single", skill_type= "buffs", target_qty= 0))

    def purify_healing(self, other_hero):
        variation = random.randint(-2, 2)
        basic_healing = 25
        actual_healing = basic_healing + variation
        hero_status_activated = [key for key, value in other_hero.status.items() if value == True]
        set_comb = set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) | set(self.list_status_debuff_toxic)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        #print(status_list_for_action)

        if other_hero.status['purify_healing'] == False:
            other_hero.status['purify_healing'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Purify Healing" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 2   # Effect lasts for 2 rounds
                    other_hero.add_buff(buff)
                    break
            else:        
              buff = Buff(
                  name='Purify Healing',
                  duration = 2,
                  initiator = self,
                  effect = 1.0
              )
              other_hero.add_buff(buff)
            
        else:
            for buff in other_hero.buffs:
                if buff.name == "Purify Healing" and buff.initiator == self:
                    buff.duration = 2   # Refresh effect
        
        self.game.display_battle_info(f"{self.name} uses Purify Healing on {other_hero.name}.")
        if status_list_for_action:
          random.shuffle(status_list_for_action)
          self.game.status_dispeller.dispell_status([status_list_for_action[0]], other_hero)
        return other_hero.take_healing(actual_healing)

    def holy_blast(self, other_heros, attack_type="NA"):
        if not isinstance(other_heros, list):
          other_heros = [other_heros]
        results = []
        basic_damage = 22
        variation = random.randint(-2, 3)
        actual_damage = basic_damage + variation
        for i, opponent in enumerate(other_heros):
          #print(f"i = {i}")
          if i == 0:
              damage_multiplier = 3 / 3  # 100% damage for the first target
          else:
              damage_multiplier = 2 / 3  # 66.67% damage for subsequent targets
          damage = math.ceil(actual_damage * damage_multiplier)
          #print(f"damage = {damage}")
          self.game.display_battle_info(f"{self.name} casts Holy Blast at {opponent.name}.")
          results.append(opponent.take_damage(damage, attack_type, self))
        return "\n".join(results)

    def shield_of_protection(self):
        hero_status_activated = [key for key, value in self.status.items() if value == True]
        set_comb = set(self.list_status_debuff_magic)  | set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) |set(self.list_status_debuff_physical)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        self.game.display_battle_info(f"{self.name} uses Shield of Protection.")
        self.game.status_dispeller.dispell_status(status_list_for_action, self)

        if self.status['shield_of_protection'] == False:
            self.status['shield_of_protection'] = True
        self.shield_of_protection_duration = 2
        for skill in self.skills:
            if skill.name == "Shield of Protection":
              skill.if_cooldown = True
              skill.cooldown = 3
        return f"{YELLOW}{self.name} is immune towards all damage.{RESET}"

    # Part B — battle analysis -------------------------------------------------
    def analyse_battle_strategy(self, battle_information):
        skills = battle_information["skills"]
        heal = skills.get("Purify Healing")
        blast = skills.get("Holy Blast")
        protection = skills.get("Shield of Protection")
        allies = battle_information["allies"]
        enemies = battle_information["opponents"]
        weakest = self._paladin_lowest_health(allies)
        curable = set(self.list_status_debuff_magic) | set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) | set(self.list_status_debuff_physical) | set(self.list_status_debuff_toxic)
        afflicted = [item for item in allies if item["active_statuses"] & curable]
        # 1. Protect/cleanse self; 2. heal critical; 3. dispel ally.
        if protection and (battle_information["self"]["hp_ratio"] <= .40 or battle_information["self"]["active_statuses"] & curable): return protection, None
        if heal and weakest and weakest["hp_ratio"] <= .38: return heal, weakest["hero"]
        if heal and afflicted: return heal, self._paladin_lowest_health(afflicted)["hero"]
        # 4. Two-target blast; 5. sustain; 6. single pressure; 7. fallback.
        if blast and len(enemies) >= 2: return blast, [item["hero"] for item in sorted(enemies, key=lambda item: (item["hp_ratio"], item["hero"].name))[:2]]
        if heal and weakest and weakest["hp_ratio"] <= .62: return heal, weakest["hero"]
        if blast and enemies: return blast, [self._paladin_priority_enemy(enemies)["hero"]]
        return protection or next(iter(skills.values()), None), None

    # Part C — return the chosen action to the live API adapter ----------------
    def ai_choose_skill(self, opponents, allies):
        self.holy_battle_information = self.collect_battle_information(opponents, allies)
        skill, self.preset_target = self.analyse_battle_strategy(self.holy_battle_information)
        return skill
