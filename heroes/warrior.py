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

class Warrior(Hero):
    
    faculty = "Warrior"

    def __init__(self, sys_init, name, group, is_player_controlled, major, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty, position=position)
            self.hero_damage_type = "physical"

class Warrior_Comprehensiveness(Warrior):
    
    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
            self.damage_type = "physical"
            self.probability_armor_breaker = 0
            self.probability_shield_bash = 0
            self.probability_slash = 0
            self.preset_target = None
            self.add_skill(Skill(self, "Slash", self.slash, target_type = "single", skill_type= "damage",))
            self.add_skill(Skill(self, "Shield Bash", self.shield_bash, target_type = "single", skill_type= "damage", capable_interrupt_magic_casting = True))
            self.add_skill(Skill(self, "Armor Breaker", self.armor_breaker, target_type = "single", skill_type= "damage"))

    def slash(self, other_hero):
      variation = random.randint(-3, 3)
      actual_damage = self.damage + variation
      damage_dealt = actual_damage - other_hero.defense
      damage_dealt = max(damage_dealt, 0)
      # Consider different situations
      if other_hero.status['bleeding_slash'] == True:
        self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash.")
      else:
        if other_hero.status['armor_breaker'] == True:
          accuracy = 100  # Bleeding effect has a 85% chance to succeed
          roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
          if roll <= accuracy:
            other_hero.status['bleeding_slash'] = True
            other_hero.status['normal'] = False
            other_hero.bleeding_slash_duration = other_hero.armor_breaker_stacks + 1
            other_hero.bleeding_slash_continuous_damage = random.randint(8, 12)
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash, {other_hero.name} got injured and start bleeding because of their broken armor.")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash")
        else:
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Slash.")
      # apply damage
      return other_hero.take_damage(damage_dealt)

    def shield_bash(self, other_hero):
        accuracy = 70  # Shield Bash has a 70% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if other_hero.status['magic_casting'] == True:
          result = self.interrupt_magic_casting(other_hero)
          if roll <= accuracy:
              other_hero.status['stunned'] = True
              other_hero.status['normal'] = False
              other_hero.stun_duration += 1
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned. {result}")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash. {result}")
        else:
          if roll <= accuracy:
            other_hero.status['stunned'] = True
            other_hero.status['normal'] = False
            other_hero.stun_duration += 1
            self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned.")
          else:
              self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash")
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/2)
            # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
          # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def armor_breaker(self, other_hero):
        damage_dealt = self.random_in_range((8, 14))  # Small damage
        if other_hero.status['armor_breaker'] == True:
          if other_hero.armor_breaker_stacks < 3:
              defense_before_reducing = other_hero.defense
              defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
              other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.armor_breaker_stacks += 1
              other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
              self.game.display_battle_info(f"{self.name} uses Armor Breaker on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")
          else:
              other_hero.armor_breaker_duration = 2  # Refresh armor breaker effect
              self.game.display_battle_info(f"{self.name} uses Armor Breaker on {other_hero.name}, but {other_hero.name}'s Armor Breaker effect cannot be further stacked. Armor Breaker duration refreshed")
        else:
          other_hero.status['armor_breaker'] = True
          defense_before_reducing = other_hero.defense
          defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
          other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.armor_breaker_stacks += 1
          other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
          self.game.display_battle_info(f"{self.name} uses Armor Breaker on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")

        return other_hero.take_damage(damage_dealt)

    # Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_armor_breaker = 0.25
      self.probability_shield_bash = 0.25
      self.probability_slash = 0.5

    def strategy_1(self):
      self.probability_armor_breaker = 0
      self.probability_shield_bash = 1
      self.probability_slash = 0

    def strategy_2(self):
      self.probability_armor_breaker = 0.9
      self.probability_shield_bash = 0
      self.probability_slash = 0.1

    def strategy_3(self):
      self.probability_armor_breaker = 0.5
      self.probability_shield_bash = 0
      self.probability_slash = 0.5

    def strategy_4(self):
      self.probability_armor_breaker = 0
      self.probability_shield_bash = 0
      self.probability_slash = 1

    def strategy_5(self):
      self.probability_armor_breaker = 0
      self.probability_shield_bash = 0.5
      self.probability_slash = 0.5

    def battle_analysis(self, opponents, allies):
      # Sort hp from low to high
      sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
      sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
      sorted_allies_excludes_self = sorted_allies.copy()
      for ally in sorted_allies_excludes_self:
        if ally == self:
          sorted_allies_excludes_self.remove(ally)

      # Priority targets tackling strategy
      # 1 Slash target hp < 35%
      for opponent in sorted_opponents:
        if opponent.hp <= 0.45 * opponent.hp_max and opponent.faculty != "Warrior" and opponent.faculty != "Paladin":
          self.strategy_4()
          return opponent
        elif opponent.hp <= 0.25 * opponent.hp_max and (opponent.faculty == "Warrior" or opponent.faculty == "Paladin"):
          self.strategy_4()
          return opponent
        elif opponent.hp <= 0.55 * opponent.hp_max:
          self.strategy_5()
          return opponent

      for opponent in opponents:
        if opponent.status['magic_casting'] == True:
          self.strategy_1()
          return opponent
      for opponent in opponents:
          if opponent.status['armor_breaker'] == True and opponent.armor_breaker_stacks < 2:
            if opponent.faculty == 'Mage' or opponent.faculty == 'Rogue':
              self.strategy_4()
              return opponent
            else:
              self.strategy_3()
              return opponent
          elif opponent.status['armor_breaker'] == True and opponent.armor_breaker_stacks >= 2:
            self.strategy_4()
            return opponent

      # If no priority targets, then random choose one target and utilize corresponding strategy
      opponent = random.choice(opponents)
      if opponent.faculty == 'Mage' or opponent.faculty == 'Rogue':
        self.strategy_2()
        return opponent
      if opponent.faculty == 'Warrior' or opponent.faculty == 'Paladin':
        self.strategy_2()
        return opponent

      return opponent


    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_slash, self.probability_shield_bash, self.probability_armor_breaker]
        #available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        #chosen_skill = random.choice(available_skills)
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent

    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])
    
