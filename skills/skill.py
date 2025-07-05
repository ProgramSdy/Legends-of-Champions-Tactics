import math
import random
from heroes import *
from skills import *

class Skill:
    def __init__(self, initiator, name, skill_action, target_type, skill_type, target_qty = 1, capable_interrupt_magic_casting = False, is_instant_skill = True, damage_nature = "NA", damage_type = "NA"):       
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
        self.immunity_condition_all = ['shield_of_protection', 'glacier']
        self.immunity_condition_physical = []
        self.immunity_condition_magical = []
        self.active_state = None
        self.damage_nature = damage_nature
        self.damage_type = damage_type

    def immunity_condition_all_check(self, opponent):
        # Check for immunity to all damage
        for state in getattr(self, 'immunity_condition_all', []):
            if opponent.status[state] is True:
                self.active_state = state
                return True
        return False
    
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
            "dead": []
        }
        for target in targets:
            if self.death_check(target):
                outcomes["dead"].append(target)
                continue
            if self.evasion_check(target):
                outcomes["evaded"].append(target)
                continue
            if self.immunity_condition_all_check(target):
                outcomes["immunity_condition_all"].append(target)
                continue
            if self.immunity_condition_physical_check(target):
                outcomes["immunity_condition_physical"].append(target)
                continue
            if self.immunity_condition_magical_check(target):
                outcomes["immunity_condition_magical"].append(target)
                continue
            outcomes["hit"].append(target)
        return outcomes

    def execute(self, opponents):
        # Manage healing skills
        if self.skill_type == "healing":
            return self.skill_action(opponents)
       
        # Manage damage skills
        elif self.skill_type == "damage":
          if not isinstance(opponents, list):
            opponents = [opponents]
          outcomes = self.resolve_targets(opponents)
          hits = outcomes["hit"]
          evaded = outcomes["evaded"]
          immune_all = outcomes["immunity_condition_all"]
          immune_phy = []
          immune_mag = []
          if self.damage_nature == "physical":
            immune_phy = outcomes["immunity_condition_physical"]
          if self.damage_nature == "magical":
            immune_mag = outcomes["immunity_condition_magical"]
          dead = outcomes["dead"]

          if self.target_type == "multi": # Manage multi-targets damage skill

            # Special condition manage casting skills
            if self.name == "Rain of Fire":
               if not self.initiator.status['hell_flame']:
                  if self.initiator.status['magic_casting'] == False:
                    return self.skill_action(opponents)

            if not hits:
              result_message = ""
              if dead:
                target_names = ', '.join([t.name for t in dead])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} were already dead. \n"
              if evaded:
                target_names = ', '.join([t.name for t in evaded])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evaded the attack. \n"
              if immune_all:
                target_names = ', '.join([t.name for t in immune_all])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to all damage \n"
              if immune_phy:
                target_names = ', '.join([t.name for t in immune_phy])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to physical damage \n"
              if immune_mag:
                target_names = ', '.join([t.name for t in immune_mag])
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to magical damage \n"
              
              # Special Condition Cool down skills
              if self.name == "Icy Squall":
                self.if_cooldown = True
                self.cooldown = 2
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
                result_message += f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immuned to magical damage. \n"
              if result_message:
                self.initiator.game.display_battle_info(result_message)
              return self.skill_action(hits)

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
                  result_message = f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} immunes to magical damage."
                
                # Special Condition
                if self.name == "Shield of Righteous":
                    if self.initiator.status['shield_of_righteous'] == False:
                      self.initiator.status['shield_of_righteous'] = True
                      defense_before_increasing = self.initiator.defense
                      defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.initiator.original_defense * 0.15)  # Increase hero's defense by 15%
                      self.initiator.defense_increased_amount_by_shield_of_righteous = self.initiator.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
                      self.initiator.defense = self.initiator.defense + defense_increased_amount_by_shield_of_righteous_single
                      self.initiator.shield_of_righteous_stacks += 1
                      self.initiator.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
                      result_message += f" Defense of {self.initiator.name} has increased from {defense_before_increasing} to {self.initiator.defense}."
                    else:
                      if self.initiator.shield_of_righteous_stacks < 2: #shield of righteous effect can stack for two times.
                        defense_before_increasing = self.initiator.defense
                        defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.initiator.original_defense * 0.15)  # Increase hero's defense by 15%
                        self.initiator.defense_increased_amount_by_shield_of_righteous = self.initiator.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
                        self.initiator.defense = self.initiator.defense + defense_increased_amount_by_shield_of_righteous_single
                        self.initiator.shield_of_righteous_stacks += 1
                        self.initiator.shield_of_righteous_duration = 3  # Effect lasts for 2 rounds
                        result_message += f" Defense of {self.initiator.name} has increased from {defense_before_increasing} to {self.initiator.defense}."
                      else:
                        self.initiator.shield_of_righteous_duration = 3
                        result_message += f" Shield of Righteous buff duration refreshed."
                if self.name == "Crusader Strike":
                  if self.initiator.status['wrath_of_crusader'] == False:
                    self.initiator.status['wrath_of_crusader'] = True
                    agility_before_increasing = self.initiator.agility
                    agility_increased_amount_by_wrath_of_crusader_single = math.ceil(self.initiator.original_agility * 0.75)  # Increase hero's agility by 75%
                    self.initiator.agility_increased_amount_by_wrath_of_crusader = self.initiator.agility_increased_amount_by_wrath_of_crusader + agility_increased_amount_by_wrath_of_crusader_single  # Defense increase accumulated
                    self.initiator.agility = self.initiator.agility + agility_increased_amount_by_wrath_of_crusader_single
                    self.initiator.wrath_of_crusader_stacks += 1
                    self.initiator.wrath_of_crusader_duration = 3  # Effect lasts for 2 rounds
                    result_message += f" Agility of {self.initiator.name} has increased from {agility_before_increasing} to {self.initiator.agility}."
                  else:
                    if self.initiator.wrath_of_crusader_stacks < 2: # wrath of crusader effect can stack for two times.
                      agility_before_increasing = self.initiator.agility
                      agility_increased_amount_by_wrath_of_crusader_single = math.ceil(self.initiator.original_agility * 0.75)  # Increase hero's agility by 75%
                      self.initiator.agility_increased_amount_by_wrath_of_crusader = self.initiator.agility_increased_amount_by_wrath_of_crusader + agility_increased_amount_by_wrath_of_crusader_single  # Defense increase accumulated
                      self.initiator.agility = self.initiator.agility + agility_increased_amount_by_wrath_of_crusader_single
                      self.initiator.wrath_of_crusader_stacks += 1
                      self.initiator.wrath_of_crusader_duration = 3  # Effect lasts for 2 rounds
                      result_message += f" Agility of {self.initiator.name} has increased from {agility_before_increasing} to {self.initiator.agility}."
                    else:
                      self.wrath_of_crusader_duration = 3
                      result_message += f" Wrath of Crusader buff duration refreshed"
                if self.name == "Shadow Word Insanity" or self.name == "Curse of Fear":
                  self.if_cooldown = True
                  self.cooldown = 3
                if self.name == "Pestilence":
                  self.if_cooldown = True
                  self.cooldown = 2
                if self.name == "Cumbrous Axe":
                  self.if_cooldown = True
                  self.cooldown = 3
                  self.initiator.status['cumbrous_axe'] = True
                  self.initiator.healing_boost_effects['cumbrous_axe'] = 1.0
                  for buff in self.initiator.buffs_debuffs_recycle_pool:
                    if buff.name == "Cumbrous Axe" and buff.initiator == self:
                        self.initiator.buffs_debuffs_recycle_pool.remove(buff)
                        buff.duration = 2
                        self.initiator.add_buff(buff)   
                  else:
                      buff = Buff(
                          name='Cumbrous Axe',
                          duration=2,
                          initiator=self,
                          effect=1
                      )
                      self.initiator.add_buff(buff)
                  result_message +=  f" The healing {self.initiator.name} receives is boost."
                if self.name == "Heroric Charge":
                  basic_healing_heroric_charge = 22
                  variation = random.randint(-2, 2)
                  actual_healing = basic_healing_heroric_charge + variation
                  self.if_cooldown = True
                  self.cooldown = 3
                  result_message +=  f"Holy light showers {self.initiator.name}. {self.initiator.take_healing(actual_healing)}."
                return result_message
              else:
                return self.skill_action(hits[0])

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
        self.type = ['none']

class Debuff:
  def __init__(self, name, duration, initiator, effect):
        self.name = name
        self.duration = duration
        self.initiator = initiator
        self.effect = effect
        self.type = ['none']