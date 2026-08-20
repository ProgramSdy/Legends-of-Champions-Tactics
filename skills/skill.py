import math
import inspect
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

class Skill:
    def __init__(self, initiator, name, skill_action, target_type, skill_type, target_qty = 1, capable_interrupt_magic_casting = False, is_control_skill = False, is_instant_skill = True, damage_nature = "NA", damage_type = "NA", attack_type = "NA", independent_effect_action = None):
        self.initiator = initiator  # Reference to the hero instance who initiated the skill
        self.name = name            # Name of the skill, e.g., "Fireball"
        self.skill_action = skill_action   # This is a method reference that performs the skill's action
        self.target_type = target_type  # Indicates the targeting type ("single" or "multi")
        self.skill_type = skill_type  # Indicates the skill type ("damage" or "healing" or "damage_healing"or "effect")
        self.target_qty = target_qty  # Number of targets for the skill
        self.capable_interrupt_magic_casting = capable_interrupt_magic_casting  # Flag to indicate if the skill can interrupt magic casting
        self.is_control_skill = is_control_skill  # Flag to indicate if the skill is a control skill
        self.is_instant_skill = is_instant_skill  # Flag to indicate if the skill is instant
        self.if_cooldown = False  # Flag to indicate if the skill is on cooldown
        self.cooldown = 0  # Skill cooldown in rounds
        self.is_available = True
        self.immunity_condition_all = ['shield_of_protection', 'glacier']
        self.immunity_condition_physical = []
        self.immunity_condition_magical = ['anti_magic_shield']
        self.immunity_condition_control = ['warlust']
        self.active_state = None
        self.damage_nature = damage_nature
        self.damage_type = damage_type
        self.attack_type = attack_type
        self.independent_effect_action = independent_effect_action
        # Authoritative outcome of the most recent execution, keyed by target.
        # Consumers such as adapters must use this instead of inferring a miss
        # from unchanged HP: a successful hit can legitimately deal 0 damage.
        self.last_target_outcomes = {}
        # Immunity outcomes retain the specific engine status that authored
        # them.  Keep this separate from ``last_target_outcomes`` so existing
        # consumers of its stable string values remain compatible.
        self.last_target_outcome_reasons = {}

    def _call_skill_action(self, *args):
        """Invoke a skill while preserving legacy action signatures.

        Damage actions opt in by declaring ``attack_type``. Other existing
        actions, including those with extra positional mode values, receive
        exactly the arguments they received before UI-018.
        """
        parameters = inspect.signature(self.skill_action).parameters
        if "attack_type" in parameters:
            return self.skill_action(*args, attack_type=self.attack_type)
        return self.skill_action(*args)

    def immunity_condition_all_check(self, opponent):
        # Check for immunity to all damage
        state = self._immunity_reason(opponent, self.immunity_condition_all)
        self.active_state = state
        return state is not None

    @staticmethod
    def _immunity_reason(opponent, conditions):
        return next(
            (state for state in conditions if opponent.status[state] is True),
            None,
        )
    
    def immunity_condition_physical_check(self, opponent):
        # Check for immunity to physical damage
        for state in getattr(self, 'immunity_condition_physical', []):
            if opponent.status[state] is True:
                self.active_state = state
                return True
        return False
            
    def immunity_condition_magical_check(self, opponent):
        # Check for immunity to magical damage
        for state in getattr(self, 'immunity_condition_magical', []):
            if opponent.status[state] is True:
                self.active_state = state
                return True
        return False
    
    def immunity_condition_control_check(self, opponent):
        # Check for immunity to control effects
        for state in getattr(self, 'immunity_condition_control', []):
            if opponent.status[state] is True:
                self.active_state = state
                return True
        return False

    def evasion_check(self, opponent):
        # Calculate the chance to evade based on agility;
        if opponent.evasion_capability <= (opponent.agility * 0.5):
          evasion_chance = min(50, opponent.agility * 0.5)  # capping the evasion chance at 50%
        else:
          evasion_chance = opponent.evasion_capability
        if random.randint(1, 100) <= math.ceil(evasion_chance):
           return True
        return False
    
    def death_check(self, opponent):
       if opponent.hp <= 0:
          return True
       return False

    def resolve_targets(self, targets):
        outcomes = {
            "hit": [],
            "evaded": [],
            "immunity_condition_all": [],
            "immunity_condition_physical": [],
            "immunity_condition_magical": [],
            "immunity_condition_control": [],
            "dead": []
        }
        self.last_target_outcome_reasons = {}
        for target in targets:
            if self.death_check(target):
                outcomes["dead"].append(target)
                continue
            if self.evasion_check(target):
                outcomes["evaded"].append(target)
                continue
            if self.immunity_condition_all_check(target):
                outcomes["immunity_condition_all"].append(target)
                self.last_target_outcome_reasons[id(target)] = self._immunity_reason(
                    target, self.immunity_condition_all
                )
                continue
            if self.immunity_condition_physical_check(target):
                if self.damage_nature == "physical":
                  outcomes["immunity_condition_physical"].append(target)
                  self.last_target_outcome_reasons[id(target)] = self._immunity_reason(
                      target, self.immunity_condition_physical
                  )
                  continue
            if self.immunity_condition_magical_check(target):
                if self.damage_nature == "magical":
                  outcomes["immunity_condition_magical"].append(target)
                  self.last_target_outcome_reasons[id(target)] = self._immunity_reason(
                      target, self.immunity_condition_magical
                  )
                  continue
            if self.immunity_condition_control_check(target):
                if self.is_control_skill == True:
                  outcomes["immunity_condition_control"].append(target)
                  self.last_target_outcome_reasons[id(target)] = self._immunity_reason(
                      target, self.immunity_condition_control
                  )
                  continue
            outcomes["hit"].append(target)
        self.last_target_outcomes = {
            id(target): outcome
            for outcome, resolved_targets in outcomes.items()
            for target in resolved_targets
        }
        return outcomes

    def execute(self, opponents):
        result_message = ""
        self.last_target_outcomes = {}
        self.last_target_outcome_reasons = {}
        """
        if self.name == "Crushing Wave":
          for hero in opponents:
            print(f"{RED}Debug Skill: Hero name = {hero.name}{RESET}")
        """

        # Manage healing skills
        if self.skill_type == "healing":
            return self._call_skill_action(opponents)
       
        # Manage damage skills
        elif self.skill_type == "damage":
          if self.is_instant_skill == False and self.initiator.status['magic_casting'] == False:
            return self._call_skill_action(opponents)
          if not isinstance(opponents, list):
            opponents = [opponents]
          outcomes = self.resolve_targets(opponents)
          hits = outcomes["hit"]
          evaded = outcomes["evaded"]
          dead = outcomes["dead"]
          immune_all = outcomes["immunity_condition_all"]
          immune_phy = outcomes["immunity_condition_physical"]
          immune_mag = outcomes["immunity_condition_magical"]
          immune_ctrl = outcomes["immunity_condition_control"]

          if self.target_type == "multi": # Manage multi-targets damage skill

            # Special condition manage casting skills
            if self.name == "Rain of Fire":
               if not self.initiator.status['hell_flame']:
                  if self.initiator.status['magic_casting'] == False:
                    return self._call_skill_action(opponents)
            elif self.name == "Blizzard":
               if not self.initiator.status['bless_of_frost']:
                  if self.initiator.status['magic_casting'] == False:
                    return self._call_skill_action(opponents)

            if not hits:
              #result_message = ""
              if dead:
                target_names = ', '.join([t.name for t in dead])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} were already dead. \n"
              if evaded:
                target_names = ', '.join([t.name for t in evaded])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evaded the attack. \n"
              if immune_all:
                target_names = ', '.join([t.name for t in immune_all])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to all damage. \n"
              if immune_phy:
                target_names = ', '.join([t.name for t in immune_phy])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to physical damage. \n"
              if immune_mag:
                target_names = ', '.join([t.name for t in immune_mag])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to magical effect. \n"
              if immune_ctrl:
                target_names = ', '.join([t.name for t in immune_ctrl])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to control effect. \n"
              
              # Special Condition Cool down skills
              if self.name == "Thunder Pot":
                self.if_cooldown = True
                self.cooldown = 3
              if self.name == "Icy Squall":
                self.if_cooldown = True
                self.cooldown = 2
              if self.name == "Crushing Wave":
                self.if_cooldown = True
                self.cooldown = 2
              if self.initiator.status['magic_casting'] == True:
                self.initiator.status['magic_casting'] = False
              return result_message
            
            else:
              result_message = ""
              if dead:
                target_names = ', '.join([t.name for t in dead])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} were already dead. \n"
              if evaded:
                target_names = ', '.join([t.name for t in evaded])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evaded the attack. \n"
              if immune_all:
                target_names = ', '.join([t.name for t in immune_all])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to all damage. \n"
              if immune_phy:
                target_names = ', '.join([t.name for t in immune_phy])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to physical damage. \n"
              if immune_mag:
                target_names = ', '.join([t.name for t in immune_mag])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to magical effect. \n"
              if immune_ctrl:
                if self.name == "Heroric Charge" or self.name == "Cumbrous Axe" or self.name == "Thunder Pot":
                  target_names = ', '.join([t.name for t in immune_ctrl])
                  result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to control effect. {target_names} avoids being scoffed."
                  result_message += f" {self._call_skill_action(immune_ctrl[0])}"
                else:
                  target_names = ', '.join([t.name for t in immune_ctrl])
                  result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to control effect. \n"
              if result_message:
                self.initiator.game.display_battle_info(result_message)
              return self._call_skill_action(hits)

          elif self.target_type == "single": # Manage single target damage skill
              if not hits:
                if dead:
                  target_names = ', '.join([t.name for t in dead])
                  result_message = f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} was already dead."
                if evaded:
                  target_names = ', '.join([t.name for t in evaded])
                  result_message = f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack."
                if immune_all:
                  target_names = ', '.join([t.name for t in immune_all])
                  result_message = f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immunes to all damage."
                if immune_phy:
                  target_names = ', '.join([t.name for t in immune_phy])
                  result_message = f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immunes to physical damage."
                if immune_mag:
                  target_names = ', '.join([t.name for t in immune_mag])
                  result_message = f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immunes to magical effect."
                if immune_ctrl:
                  #print(f"{RED}Debug Skill: immunity control!{RESET}")
                  if self.name == "Heroric Charge" or self.name == "Cumbrous Axe" or self.name == "Thunder Pot":
                    target_names = ', '.join([t.name for t in immune_ctrl])
                    result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to control effect. {target_names} avoids being scoffed."
                    result_message += f" {self._call_skill_action(immune_ctrl[0])}"
                  else:
                    target_names = ', '.join([t.name for t in immune_ctrl])
                    result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to control effect."
                # Special Condition
                if self.initiator.status['magic_casting'] == True:
                    self.initiator.status['magic_casting'] = False
                if self.independent_effect_action is not None:
                  effect_message = self.independent_effect_action(self)
                  if effect_message:
                    result_message += f" {effect_message}"
                if self.name == "Shadow Word Insanity" or self.name == "Curse of Fear" or self.name == "Shield Bash" or self.name == "Heroric Charge" or self.name == "Cumbrous Axe" or self.name == "Thunder Pot":
                  self.if_cooldown = True
                  self.cooldown = 3
                if self.name == "Pestilence":
                  self.if_cooldown = True
                  self.cooldown = 2
                if result_message:
                 return result_message
                #else:
                   #print(f"{RED}Debug Skill: skill name = {self.name}{RESET}")
              else:
                return self._call_skill_action(hits[0])

        # Manage damage healing skill
        elif self.skill_type == "damage_healing":

          # Special Condition
          if self.name == "Glacier":
            self.if_cooldown = True
            self.cooldown = 3

          if opponents in self.initiator.allies:
            self.last_target_outcomes[id(opponents)] = "ally"
            return self._call_skill_action(opponents, 'ally')
          else:
            if not self.evasion_check(opponents):
              self.last_target_outcomes[id(opponents)] = "hit"
              return self._call_skill_action(opponents, 'opponent')
            else:
              self.last_target_outcomes[id(opponents)] = "evaded"
              return f"{self.initiator.name} tries to use {self.name} on {opponents.name}, but {opponents.name} evades the attack."
        # Manage summon skill
        elif self.skill_type == "summon":
          return self.skill_action()
        # Manage buff skill
        elif self.skill_type == "buffs":
          if opponents == ['none']:
            return self.skill_action()
          else:
            if self.target_type == "multi":
              return self.skill_action(opponents)
            elif self.target_type == "single":
              if self.name == "Holy Word Redemption": #designed code for Holy Word Redemption
                if len(self.initiator.allies) > 1 and self.initiator.hp <= round(0.75 * self.initiator.hp_max): #check if there is only the skill initiator remains
                  accuracy = 100  # Holy Word Redemption has a 100% chance to protect an extra hero if self hp < 75%
                  roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
                  if roll <= accuracy:
                    available_targets = [hero for hero in self.initiator.allies if hero != opponents]
                    extra_target = None
                    for target in available_targets:
                      for buff in target.buffs:
                        if buff.name == "Holy Word Redemption":
                          break
                      else:
                        extra_target = target
                        break
                    if extra_target is None:
                      extra_target = random.choice(available_targets)
                    if extra_target:
                      self.initiator.game.display_battle_info(f"{self.skill_action(opponents)}")
                      self.initiator.game.display_battle_info(f"{self.initiator.name} recieves the guidance of holy light and will protect an extra hero")
                      return f"{self.skill_action(extra_target)}"
                    else:
                      return self.skill_action(opponents)
                  else:
                    return self.skill_action(opponents)
                else:
                  return self.skill_action(opponents)
              else:
                return self.skill_action(opponents)

class Buff:
  def __init__(self, name, duration, initiator, effect):
        self.name = name
        self.duration = duration
        self.initiator = initiator
        self.effect = effect
        self.type = ['none']

class Debuff:
  def __init__(self, name, duration, initiator, effect):
        self.name = name
        self.duration = duration
        self.initiator = initiator
        self.effect = effect
        self.type = ['none']