class Warrior_Defence(Warrior):
    
    major = "Defence"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
            self.damage_type = "physical"
            self.probability_armor_breaker = 0
            self.probability_shield_bash = 0
            self.probability_slash = 0
            self.preset_target = None
            self.add_skill(Skill(self, "Devastate", self.devastate, target_type = "single", skill_type= "damage",attack_type = "melee"))
            self.add_skill(Skill(self, "Shield Bash", self.shield_bash, target_type = "single", skill_type= "damage", attack_type = "melee", capable_interrupt_magic_casting = True))
            self.add_skill(Skill(self, "Thunder Pot", self.thunder_pot, target_type = "multi", skill_type= "damage", target_qty=2, attack_type = "ranged_projectile", is_control_skill = True, independent_effect_action=self.independent_shield_lash))

    def shield_bash(self, other_hero, attack_type="NA"):
        if other_hero.status['magic_casting'] == True:
          interrupt_magic_result = self.interrupt_magic_casting(other_hero)
          other_hero.status['stunned'] = True
          other_hero.status['normal'] = False
          other_hero.stun_duration += 1
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned. {interrupt_magic_result}")
        else:
          other_hero.status['stunned'] = True
          other_hero.status['normal'] = False
          other_hero.stun_duration += 1
          self.game.display_battle_info(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned.")
        for skill in self.skills:
            if skill.name == "Shield Bash":
              skill.if_cooldown = True
              skill.cooldown = 3
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/4)
        damage_dealt = max(damage_dealt, 1)
        return other_hero.take_damage(damage_dealt, attack_type, self)

    def devastate(self, other_hero, attack_type="NA"):
        variation = random.randint(-1, 1)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.75)
        damage_dealt = max(damage_dealt, 1)
        if other_hero.status['armor_breaker'] == True:
          if other_hero.armor_breaker_stacks == 1:
            defense_before_reducing = other_hero.defense
            defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
            other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
            other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
            other_hero.armor_breaker_stacks += 1
            other_hero.armor_breaker_duration = 2  # armor breaker Effect lasts for 2 rounds
            self.game.display_battle_info(f"{self.name} uses Devastate on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")
          else:
            other_hero.armor_breaker_duration = 2  # Refresh armor breaker effect
            self.game.display_battle_info(f"{self.name} uses Devastate on {other_hero.name}, refreshes their duration of Armor Breaker")
        else:
          other_hero.status['armor_breaker'] = True
          defense_before_reducing = other_hero.defense
          defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
          other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.armor_breaker_stacks += 1
          other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
          self.game.display_battle_info(f"{self.name} uses Devastate on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")

        return other_hero.take_damage(damage_dealt, attack_type, self)

    def thunder_pot(self, other_heroes, attack_type="NA"):
        self.status['shield_lash'] = True
        self.fire_resistance_boost_amount['shield_lash'] = 45
        self.frost_resistance_boost_amount['shield_lash'] = 45
        self.death_resistance_boost_amount['shield_lash'] = 45
        self.nature_resistance_boost_amount['shield_lash'] = 45

        self.fire_resistance = self.fire_resistance + self.fire_resistance_boost_amount['shield_lash']
        self.frost_resistance = self.frost_resistance + self.frost_resistance_boost_amount['shield_lash']
        self.death_resistance = self.death_resistance + self.death_resistance_boost_amount['shield_lash']
        self.nature_resistance = self.nature_resistance + self.nature_resistance_boost_amount['shield_lash']
        for skill in self.skills:
            if skill.name == "Thunder Pot":
                skill.if_cooldown = True
                skill.cooldown = 3

        if not isinstance(other_heroes, list):
            other_heroes = [other_heroes]
        results = []
        selected_opponents = other_heroes
        for opponent in selected_opponents:
            basic_damage = round((self.damage - opponent.defense) * 1/3)
            variation = random.randint(-1, 1)
            actual_damage = max(1, basic_damage + variation)

            if opponent.is_immunity_condition_control == True:
                if opponent.status['magic_casting'] == True:
                    interrupt_magic_result = self.interrupt_magic_casting(opponent)
                    self.game.display_battle_info(f"{self.name} casts Thunder Pot on {opponent.name}. {interrupt_magic_result}")
                    results.append(opponent.take_damage(actual_damage, attack_type, self))
                else:
                    self.game.display_battle_info(f"{self.name} casts Thunder Pot on {opponent.name}.")
                    results.append(opponent.take_damage(actual_damage, attack_type, self))
            else:
                opponent.status['scoff'] = True
                for debuff in opponent.debuffs:
                    if debuff.name == "Scoff":
                        opponent.debuffs.remove(debuff)
                        opponent.buffs_debuffs_recycle_pool.append(debuff)
                for debuff in opponent.buffs_debuffs_recycle_pool:
                    if debuff.name == "Scoff" and debuff.initiator == self:
                        opponent.buffs_debuffs_recycle_pool.remove(debuff)
                        debuff.duration = 1
                        opponent.add_debuff(debuff)
                        break   
                else:
                    debuff = Debuff(
                        name='Scoff',
                        duration=1,
                        initiator=self,
                        effect=1
                    )
                    opponent.add_debuff(debuff)

                for buff in self.buffs_debuffs_recycle_pool:
                        if buff.name == "Shield Lash" and buff.initiator == self:
                            self.buffs_debuffs_recycle_pool.remove(buff)
                            buff.duration = 2
                            self.add_buff(buff)   
                            break
                else:
                    buff = Buff(
                        name='Shield Lash',
                        duration=2,
                        initiator=self,
                        effect=1
                    )
                    self.add_buff(buff)

                if opponent.status['magic_casting'] == True:
                    interrupt_magic_result = self.interrupt_magic_casting(opponent)
                    opponent.scoff_shield_lash_duration = 2
                    self.game.display_battle_info(f"{self.name} casts Thunder Pot on {opponent.name}. {interrupt_magic_result}. {self.name}'s magical resistance is boost. {opponent.name} developed a deep hatred toward {self.name}.")
                    results.append(opponent.take_damage(actual_damage, attack_type, self))
                else:
                    opponent.scoff_shield_lash_duration = 2
                    self.game.display_battle_info(f"{self.name} casts Thunder Pot on {opponent.name}. {self.name}'s magical resistance is boost. {opponent.name} developed a deep hatred toward {self.name}.")
                    results.append(opponent.take_damage(actual_damage, attack_type, self))

        return "\n".join(results)
 
    # Battling Strategy_________________________________________________________

    # Part A — battle information collection ----------------------------------
    def _defence_combatant_snapshot(self, hero):
        active_statuses = {name for name, active in hero.status.items() if active}
        return {
            "hero": hero,
            "faculty": hero.faculty,
            "major": hero.major,
            "position": hero.position,
            "alive": hero.hp > 0,
            "hp_ratio": hero.hp / hero.hp_max if hero.hp_max else 0,
            "defense": hero.defense,
            "armor_breaker_stacks": getattr(hero, "armor_breaker_stacks", 0),
            "active_statuses": active_statuses,
            "buffs": [buff.name for buff in hero.buffs],
            "debuffs": [debuff.name for debuff in hero.debuffs],
            "skill_cooldowns": {
                skill.name: {
                    "available": skill.is_available and not skill.if_cooldown,
                    "rounds_remaining": skill.cooldown,
                }
                for skill in hero.skills
            },
        }

    def collect_battle_information(self, opponents, allies):
        """Collect the Defence Warrior's live, formation-authoritative state."""
        opponents_state = [
            self._defence_combatant_snapshot(hero) for hero in opponents
        ]
        allies_state = [self._defence_combatant_snapshot(hero) for hero in allies]
        alive_opponents = [item for item in opponents_state if item["alive"]]
        melee_targets = [
            item for item in alive_opponents if item["position"] == "front"
        ] or alive_opponents
        return {
            "self": self._defence_combatant_snapshot(self),
            "allies": [item for item in allies_state if item["alive"]],
            "opponents": alive_opponents,
            "melee_targets": melee_targets,
            "ranged_targets": alive_opponents,
            "formations": {
                "ally_positions": tuple(item["position"] for item in allies_state),
                "opponent_positions": tuple(item["position"] for item in opponents_state),
            },
            "skills": {
                skill.name: skill
                for skill in self.skills
                if skill.is_available and not skill.if_cooldown
            },
        }

    # Part B — battle analysis -------------------------------------------------
    @staticmethod
    def _defence_priority_target(candidates):
        threat_rank = {"Mage": 0, "Rogue": 1, "Priest": 2, "Warrior": 3, "Paladin": 4}
        return min(
            candidates,
            key=lambda item: (
                item["hp_ratio"],
                threat_rank.get(item["faculty"], 5),
                -item["defense"],
                item["hero"].name,
            ),
        )

    def analyse_battle_strategy(self, battle_information):
        """Choose one of seven Defence Warrior priorities for this turn."""
        skills = battle_information["skills"]
        melee_targets = battle_information["melee_targets"]
        ranged_targets = battle_information["ranged_targets"]
        if not ranged_targets:
            return next(iter(skills.values()), None), None

        devastate = skills.get("Devastate")
        shield_bash = skills.get("Shield Bash")
        thunder_pot = skills.get("Thunder Pot")

        # 1. Immediately interrupt and stun a reachable active caster.
        casters = [
            item for item in melee_targets if "magic_casting" in item["active_statuses"]
        ]
        if shield_bash and casters:
            return shield_bash, self._defence_priority_target(casters)["hero"]

        # 2. Use Devastate to finish a reachable opponent before it can act.
        low_health = [item for item in melee_targets if item["hp_ratio"] <= 0.30]
        if devastate and low_health:
            return devastate, self._defence_priority_target(low_health)["hero"]

        # 3. Use Thunder Pot's multi-target Scoff and resistance gain when it
        # can affect at least two live enemies, especially dangerous casters.
        priority_ranged = [
            item
            for item in ranged_targets
            if item["faculty"] in {"Mage", "Rogue", "Priest"}
            or "magic_casting" in item["active_statuses"]
        ]
        if thunder_pot and len(ranged_targets) >= 2 and priority_ranged:
            ordered = sorted(
                ranged_targets,
                key=lambda item: (
                    item not in priority_ranged,
                    item["hp_ratio"],
                    item["hero"].name,
                ),
            )
            return thunder_pot, [item["hero"] for item in ordered[:2]]

        # 4. Stun a reachable Mage or Rogue to blunt the highest immediate
        # offensive threat when an interruption is not already required.
        high_threat_melee = [
            item for item in melee_targets if item["faculty"] in {"Mage", "Rogue"}
        ]
        if shield_bash and high_threat_melee:
            return shield_bash, self._defence_priority_target(high_threat_melee)["hero"]

        # 5. Apply or build Devastate's Armor Breaker on the most heavily
        # defended reachable target.  Devastate's engine effect caps at two.
        stackable_defenders = [
            item for item in melee_targets if item["armor_breaker_stacks"] < 2
        ]
        if devastate and stackable_defenders:
            return devastate, max(
                stackable_defenders,
                key=lambda item: (item["defense"], -item["hp_ratio"], item["hero"].name),
            )["hero"]

        # 6. If no priority control target exists, use Thunder Pot to hold two
        # opponents' attention on the tank whenever it can hit both.
        if thunder_pot and len(ranged_targets) >= 2:
            ordered = sorted(
                ranged_targets,
                key=lambda item: (item["hp_ratio"], item["hero"].name),
            )
            return thunder_pot, [item["hero"] for item in ordered[:2]]

        # 7. Fall back to reliable melee pressure on the most vulnerable legal
        # target.  The adapter verifies this target before execution.
        target = self._defence_priority_target(melee_targets)["hero"]
        return devastate or shield_bash or thunder_pot, target

    # Part C — return the selected action to the live API adapter -------------
    def ai_choose_skill(self, opponents, allies):
        self.defence_battle_information = self.collect_battle_information(
            opponents, allies
        )
        skill, target = self.analyse_battle_strategy(self.defence_battle_information)
        self.preset_target = target
        return skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        return self.preset_target

