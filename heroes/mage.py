import math
import random
from heroes import *
from skills import *
from heroes.summon_factory import SummonFactory



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

    def __init__(self, sys_init, name, group, is_player_controlled, major, position="front"):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty, position=position)
            self.hero_damage_type = "elemental"

class Mage_Comprehensiveness(Mage):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled, position="front"):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major, position=position)
        self.preset_target = None
        self.add_skill(Skill(self, "Fireball", self.fireball, target_type = "single", skill_type= "damage", attack_type = "ranged_projectile",damage_nature = "magical", damage_type = "fire"))
        self.add_skill(Skill(self, "Arcane Missiles", self.arcane_missiles, target_type = "multi", skill_type= "damage", attack_type = "ranged_projectile", target_qty= 2, damage_nature = "magical", damage_type = "arcane"))
        self.add_skill(Skill(self, "Frost Bolt", self.frost_bolt, target_type = "single", skill_type= "damage", attack_type = "ranged_projectile", damage_nature = "magical", damage_type = "frost"))

    @staticmethod
    def _fireball_direct_damage(damage, fire_resistance, variation):
        """Pure pre-formation damage shared by execution and audited preview."""
        return max(damage + variation - fire_resistance, 0)

    @staticmethod
    def _arcane_missiles_direct_damage(damage, arcane_resistance, variation):
        """Pure per-target damage for Arcane's one shared variation roll."""
        return math.ceil((damage + variation - arcane_resistance) * 2 / 3)

    @staticmethod
    def _frost_bolt_direct_damage(damage, frost_resistance, variation):
        """Pure pre-formation damage shared by execution and audited preview."""
        return max(
            math.ceil((damage + variation - frost_resistance) * 4 / 5),
            0,
        )

    def audited_direct_damage_range(self, skill_name, target):
        """Return the five-skill MVP's RNG-free direct input range.

        This method deliberately excludes evasion, deterministic prevention,
        formation adjustment, absorption, and linked damage. The adapter owns
        those current-battle facts and applies them without executing a skill.
        """
        if skill_name == "Fireball":
            calculate = self._fireball_direct_damage
            resistance = target.fire_resistance
            variations = (-5, 5)
        elif skill_name == "Arcane Missiles":
            calculate = self._arcane_missiles_direct_damage
            resistance = target.arcane_resistance
            variations = (-3, 3)
        elif skill_name == "Frost Bolt":
            calculate = self._frost_bolt_direct_damage
            resistance = target.frost_resistance
            variations = (-2, 2)
        else:
            return None
        values = [
            max(0, calculate(self.damage, resistance, variation))
            for variation in variations
        ]
        return min(values), max(values)

    def fireball(self, other_hero, attack_type="NA"):
        variation = random.randint(-5, 5)
        damage_dealt = self._fireball_direct_damage(
            self.damage, other_hero.fire_resistance, variation
        )
        self.game.display_battle_info(f"{self.name} casts Fireball at {other_hero.name}.")
        return other_hero.take_damage(damage_dealt, attack_type, self)

    def arcane_missiles(self, other_heros, attack_type="NA"):
        if not isinstance(other_heros, list):
          other_heros = [other_heros]
        results = []
        variation = random.randint(-3, 3)
        selected_opponents = other_heros
        for opponent in selected_opponents:
            damage_dealt = self._arcane_missiles_direct_damage(
                self.damage, opponent.arcane_resistance, variation
            )
            self.game.display_battle_info(f"{self.name} casts Arcane Missiles at {opponent.name}.")
            results.append(opponent.take_damage(damage_dealt, attack_type, self))
        return "\n".join(results)

    def frost_bolt(self, other_hero, attack_type="NA"):
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
        damage_dealt = self._frost_bolt_direct_damage(
            self.damage, other_hero.frost_resistance, variation
        )
        return other_hero.take_damage(damage_dealt, attack_type, self)

    # Battling Strategy_________________________________________________________

    # Part A — battle information collection ----------------------------------
    def _mage_comprehensiveness_combatant_snapshot(self, hero):
        """Collect live elemental and control facts used by this Mage."""
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
            "defense": hero.defense,
            "agility": hero.agility,
            "original_agility": hero.original_agility,
            "fire_resistance": hero.fire_resistance,
            "frost_resistance": hero.frost_resistance,
            "arcane_resistance": hero.arcane_resistance,
            "active_statuses": active_statuses,
            "cold_duration": getattr(hero, "cold_duration", 0),
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
        """Build the Mage's current-turn view from engine-owned state."""
        opponent_snapshots = [
            self._mage_comprehensiveness_combatant_snapshot(hero)
            for hero in opponents
        ]
        ally_snapshots = [
            self._mage_comprehensiveness_combatant_snapshot(hero)
            for hero in allies
        ]
        alive_opponents = [item for item in opponent_snapshots if item["alive"]]
        damageable_opponents = [
            item
            for item in alive_opponents
            if not (
                item["active_statuses"]
                & {"shield_of_protection", "anti_magic_shield"}
            )
        ]
        return {
            "self": self._mage_comprehensiveness_combatant_snapshot(self),
            "allies": [item for item in ally_snapshots if item["alive"]],
            "opponents": alive_opponents,
            "damageable_opponents": damageable_opponents,
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
    def _mage_priority_target(candidates):
        """Prefer lower HP, then an efficient rank and stable name."""
        return min(
            candidates,
            key=lambda item: (
                item["hp_ratio"],
                0 if item["position"] == "front" else 1,
                -item["agility"],
                item["hero"].name,
            ),
        )

    @staticmethod
    def _mage_single_target_skill(target, fireball, frost_bolt):
        """Choose between the two single attacks from current resistance."""
        if fireball and frost_bolt:
            if target["frost_resistance"] < target["fire_resistance"]:
                return frost_bolt
            return fireball
        return fireball or frost_bolt

    @staticmethod
    def _mage_arcane_targets(candidates):
        return sorted(
            candidates,
            key=lambda item: (
                item["arcane_resistance"],
                item["hp_ratio"],
                0 if item["position"] == "front" else 1,
                item["hero"].name,
            ),
        )[:2]

    def analyse_battle_strategy(self, battle_information):
        """Choose one legal Mage action without duplicating damage formulas."""
        skills = battle_information["skills"]
        opponents = battle_information["opponents"]
        damageable = battle_information["damageable_opponents"] or opponents

        fireball = skills.get("Fireball")
        arcane_missiles = skills.get("Arcane Missiles")
        frost_bolt = skills.get("Frost Bolt")

        if not opponents:
            return None, None

        # 1. Concentrate a single spell on an opponent already under kill
        # pressure, using the lower of its current Fire/Frost resistances.
        low_health = [item for item in damageable if item["hp_ratio"] <= 0.25]
        if low_health and (fireball or frost_bolt):
            target = self._mage_priority_target(low_health)
            return (
                self._mage_single_target_skill(target, fireball, frost_bolt),
                target["hero"],
            )

        # 2. Apply Cold to the fastest viable opponent that does not already
        # have it. Recasting while Cold is active would not refresh duration.
        cold_candidates = [
            item for item in damageable if "cold" not in item["active_statuses"]
        ]
        cold_is_already_controlling = any(
            "cold" in item["active_statuses"] for item in damageable
        )
        if frost_bolt and cold_candidates and not cold_is_already_controlling:
            target = min(
                cold_candidates,
                key=lambda item: (
                    -item["agility"],
                    item["frost_resistance"],
                    item["hp_ratio"],
                    item["hero"].name,
                ),
            )
            return frost_bolt, target["hero"]

        # 3. Arcane Missiles is deliberately reserved for a complete pair of
        # distinct living targets; 1v1 never relies on adapter target filling.
        if arcane_missiles and len(damageable) >= 2:
            targets = self._mage_arcane_targets(damageable)
            return arcane_missiles, [item["hero"] for item in targets]

        # 4. Exploit the lower current Fire/Frost resistance on the most urgent
        # target once Cold and multi-target priorities are exhausted.
        if fireball or frost_bolt:
            target = min(
                damageable,
                key=lambda item: (
                    min(item["fire_resistance"], item["frost_resistance"]),
                    item["hp_ratio"],
                    0 if item["position"] == "front" else 1,
                    item["hero"].name,
                ),
            )
            return (
                self._mage_single_target_skill(target, fireball, frost_bolt),
                target["hero"],
            )

        # 5. If only Arcane Missiles remains available, keep its required pair.
        if arcane_missiles and len(opponents) >= 2:
            targets = self._mage_arcane_targets(opponents)
            return arcane_missiles, [item["hero"] for item in targets]

        # 6. A hard-immunity state is still target-legal. Preserve a stable
        # legal single-target fallback when no damageable alternative exists.
        fallback_target = self._mage_priority_target(opponents)["hero"]
        if fireball or frost_bolt:
            target_state = next(
                item for item in opponents if item["hero"] is fallback_target
            )
            return (
                self._mage_single_target_skill(
                    target_state, fireball, frost_bolt
                ),
                fallback_target,
            )
        if arcane_missiles and len(opponents) >= 2:
            targets = self._mage_arcane_targets(opponents)
            return arcane_missiles, [item["hero"] for item in targets]
        return None, None

    # Part C — return the chosen action to the live API adapter ----------------
    def ai_choose_skill(self, opponents, allies):
        self.mage_comprehensiveness_battle_information = (
            self.collect_battle_information(opponents, allies)
        )
        skill, target = self.analyse_battle_strategy(
            self.mage_comprehensiveness_battle_information
        )
        self.preset_target = target
        return skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        return self.preset_target

class Mage_Water(Mage):

    major = "Water"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Summon Water Elemental", self.summon_water_elemental, target_type="single", skill_type="summon", target_qty= 0, damage_nature = "magical", damage_type = "water"))
        self.add_skill(Skill(self, "Water Arrow", self.water_arrow, target_type = "single", skill_type= "damage_healing", damage_nature = "magical", damage_type = "water"))
        self.add_skill(Skill(self, "Aqua Ring", self.aqua_ring, target_type = "single", skill_type= "healing"))

    def summon_water_elemental(self):
        unit_group = self.group
        unit_duration = 3  # The summoning unit will last for 3 rounds
        unit_race = 'element'
        waterelemental = SummonFactory.create_summon(
        name="WaterElemental",
        sys_init=self.sys_init,
        group=unit_group,
        master=self,
        duration=unit_duration,
        summon_unit_race=unit_race,
        is_player_controlled=False
        )
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
      if other_hero.is_summoned == True and other_hero.master == self: # boost effect
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
                  other_hero.agility = other_hero.agility + agility_increased_amount_by_water_arrow_single
                  self.game.display_battle_info(f"{self.name} uses Water Arrow on {other_hero.name} again, {other_hero.name} has received energy from water. {other_hero.name}'s damage and agility has increased, {other_hero.name} will stay one more round in the battle field.")
                  return f"{other_hero.name}'s damage has increased from {damage_before_increasing} to {other_hero.damage}, agility has increased from {agility_before_increasing} to {other_hero.agility}."
        else:
           return f"{self.name} uses Water Arrow on {other_hero.name} again, but {other_hero.name} cannot be futher strenthened, {other_hero.name} will stay one more round in the battle field."

      else: # damage effect
        variation = random.randint(-2, 2)
        actual_damage = math.ceil((self.damage - other_hero.nature_resistance) * 2/5)
        damage_dealt = actual_damage + variation
        damage_dealt = max(damage_dealt, 0) # Ensure damage dealt is at least 0
        self.game.display_battle_info(f"{self.name} casts Water Arrow at {other_hero.name}.")
        return f"{other_hero.take_damage(damage_dealt)}"
    
    def aqua_ring(self, other_hero):
        variation = random.randint(-2, 2)
        basic_healing = 20
        actual_healing = basic_healing + variation
        hero_status_activated = [key for key, value in other_hero.status.items() if value == True]
        set_comb = set(self.list_status_debuff_magic) |  set(self.list_status_debuff_toxic)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        #print(status_list_for_action)

        if other_hero.status['aqua_ring'] == False:
            other_hero.status['aqua_ring'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Aqua Ring" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 2   # Effect lasts for 2 rounds
                    other_hero.add_buff(buff)
                    break
            else:        
              buff = Buff(
                  name='Aqua Ring',
                  duration = 2,
                  initiator = self,
                  effect = 1.0
              )
              other_hero.add_buff(buff)
            
        else:
            for buff in other_hero.buffs:
                if buff.name == "Aqua Ring" and buff.initiator == self:
                    buff.duration = 2   # Refresh effect
        
        self.game.display_battle_info(f"{self.name} uses Aqua Ring on {other_hero.name}.")
        if status_list_for_action:
          random.shuffle(status_list_for_action)
          self.game.status_dispeller.dispell_status([status_list_for_action[0]], other_hero)
        return other_hero.take_healing(actual_healing)
    
class Mage_Frost(Mage):

    major = "Frost"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Frost Bolt", self.frost_bolt, target_type = "single", skill_type= "damage", damage_nature = "magical", damage_type = "frost"))
        self.add_skill(Skill(self, "Blizzard", self.blizzard, "multi", skill_type= "damage", target_qty=3, is_instant_skill = False, damage_nature = "magical", damage_type = "frost"))
        self.add_skill(Skill(self, "Glacier", self.glacier, "single", skill_type= "damage_healing", damage_nature = "magical", damage_type = "frost"))

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
    
    def blizzard(self, other_heroes):
        if not isinstance(other_heroes, list):
          other_heroes = [other_heroes]

        if self.status['bless_of_frost']:
          if self.status['magic_casting'] == False:
            self.game.display_battle_info(f"{self.name} receives bless of frost and will cast Blizzard instantly!")
            self.status['bless_of_frost'] = False  # Reset the status after use
            results = []
            variation = random.randint(-2, 2)
            actual_damage = self.damage + variation
            selected_opponents = other_heroes
            for opponent in selected_opponents:
              if opponent.hp > 0:
                damage_dealt = round((actual_damage - opponent.frost_resistance) * 2/3)
                self.game.display_battle_info(f"{self.name} casts Blizzard at {opponent.name}.")
                results.append(opponent.take_damage(damage_dealt))
            return "\n".join(results)
          elif self.status['magic_casting'] == True:
            self.status['magic_casting'] = False
            self.game.display_battle_info(f"From bless of frost, {self.name} casts a much powerful Blizzard!")
            self.status['bless_of_frost'] = False  # Reset the status after use
            results = []
            variation = random.randint(-2, 2)
            actual_damage = self.damage + variation
            selected_opponents = other_heroes
            for opponent in selected_opponents:
              if opponent.hp > 0:
                damage_dealt = actual_damage - opponent.frost_resistance
                self.game.display_battle_info(f"{self.name} casts Blizzard at {opponent.name}.")
                results.append(opponent.take_damage(damage_dealt))
            return "\n".join(results)

        if self.status['magic_casting'] == False:
          self.status['magic_casting'] = True
          self.game.display_battle_info(f"{self.name} is casting Blizzard.")
          self.magic_casting_duration = 1
          for skill in self.skills:
            if skill.name == "Blizzard":
              return self.magic_casting(skill, other_heroes)

        elif self.status['magic_casting'] == True:
          self.status['magic_casting'] = False
          results = []
          variation = random.randint(-2, 2)
          actual_damage = self.damage + variation
          selected_opponents = other_heroes
          for opponent in selected_opponents:
            if opponent.hp > 0:
              damage_dealt = round((actual_damage - opponent.frost_resistance) * 2/3)
              self.game.display_battle_info(f"{self.name} casts Blizzard at {opponent.name}.")
              results.append(opponent.take_damage(damage_dealt))
          return "\n".join(results)
        
    def glacier(self, other_hero, target_type):
        for skill in self.skills:
          if skill.name == "Glacier":
            skill.if_cooldown = True
            skill.cooldown = 3
        if other_hero.status['glacier'] == False:
            other_hero.status['glacier'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Glacier" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 2   # Effect lasts for 2 rounds
                    other_hero.add_buff(buff)
                    return f"{self.name} casts Glacier on {other_hero.name}. {other_hero.name} is frozen and cannot move."

            buff = Buff(
                name='Glacier',
                duration = 2,
                initiator = self,
                effect = 0.15
            )
            other_hero.add_buff(buff)
            return f"{self.name} casts Glacier on {other_hero.name}. {other_hero.name} is frozen and cannot move."
        else:
            return f"{self.name} tries to use Glacier on {other_hero.name}. But {other_hero.name} has already been frozen."
        
class Mage_Arcane(Mage):

    major = "Arcane"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Arcane Missiles", self.arcane_missiles, target_type = "multi", skill_type= "damage", target_qty= 2, damage_nature = "magical", damage_type = "arcane"))
        self.add_skill(Skill(self, "Arcane Shock", self.arcane_shock, target_type = "single", skill_type= "damage", damage_nature = "magical", damage_type = "arcane"))
        self.add_skill(Skill(self, "Anti Magic Shield", self.anti_magic_shield, "single", skill_type= "damage_healing", damage_nature = "magical", damage_type = "arcane"))

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
    
    def arcane_shock(self, other_hero):
        variation = random.randint(-5, 5)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.arcane_resistance
        damage_dealt = max(damage_dealt, 0)
        hero_status_activated = [key for key, value in other_hero.status.items() if value == True]
        set_comb = set(self.list_status_buff_magic)
        equal_status = set(hero_status_activated) & set_comb
        status_list_for_action = list(equal_status)
        self.game.display_battle_info(f"{self.name} casts Arcane Shock at {other_hero.name}, which dispells all their positive magic effect.")
        for status in status_list_for_action:
          self.game.status_dispeller.dispell_status(status, other_hero)
        return other_hero.take_damage(damage_dealt)
    
    def anti_magic_shield(self, other_hero, target_type):
        if other_hero.status['anti_magic_shield'] == False:
            other_hero.status['anti_magic_shield'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
              if buff.name == "Anti Magic Shield" and buff.initiator == self:
                other_hero.buffs_debuffs_recycle_pool.remove(buff)
                buff.duration = 2   # Effect lasts for 2 rounds
                other_hero.add_buff(buff)
                return f"{self.name} casts Anti Magic Shield on {other_hero.name}, {other_hero.name} is immuned against all magic effect."
            buff = Buff(
                name='Anti Magic Shield',
                duration = 2,
                initiator = self,
                effect = 0.10
            )
            other_hero.add_buff(buff)
            return f"{self.name} casts Anti Magic Shield on {other_hero.name}, {other_hero.name} is immuned against all magic effect."
        else:
           return f"{self.name} Tries to cast Anti Magic Shield on {other_hero.name}, {other_hero.name} is already under Anti Magic Shield."

class Mage_Fire(Mage):

    major = "Fire"

    def __init__(self, sys_init, name, group, is_player_controlled):
        super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
        self.add_skill(Skill(self, "Fireball", self.fireball, target_type = "single", skill_type= "damage", damage_nature = "magical", damage_type = "fire"))
        self.add_skill(Skill(self, "Giant Fireball", self.giant_fireball, target_type = "single", skill_type= "damage", is_instant_skill = False, damage_nature = "magical", damage_type = "fire"))
        self.add_skill(Skill(self, "Scorchbrand", self.scorchbrand, target_type = "single", skill_type= "damage", damage_nature = "magical", damage_type = "fire"))

    def fireball(self, other_hero):
        variation = random.randint(-5, 5)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.fire_resistance
        damage_dealt = max(damage_dealt, 0)
        self.game.display_battle_info(f"{self.name} casts Fireball at {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def giant_fireball(self, other_hero):
        accuracy = 25  # Giant fire ball has 25% chance to split a small fire ball
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        is_giant_fireball_split = False
        if roll <= accuracy:
          is_giant_fireball_split = True
        if self.status['magic_casting'] == False:
          self.status['magic_casting'] = True
          self.game.display_battle_info(f"{self.name} is casting Giant Fireball.")
          self.magic_casting_duration = 1
          for skill in self.skills:
            if skill.name == "Giant Fireball":
              return self.magic_casting(skill, other_hero)
            
        elif self.status['magic_casting'] == True:
          self.status['magic_casting'] = False
          variation = random.randint(-5, 5)
          actual_damage = self.damage + variation
          damage_dealt = math.ceil(1.35 * actual_damage - other_hero.fire_resistance)
          damage_dealt = max(damage_dealt, 0)
          if is_giant_fireball_split:
            if other_hero.allies_self_excluded:
              results = []
              damage_splitted_fireball = math.ceil(0.25* damage_dealt)
              damage_giant_fireball_after_split = math.ceil(0.75* damage_dealt)
              extra_opponent = random.sample(other_hero.allies_self_excluded, 1)
              self.game.display_battle_info(f"{self.name} casts Giant Fireball at {other_hero.name}. A small fireball splites and flies towards {extra_opponent[0].name}.")
              results.append(other_hero.take_damage(damage_giant_fireball_after_split))
              results.append(extra_opponent[0].take_damage(damage_splitted_fireball))
              return "\n".join(results)
            else:
               self.game.display_battle_info(f"{self.name} casts Giant Fireball at {other_hero.name}.")
               return other_hero.take_damage(damage_dealt)
          else:
             self.game.display_battle_info(f"{self.name} casts Giant Fireball at {other_hero.name}.")
             return other_hero.take_damage(damage_dealt)

    def scorchbrand(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.fire_resistance)*(1/2))
        damage_dealt = max(damage_dealt, 0)
        if damage_dealt > 0:
          other_hero.scorchbrand_continuous_damage = round((actual_damage - other_hero.fire_resistance)*(1/3))
        else:
          other_hero.scorchbrand_continuous_damage = random.randint(3, 8)
        if other_hero.status['scorchbrand'] == False:
          other_hero.status['scorchbrand'] = True
          for debuff in other_hero.buffs_debuffs_recycle_pool:
                if debuff.name == "Scorchbrand" and debuff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(debuff)
                    debuff.duration = 3   # Effect lasts for 2 rounds
                    other_hero.add_debuff(debuff)
                    fire_resistance_before_reducing = other_hero.fire_resistance
                    other_hero.fire_resistance_reduced_amount_by_scorchbrand = round(other_hero.original_fire_resistance * debuff.effect)  # Reduce target's damage by 18%
                    other_hero.fire_resistance = other_hero.fire_resistance - other_hero.fire_resistance_reduced_amount_by_scorchbrand
                    self.game.display_battle_info(f"{self.name} casts Scorchbrand on {other_hero.name}. {other_hero.name} is burned and their fire resistance is reduced from {fire_resistance_before_reducing} to {other_hero.fire_resistance}.")
                    return other_hero.take_damage(damage_dealt)
          debuff = Debuff(
                name='Scorchbrand',
                duration = 3, # Effect lasts for 1-3 rounds
                initiator = self,
                effect = 0.18
            )
          other_hero.add_debuff(debuff)
          fire_resistance_before_reducing = other_hero.fire_resistance
          other_hero.fire_resistance_reduced_amount_by_scorchbrand = round(other_hero.original_fire_resistance * debuff.effect)  # Reduce target's damage by 18%
          other_hero.fire_resistance = other_hero.fire_resistance - other_hero.fire_resistance_reduced_amount_by_scorchbrand
          self.game.display_battle_info(f"{self.name} casts Scorchbrand on {other_hero.name}. {other_hero.name} is burned and their fire resistance is reduced from {fire_resistance_before_reducing} to {other_hero.fire_resistance}.")
          return other_hero.take_damage(damage_dealt)
        else:
          self.game.display_battle_info(f"{self.name} casts Scorchbrand on {other_hero.name}. {other_hero.name} is burned.")
          return other_hero.take_damage(damage_dealt)
