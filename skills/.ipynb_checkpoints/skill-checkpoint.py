import math
import random

class Skill:
    def __init__(self, initiator, name, skill_action, target_type, skill_type, target_qty = 1):
        self.initiator = initiator  # Reference to the hero instance who initiated the skill
        self.name = name            # Name of the skill, e.g., "Fireball"
        self.skill_action = skill_action   # This is a method reference that performs the skill's action
        self.target_type = target_type  # Indicates the targeting type ("single" or "multi")
        self.skill_type = skill_type  # Indicates the skill type ("damage" or "healing" or "effect")
        self.target_qty = target_qty  # Number of targets for the skill
        self.if_cooldown = False  # Flag to indicate if the skill is on cooldown
        self.cooldown = 0  # Skill cooldown in rounds


    def evasion_check(self, opponent):
        # Calculate the chance to evade based on agility;
        if opponent.evasion_capability <= (opponent.agility * 0.5):
          evasion_chance = min(50, opponent.agility * 0.5)  # capping the evasion chance at 50%
        else:
          evasion_chance = opponent.evasion_capability
        #print(f"Evasion Chance: {evasion_chance}")
        # Perform a random check against the evasion chance
        if random.randint(1, 100) <= math.ceil(evasion_chance):
           return True
        return False

    def execute(self, opponents):
        if self.skill_type == "healing":
          if self.target_type == "multi":
              return self.skill_action(opponents)
          elif self.target_type == "single":
              return self.skill_action(opponents)  # Pass only the first target
        elif self.skill_type == "damage":
          if self.target_type == "multi":
            target_hit = []
            target_evaded = []
            for target in opponents:
              if not self.evasion_check(target):
                target_hit.append(target)
              else:
                target_evaded.append(target)
            if not target_evaded:
              target_names = ', '.join([target.name for target in target_hit])
              #print(f"{self.initiator.name} use {self.name} on {target_names}.")
              return self.skill_action(target_hit)
            elif not target_hit:
              target_names = ', '.join([target.name for target in target_evaded])
              return f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack."
            else:
              target_names = ', '.join([target.name for target in target_evaded])
              print(f"{self.initiator.name} tries to use {self.name} on {target_names}, but {target_names} evades the attack.")
              return self.skill_action(target_hit)

          elif self.target_type == "single":
              if not self.evasion_check(opponents):
                return self.skill_action(opponents)
              else:
                return f"{self.initiator.name} tries to use {self.name} on {opponents.name}, but {opponents.name} evades the attack."

        elif self.skill_type == "buffs":
          if opponents == ['none']:
            return self.skill_action()