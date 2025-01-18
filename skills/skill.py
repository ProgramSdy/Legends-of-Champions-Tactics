import math
import random
from heroes import *
from skills import *

class Skill:
    def __init__(self, initiator, name, skill_action, target_type, skill_type, target_qty = 1, capable_interrupt_magic_casting = False, is_instant_skill = True):
        self.initiator = initiator  # Reference to the hero instance who initiated the skill
        self.name = name            # Name of the skill, e.g., "Fireball"
        self.skill_action = skill_action   # This is a method reference that performs the skill's action
        self.target_type = target_type  # Indicates the targeting type ("single" or "multi")
        self.skill_type = skill_type  # Indicates the skill type ("damage" or "healing" or "damage_healing"or "effect")
        self.target_qty = target_qty  # Number of targets for the skill
        self.capable_interrupt_magic_casting = capable_interrupt_magic_casting  # Flag to indicate if the skill can interrupt magic casting
        self.is_instant_skill = is_instant_skill  # Flag to indicate if the skill is instant
        self.if_cooldown = False  # Flag to indicate if the skill is on cooldown
        self.cooldown = 0  # Skill cooldown in rounds
        self.is_available = True


    def evasion_check(self, opponent):
        # Calculate the chance to evade based on agility;
        if opponent.evasion_capability <= (opponent.agility * 0.5):
          evasion_chance = min(50, opponent.agility * 0.5)  # capping the evasion chance at 50%
        else:
          evasion_chance = opponent.evasion_capability
        if random.randint(1, 100) <= math.ceil(evasion_chance):
           return True
        return False

    def execute(self, opponents):
        # Manage healing skills
        if self.skill_type == "healing":
          if self.target_type == "multi":
              return self.skill_action(opponents)
          elif self.target_type == "single":
              return self.skill_action(opponents)  # Pass only the first target
        # Manage damage skills
        elif self.skill_type == "damage":
          if self.is_instant_skill == False:
            if self.initiator.status['magic_casting'] == True and self.initiator.magic_casting_duration == 0:
              if self.target_type == "multi":
                if not isinstance(opponents, list):
                  opponents = [opponents]
                target_hit = []
                target_evaded = []
                for target in opponents:
                  if not self.evasion_check(target):
                    target_hit.append(target)
                  else:
                    target_evaded.append(target)

                # Check if targets is alive and if they are hit or miss
                target_hit_alive = [target for target in target_hit if target.hp > 0]
                target_evaded_alive = [target for target in target_evaded if target.hp > 0]

                if not target_evaded_alive and not target_hit_alive: # All targets dead
                  self.initiator.status['magic_casting'] = False
                  return f"{self.initiator.name} used {self.name}, but all targets are dead."

                if not target_evaded_alive:  # All targets hit
                    target_names = ', '.join([target.name for target in target_hit_alive])
                    return self.skill_action(target_hit_alive)

                elif not target_hit_alive:  # All targets missed
                    target_names = ', '.join([target.name for target in target_evaded_alive])
                    self.initiator.status['magic_casting'] = False
                    return f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack."

                else:  # Some hit, some evaded
                    target_hit_names = ', '.join([target.name for target in target_hit_alive])
                    target_evaded_names = ', '.join([target.name for target in target_evaded_alive])
                    self.initiator.game.display_battle_info(f"{self.initiator.name} tries to use {self.name} on {target_evaded_names}, but {target_evaded_names} evades the attack.")
                    return self.skill_action(target_hit_alive)


                if not target_evaded:  # all targets hit
                  target_names = ', '.join([target.name for target in target_hit])
                  #print(f"{self.initiator.name} use {self.name} on {target_names}.")
                  return self.skill_action(target_hit)
                elif not target_hit: # all targets miss
                  target_names = ', '.join([target.name for target in target_evaded])
                  self.initiator.status['magic_casting'] = False
                  return f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack."
                else:
                  target_names = ', '.join([target.name for target in target_evaded])
                  self.initiator.game.display_battle_info(f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack.")
                  return self.skill_action(target_hit)

              elif self.target_type == "single":
                  if not self.evasion_check(opponents):
                      return self.skill_action(opponents)
                  else:
                    if self.name == "Shadow Word Insanity" or self.name == "Curse of Fear":
                      self.if_cooldown = True
                      self.cooldown = 3
                      return f"{self.initiator.name} tries to use {self.name} on {opponents.name}, but {opponents.name} evades the attack."
                    else:
                      return f"{self.initiator.name} tries to use {self.name} on {opponents.name}, but {opponents.name} evades the attack."
            else:
              return self.skill_action(opponents)
          else:
            if self.target_type == "multi": # Manage damage skill with multiple targets
                if not isinstance(opponents, list):
                  opponents = [opponents]
                target_hit = []
                target_evaded = []
                for target in opponents:
                  if not self.evasion_check(target):
                    target_hit.append(target)
                  else:
                    target_evaded.append(target)
                if not target_evaded:  # all targets hit
                  target_names = ', '.join([target.name for target in target_hit])
                  #print(f"{self.initiator.name} use {self.name} on {target_names}.")
                  return self.skill_action(target_hit)
                elif not target_hit: # all targets miss
                  target_names = ', '.join([target.name for target in target_evaded])
                  return f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack."
                else:
                  target_names = ', '.join([target.name for target in target_evaded])
                  self.initiator.game.display_battle_info(f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack.")
                  return self.skill_action(target_hit)
            elif self.target_type == "single": # Manage damage skill with single targets
                if not self.evasion_check(opponents):
                    return self.skill_action(opponents)
                else:
                  if self.name == "Shield of Righteous":
                    if self.initiator.status['shield_of_righteous'] == False:
                      self.initiator.status['shield_of_righteous'] = True
                      defense_before_increasing = self.initiator.defense
                      defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.initiator.original_defense * 0.15)  # Increase hero's defense by 15%
                      self.initiator.defense_increased_amount_by_shield_of_righteous = self.initiator.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
                      self.initiator.defense = self.initiator.defense + defense_increased_amount_by_shield_of_righteous_single
                      self.initiator.shield_of_righteous_stacks += 1
                      self.initiator.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
                      return f"{self.initiator.name} tries to attack {opponents.name} with Shield of Righteous, but {opponents.name} evades the attack. Defense of {self.initiator.name} has increased from {defense_before_increasing} to {self.initiator.defense}."
                    else:
                      if self.initiator.shield_of_righteous_stacks < 2: #shield of righteous effect can stack for two times.
                        defense_before_increasing = self.initiator.defense
                        defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.initiator.original_defense * 0.15)  # Increase hero's defense by 15%
                        self.initiator.defense_increased_amount_by_shield_of_righteous = self.initiator.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
                        self.initiator.defense = self.initiator.defense + defense_increased_amount_by_shield_of_righteous_single
                        self.initiator.shield_of_righteous_stacks += 1
                        self.initiator.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
                        return f"{self.initiator.name} tries to attack {opponents.name} with Shield of Righteous, but {opponents.name} evades the attack. Defense of {self.initiator.name} has increased from {defense_before_increasing} to {self.initiator.defense}."
                      else:
                        self.initiator.shield_of_righteous_duration = 3
                        return f"{self.initiator.name} tries to attack {opponents.name} with Shield of Righteous. but {opponents.name} evades the attack. Shield of Righteous buff duration refreshed"
                  if self.name == "Shadow Word Insanity" or self.name == "Curse of Fear":
                    self.if_cooldown = True
                    self.cooldown = 3
                    return f"{self.initiator.name} tries to use {self.name} on {opponents.name}, but {opponents.name} evades the attack."
                  else:
                    return f"{self.initiator.name} tries to use {self.name} on {opponents.name}, but {opponents.name} evades the attack."
        # Manage damage healing skill
        elif self.skill_type == "damage_healing":
          if opponents in self.initiator.allies:
            return self.skill_action(opponents, 'ally')
          else:
            if not self.evasion_check(opponents):
              return self.skill_action(opponents, 'opponent')
            else:
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

class Debuff:
  def __init__(self, name, duration, initiator, effect):
        self.name = name
        self.duration = duration
        self.initiator = initiator
        self.effect = effect