class Warrior_Weapon_Master(Warrior):
    
    major = "Weapon_Master"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
            self.damage_type = "physical"
            self.probability_armor_breaker = 0
            self.probability_shield_bash = 0
            self.probability_slash = 0
            self.preset_target = None
            self.add_skill(Skill(self, "Fatal Strike", self.fatal_strike, target_type = "single", skill_type= "damage",attack_type = "melee"))
            self.add_skill(Skill(self, "Armor Crush", self.armor_crush, target_type = "single", skill_type= "damage", attack_type = "melee"))
            self.add_skill(Skill(self, "Antivenom Potion", self.antivenom_potion, target_type = "single", skill_type= "buffs", target_qty= 0))

    def fatal_strike(self, other_hero, attack_type="NA"):
      variation = random.randint(-3, 3)
      actual_damage = self.damage + variation
      damage_dealt = actual_damage - other_hero.defense
      damage_dealt = max(damage_dealt, 1)
      if not other_hero.status['fatal_strike']:
          other_hero.status['fatal_strike'] = True
          other_hero.healing_reduction_effects['fatal_strike'] = 0.7
          for debuff in other_hero.buffs_debuffs_recycle_pool:
              if debuff.name == "Fatal Strike" and debuff.initiator == self:
                  other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                  debuff.duration = 2
                  other_hero.add_debuff(debuff)
                  self.game.display_battle_info(f"{self.name} uses Fatal Strike on {other_hero.name}. The healing they receive will be reduced sharply.")
                  return other_hero.take_damage(damage_dealt, attack_type, self)
          
          debuff = Debuff(
              name='Fatal Strike',
              duration=2,
              initiator=self,
              effect=0.8
          )
          other_hero.add_debuff(debuff)
          self.game.display_battle_info(f"{self.name} uses Fatal Strike on {other_hero.name}. The healing they receive will be reduced sharply.")
          return other_hero.take_damage(damage_dealt, attack_type, self)
      else:
          self.game.display_battle_info(f"{self.name} uses Fatal Strike on {other_hero.name}.")
      return other_hero.take_damage(damage_dealt, attack_type, self)

    def armor_crush(self, other_hero, attack_type="NA"):
        #damage_dealt_stack_0 = self.random_in_range((6, 10))  # Small damage
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.55) 
        damage_dealt = max(damage_dealt, 1) # damage dealt stack 0
        
        if other_hero.status['armor_breaker'] == True:
          if other_hero.armor_breaker_stacks == 1:
              damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.65)
              damage_dealt = max(damage_dealt, 1) # damage dealt stack 1
              defense_before_reducing = other_hero.defense
              defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
              other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.armor_breaker_stacks += 1
              other_hero.armor_breaker_duration = 2  # armor breaker Effect lasts for 2 rounds
              other_hero.status['wound_armor_crush'] = True
              other_hero.wound_armor_crush_duration = 2
              agility_before_reduce = other_hero.agility
              other_hero.agility_reduced_amount_by_wound_armor_crush = int(other_hero.agility * 0.2)
              other_hero.agility -= other_hero.agility_reduced_amount_by_wound_armor_crush
              self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}. This attack causes wound. {other_hero.name}'s agility has reduced from {agility_before_reduce} to {other_hero.agility}.")
          elif other_hero.armor_breaker_stacks == 2:
              damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.75)
              damage_dealt = max(damage_dealt, 1) # damage dealt stack 2
              defense_before_reducing = other_hero.defense
              defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
              other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.armor_breaker_stacks += 1
              other_hero.armor_breaker_duration = 2  # armor breaker Effect lasts for 2 rounds
              other_hero.status['bleeding_armor_crush'] = True
              other_hero.bleeding_armor_crush_duration = 3
              other_hero.bleeding_armor_crush_continuous_damage = random.randint(8, 12)
              self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}. {other_hero.name} got injured and start bleeding.")
          else:
              damage_dealt = math.ceil((actual_damage - other_hero.defense) * 0.75)
              damage_dealt = max(damage_dealt, 1) # damage dealt stack >= 3
              other_hero.armor_breaker_duration = 2  # Refresh armor breaker effect
              self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, but {other_hero.name}'s Armor Breaker effect cannot be further stacked. Armor Breaker duration refreshed")
        else:
          other_hero.status['armor_breaker'] = True
          defense_before_reducing = other_hero.defense
          defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
          other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
          other_hero.armor_breaker_stacks += 1
          other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
          self.game.display_battle_info(f"{self.name} uses Armor Crush on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")
        return other_hero.take_damage(damage_dealt, attack_type, self)

    def antivenom_potion(self):
        self.status['antivenom_potion'] = True
        self.poison_resistance_boost_amount['antivenom_potion'] = 45
        basic_healing = 19
        variation = random.randint(-1, 1)
        actual_healing = basic_healing + variation
        self.poison_resistance = self.poison_resistance + self.poison_resistance_boost_amount['antivenom_potion']
        
        for skill in self.skills:
            if skill.name == "Antivenom Potion":
              skill.if_cooldown = True
              skill.cooldown = 3

        for buff in self.buffs_debuffs_recycle_pool:
                if buff.name == "Antivenom Potion" and buff.initiator == self:
                    self.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 2
                    self.add_buff(buff)   
                    break
        else:
            buff = Buff(
                name='Antivenom Potion',
                duration=2,
                initiator=self,
                effect=1
            )
            self.add_buff(buff)

        hero_status_activated = [key for key, value in self.status.items() if value == True]
        set_comb = set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_toxic)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        if status_list_for_action:
          self.game.display_battle_info(f"{self.name} drinks Antivenom Potion.")
          self.game.status_dispeller.dispell_status(status_list_for_action, self)
          return f"{self.take_healing(actual_healing)}. {self.name}'s poison resistance is boost."
        return f"{self.name} drinks Antivenom Potion. {self.take_healing(actual_healing)}. {self.name}'s poison resistance is boost."


    # Battling Strategy_________________________________________________________

    # Part A — battle information collection ----------------------------------
    def _weapon_master_combatant_snapshot(self, hero):
        """Return the combat facts Weapon Master strategy is allowed to inspect.

        The API adapter owns formation assignment and target validation.  The
        engine exposes that authoritative formation state on each hero's
        ``position`` field, so strategy reads positions rather than duplicating
        formation IDs or frontend layout rules here.
        """
        active_statuses = {
            name for name, active in hero.status.items() if active
        }
        return {
            "hero": hero,
            "faculty": hero.faculty,
            "major": hero.major,
            "position": hero.position,
            "alive": hero.hp > 0,
            "hp": hero.hp,
            "hp_max": hero.hp_max,
            "hp_ratio": hero.hp / hero.hp_max if hero.hp_max else 0,
            "defense": hero.defense,
            "original_defense": hero.original_defense,
            "armor_breaker_stacks": getattr(hero, "armor_breaker_stacks", 0),
            "active_statuses": active_statuses,
            "buffs": [buff.name for buff in hero.buffs],
            "debuffs": [debuff.name for debuff in hero.debuffs],
            "skill_cooldowns": {
                skill.name: {
                    "available": skill.is_available and not skill.if_cooldown,
                    "rounds_remaining": skill.cooldown,
                }
                for skill in hero.skills
            },
        }

    def collect_battle_information(self, opponents, allies):
        """Collect the current, engine-authoritative state for one AI turn."""
        opponent_snapshots = [
            self._weapon_master_combatant_snapshot(hero) for hero in opponents
        ]
        ally_snapshots = [
            self._weapon_master_combatant_snapshot(hero) for hero in allies
        ]
        alive_opponents = [item for item in opponent_snapshots if item["alive"]]
        alive_allies = [item for item in ally_snapshots if item["alive"]]
        living_front_opponents = [
            item for item in alive_opponents if item["position"] == "front"
        ]

        # This exactly matches battle_api.adapter._valid_target_ids for the
        # Weapon Master's melee damage skills.  When no front defender remains,
        # rear opponents become reachable.
        reachable_opponents = living_front_opponents or alive_opponents
        return {
            "self": self._weapon_master_combatant_snapshot(self),
            "allies": alive_allies,
            "opponents": alive_opponents,
            "reachable_opponents": reachable_opponents,
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
    def _weapon_master_priority_target(candidates):
        """Prefer a lower-health, higher-threat target without random choices."""
        threat_rank = {"Mage": 0, "Rogue": 1, "Priest": 2, "Warrior": 3, "Paladin": 4}
        return min(
            candidates,
            key=lambda item: (
                item["hp_ratio"],
                threat_rank.get(item["faculty"], 5),
                -item["defense"],
                item["hero"].name,
            ),
        )

    def analyse_battle_strategy(self, battle_information):
        """Choose a Weapon Master action from a small, explainable rule set.

        The returned target is always drawn from the formation-legal melee
        pool.  The API adapter remains the final authority and validates this
        choice again before it resolves the skill.
        """
        skills = battle_information["skills"]
        reachable = battle_information["reachable_opponents"]
        self_state = battle_information["self"]

        if not reachable:
            return next(iter(skills.values()), None), None

        fatal_strike = skills.get("Fatal Strike")
        armor_crush = skills.get("Armor Crush")
        antivenom = skills.get("Antivenom Potion")

        # 1. Finish a reachable, low-health opponent with Fatal Strike.
        low_health = [item for item in reachable if item["hp_ratio"] <= 0.35]
        if fatal_strike and low_health:
            return fatal_strike, self._weapon_master_priority_target(low_health)["hero"]

        # 2. Stabilise: cure toxic effects (and their related bleeding effects)
        # or recover from critical health whenever Antivenom is ready.
        removable_statuses = (
            set(self.list_status_debuff_toxic) | set(self.list_status_debuff_bleeding)
        )
        if antivenom and (
            self_state["hp_ratio"] <= 0.35
            or self_state["active_statuses"] & removable_statuses
        ):
            return antivenom, None

        # 3. Against a team with a living Priest, apply healing reduction to a
        # reachable target that does not already have Fatal Strike.
        enemy_has_healer = any(
            item["faculty"] == "Priest" for item in battle_information["opponents"]
        )
        unmarked_targets = [
            item for item in reachable if "fatal_strike" not in item["active_statuses"]
        ]
        if fatal_strike and enemy_has_healer and unmarked_targets:
            return fatal_strike, self._weapon_master_priority_target(unmarked_targets)["hero"]

        # 4. Strip defence from a reachable Warrior or Paladin before spending
        # attacks on lower-defence targets.  Three stacks is the engine cap.
        armored_frontliners = [
            item
            for item in reachable
            if item["faculty"] in {"Warrior", "Paladin"}
            and item["armor_breaker_stacks"] < 3
        ]
        if armor_crush and armored_frontliners:
            target = max(
                armored_frontliners,
                key=lambda item: (item["defense"], -item["hp_ratio"], item["hero"].name),
            )
            stacks = target["armor_breaker_stacks"]
            if fatal_strike and stacks == 1:
                # Owner rule: reinforce once 65% of the time, otherwise apply
                # Fatal Strike's healing-reduction pressure.
                return (
                    armor_crush if random.random() < 0.65 else fatal_strike,
                    target["hero"],
                )
            if fatal_strike and stacks == 2:
                # Owner rule: at two stacks, reinforce and Fatal Strike are
                # equally likely choices.
                return (
                    armor_crush if random.random() < 0.50 else fatal_strike,
                    target["hero"],
                )
            return armor_crush, target["hero"]

        # 5. Focus the reachable high-threat Mage or Rogue.
        high_threat = [
            item for item in reachable if item["faculty"] in {"Mage", "Rogue"}
        ]
        if fatal_strike and high_threat:
            return fatal_strike, self._weapon_master_priority_target(high_threat)["hero"]

        # 6. Continue Armor Crush on another reachable, stackable defender.
        stackable = [item for item in reachable if item["armor_breaker_stacks"] < 3]
        if armor_crush and stackable:
            return armor_crush, max(
                stackable,
                key=lambda item: (item["defense"], -item["hp_ratio"], item["hero"].name),
            )["hero"]

        # 7. A deterministic damage fallback keeps this specialization from
        # handing target choice to the adapter's random missing-target fallback.
        fallback_target = self._weapon_master_priority_target(reachable)["hero"]
        return fatal_strike or armor_crush or next(iter(skills.values())), fallback_target

    # Part C — return the chosen action to the live API adapter ----------------
    def ai_choose_skill(self, opponents, allies):
        self.weapon_master_battle_information = self.collect_battle_information(
            opponents, allies
        )
        skill, target = self.analyse_battle_strategy(
            self.weapon_master_battle_information
        )
        self.preset_target = target
        return skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        # Targetless Antivenom is executed by the adapter without a target.
        return self.preset_target

class Warrior_Berserker(Warrior):

    major = "Berserker"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
        self.damage_type = "physical"
        self.preset_target = None
        self.blood_frenzy_duration = 0
        self.agility_increased_amount_by_blood_frenzy = 0
        self.defense_decreased_amount_by_blood_frenzy = 0

        # 技能
        self.add_skill(Skill(self, "Moon Slash", self.moon_slash, target_type="multi", skill_type="damage", target_qty=2, attack_type = "ranged_instant"))
        self.add_skill(Skill(self, "Warlust", self.warlust, target_type="single", skill_type="buffs", target_qty=0))
        self.add_skill(Skill(self, "Strike of Meteorite", self.strike_of_meteorite, target_type="single", skill_type="damage", attack_type = "melee", capable_interrupt_magic_casting=True))

    # ========== 特殊状态：Blood Frenzy ==========
    def trigger_blood_frenzy(self):
        if self.status['blood_frenzy']:
            return False

        hp_percent = self.hp / self.hp_max
        roll = random.randint(1, 100)

        # Preserve the live ``Hero.take_damage`` probability bands while
        # consolidating their implementation in this single activation path.
        if hp_percent <= 0.1:
            activate = True
        elif hp_percent <= 0.25 and roll <= 75:
            activate = True
        elif hp_percent <= 0.5 and roll <= 50:
            activate = True
        else:
            activate = False

        if activate:
            self.status['blood_frenzy'] = True
            self.blood_frenzy_duration = 2
            self.agility_increased_amount_by_blood_frenzy = 20
            self.agility += self.agility_increased_amount_by_blood_frenzy
            self.defense_decreased_amount_by_blood_frenzy = round(
                self.defense / 2
            )
            defense_after_decreasing = max(
                0,
                self.defense
                - self.defense_decreased_amount_by_blood_frenzy,
            )
            self.defense = defense_after_decreasing
            return True
        return False

    def blood_frenzy_effect(self, damage_dealt):
        """每次攻击吸血"""
        if self.status['blood_frenzy'] and damage_dealt > 0:
            heal_amount = int(damage_dealt * 0.3)
            self.take_healing(heal_amount)
            self.game.display_battle_info(f"{self.name} drains {heal_amount} HP from Blood Frenzy!")

    # ========== 技能 1：Moon Slash ========== 
    # attack 2 targets, cause bleeding if target is armor broken
    def moon_slash(self, other_heroes, attack_type="NA"):
        if not isinstance(other_heroes, list):
          other_heroes = [other_heroes]
        results = []
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        selected_opponents = other_heroes
        for opponent in selected_opponents:
            damage_dealt = math.ceil((actual_damage - opponent.defense) * 2/3)
            damage_dealt = max(damage_dealt, 1)
            self.game.display_battle_info(f"{self.name} uses Moon Slash at {opponent.name}.")
            results.append(opponent.take_damage(damage_dealt, attack_type, self))
            if self.status['blood_frenzy']:
               blood_drain = int(damage_dealt * 0.3)
               results.append(f"{self.name} is draining blood due to Blood Frenzy. {self.take_healing(blood_drain)}")
            if opponent.status['armor_breaker']:
                opponent.status['bleeding_moon_slash'] = True
                opponent.bleeding_moon_slash_duration = 2
                opponent.bleeding_moon_slash_continuous_damage = random.randint(6, 10)
                moon_slash_debuff = next(
                    (
                        debuff
                        for debuff in opponent.debuffs
                        if debuff.name == "Moon Slash"
                    ),
                    None,
                )
                if moon_slash_debuff is None:
                    moon_slash_debuff = next(
                        (
                            debuff
                            for debuff in opponent.buffs_debuffs_recycle_pool
                            if debuff.name == "Moon Slash"
                        ),
                        None,
                    )
                    if moon_slash_debuff is not None:
                        opponent.buffs_debuffs_recycle_pool.remove(
                            moon_slash_debuff
                        )
                        opponent.add_debuff(moon_slash_debuff)
                    else:
                        moon_slash_debuff = Debuff(
                            name="Moon Slash",
                            duration=2,
                            initiator=self,
                            effect=opponent.bleeding_moon_slash_continuous_damage,
                        )
                        opponent.add_debuff(moon_slash_debuff)
                moon_slash_debuff.duration = 2
                moon_slash_debuff.initiator = self
                moon_slash_debuff.effect = (
                    opponent.bleeding_moon_slash_continuous_damage
                )
                results.append(f"{opponent.name} is bleeding!")
        return "\n".join(results)


    # ========== 技能 2：Warlust ==========
    # Remove and then immune control type debuffs and gain damage increasement buff
    def warlust(self):
        hero_status_activated = [key for key, value in self.status.items() if value == True]
        set_comb = set(self.list_status_debuff_control)  
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        self.game.display_battle_info(f"{self.name} is empowered by Warlust.")
        self.game.status_dispeller.dispell_status(status_list_for_action, self)

        if self.status['warlust'] == False:
            self.status['warlust'] = True
            self.is_immunity_condition_control = True
        self.warlust_duration = 2
        damage_before_increasing = self.damage # damage increase
        self.damage_increased_amount_by_warlust = round(self.original_damage * (1/3))  # Increase hero's damage by 30%
        self.damage = self.damage + self.damage_increased_amount_by_warlust

        for skill in self.skills:
            if skill.name == "Warlust":
              skill.if_cooldown = True
              skill.cooldown = 3
        return f"{self.name} is immune to any control skill! {self.name}'s damage increased from {damage_before_increasing} to {self.damage}."

    # ========== 技能 3：Hammer of Meteorite ==========
    # Attack single target, chance to cause armor break or weaken, interrupt magic casting
    def strike_of_meteorite(self, other_hero, attack_type="NA"):
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        damage_dealt = max(actual_damage - other_hero.defense, 0)

        # 打断施法
        if other_hero.status['magic_casting']:
            result = self.interrupt_magic_casting(other_hero)
            self.game.display_battle_info(f"{self.name} smashes {other_hero.name} with Hammer of the Meteorite! {result}")
        else:
            self.game.display_battle_info(f"{self.name} smashes {other_hero.name} with Hammer of the Meteorite!")

        # 随机触发附加效果
        roll = random.randint(1, 100)
        if roll <= 100:
            if other_hero.status['armor_breaker'] == True:
              if other_hero.armor_breaker_stacks < 3:
                  defense_before_reducing = other_hero.defense
                  defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
                  other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
                  other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
                  other_hero.armor_breaker_stacks += 1
                  other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
                  self.game.display_battle_info(f"{other_hero.name} suffers Armor Break from Hammer of the Meteorite!, their defense reduce from {defense_before_reducing} to {other_hero.defense}.")
              else:
                  other_hero.armor_breaker_duration = 2  # Refresh armor breaker effect
                  self.game.display_battle_info(f"{other_hero.name} suffers Armor Break from Hammer of the Meteorite!, but their Armor Breaker effect cannot be further stacked. Armor Breaker duration refreshed")
            else:
              other_hero.status['armor_breaker'] = True
              defense_before_reducing = other_hero.defense
              defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
              other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
              other_hero.armor_breaker_stacks += 1
              other_hero.armor_breaker_duration = 2  # Effect lasts for 2 rounds
              self.game.display_battle_info(f"{other_hero.name} suffers Armor Break from Hammer of the Meteorite, their defense reduce from {defense_before_reducing} to {other_hero.defense}.")

        if self.status['blood_frenzy']:
               blood_drain = int(damage_dealt * 0.3)
               self.game.display_battle_info(f"{self.name} is draining blood due to Blood Frenzy. {self.take_healing(blood_drain)}")
               return other_hero.take_damage(damage_dealt, attack_type, self)
        else:
          return other_hero.take_damage(damage_dealt, attack_type, self)

    # Part A — battle information collection ----------------------------------
    def _berserker_combatant_snapshot(self, hero):
        active_statuses = {name for name, active in hero.status.items() if active}
        return {
            "hero": hero,
            "faculty": hero.faculty,
            "major": hero.major,
            "position": hero.position,
            "alive": hero.hp > 0,
            "hp_ratio": hero.hp / hero.hp_max if hero.hp_max else 0,
            "defense": hero.defense,
            "armor_breaker_stacks": getattr(hero, "armor_breaker_stacks", 0),
            "active_statuses": active_statuses,
            "buffs": [buff.name for buff in hero.buffs],
            "debuffs": [debuff.name for debuff in hero.debuffs],
            "skill_cooldowns": {
                skill.name: {
                    "available": skill.is_available and not skill.if_cooldown,
                    "rounds_remaining": skill.cooldown,
                }
                for skill in hero.skills
            },
        }

    def collect_battle_information(self, opponents, allies):
        """Collect the Berserker's live, formation-authoritative state."""
        opponents_state = [
            self._berserker_combatant_snapshot(hero) for hero in opponents
        ]
        allies_state = [self._berserker_combatant_snapshot(hero) for hero in allies]
        alive_opponents = [item for item in opponents_state if item["alive"]]
        melee_targets = [
            item for item in alive_opponents if item["position"] == "front"
        ] or alive_opponents
        return {
            "self": self._berserker_combatant_snapshot(self),
            "allies": [item for item in allies_state if item["alive"]],
            "opponents": alive_opponents,
            "melee_targets": melee_targets,
            # Moon Slash is ranged instant and can select any live opponent.
            "moon_slash_targets": alive_opponents,
            "formations": {
                "ally_positions": tuple(item["position"] for item in allies_state),
                "opponent_positions": tuple(item["position"] for item in opponents_state),
            },
            "skills": {
                skill.name: skill
                for skill in self.skills
                if skill.is_available and not skill.if_cooldown
            },
        }

    # Part B — battle analysis -------------------------------------------------
    @staticmethod
    def _berserker_priority_target(candidates):
        threat_rank = {"Mage": 0, "Rogue": 1, "Priest": 2, "Warrior": 3, "Paladin": 4}
        return min(
            candidates,
            key=lambda item: (
                item["hp_ratio"],
                threat_rank.get(item["faculty"], 5),
                -item["defense"],
                item["hero"].name,
            ),
        )

    def analyse_battle_strategy(self, battle_information):
        """Choose one of seven aggressive Berserker priorities for this turn."""
        skills = battle_information["skills"]
        melee_targets = battle_information["melee_targets"]
        moon_targets = battle_information["moon_slash_targets"]
        self_state = battle_information["self"]
        if not moon_targets:
            return next(iter(skills.values()), None), None

        moon_slash = skills.get("Moon Slash")
        warlust = skills.get("Warlust")
        meteorite = skills.get("Strike of Meteorite")

        # 1. Interrupt an active caster the Berserker can reach in melee.
        casters = [
            item for item in melee_targets if "magic_casting" in item["active_statuses"]
        ]
        if meteorite and casters:
            return meteorite, self._berserker_priority_target(casters)["hero"]

        # 2. Finish a reachable low-health opponent with the stronger melee
        # strike before it can recover or act.
        low_health = [item for item in melee_targets if item["hp_ratio"] <= 0.30]
        if meteorite and low_health:
            return meteorite, self._berserker_priority_target(low_health)["hero"]

        # 3. Exploit existing Armor Breaker on two targets: Moon Slash applies
        # its bleeding effect to every selected armor-broken opponent.
        armor_broken = [
            item for item in moon_targets if "armor_breaker" in item["active_statuses"]
        ]
        if moon_slash and len(moon_targets) >= 2 and armor_broken:
            ordered = sorted(
                moon_targets,
                key=lambda item: (
                    item not in armor_broken,
                    item["hp_ratio"],
                    item["hero"].name,
                ),
            )
            return moon_slash, [item["hero"] for item in ordered[:2]]

        # 4. Establish Warlust's damage increase and control immunity before a
        # multi-enemy engagement or while Blood Frenzy makes the Berserker more
        # exposed at low health.  Turn directives still handle active control.
        if warlust and "warlust" not in self_state["active_statuses"] and (
            len(moon_targets) >= 2
            or self_state["hp_ratio"] <= 0.50
            or "blood_frenzy" in self_state["active_statuses"]
        ):
            return warlust, None

        # 5. Use Strike of Meteorite to open or deepen Armor Breaker on a
        # reachable high-defence target.  Its engine effect can stack to three.
        stackable_defenders = [
            item for item in melee_targets if item["armor_breaker_stacks"] < 3
        ]
        if meteorite and stackable_defenders:
            return meteorite, max(
                stackable_defenders,
                key=lambda item: (item["defense"], -item["hp_ratio"], item["hero"].name),
            )["hero"]

        # 6. Pressure two living enemies with Moon Slash, favoring Mage/Rogue
        # targets so its ranged reach remains useful across formations.
        if moon_slash and len(moon_targets) >= 2:
            ordered = sorted(
                moon_targets,
                key=lambda item: (
                    item["faculty"] not in {"Mage", "Rogue"},
                    item["hp_ratio"],
                    item["hero"].name,
                ),
            )
            return moon_slash, [item["hero"] for item in ordered[:2]]

        # 7. Fall back to focused melee pressure on the most vulnerable legal
        # target; the adapter validates final melee legality before execution.
        target = self._berserker_priority_target(melee_targets)["hero"]
        return meteorite or moon_slash or warlust, target

    # Part C — return the selected action to the live API adapter -------------
    def ai_choose_skill(self, opponents, allies):
        self.berserker_battle_information = self.collect_battle_information(
            opponents, allies
        )
        skill, target = self.analyse_battle_strategy(
            self.berserker_battle_information
        )
        self.preset_target = target
        return skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        return self.preset_target
