import math
import random

class Hero:
    # Class variables for ranges and skills - no specific values here
    damage_interval = (0, 0)
    defense_interval = (0, 0)
    magic_resistance_interval = (0, 0)
    agility_interval = (0, 0)
    hp_interval = (0, 0)
    status = {
        'normal':True,
        'stunned':False,
        'burned':False,
        'poison':False,
        'cold': False,
        'frozen':False,
        'shadow_word_pain':False,
        'poisoned_dagger':False,
        'bleeding_sharp_blade': False,
        'shadow_evasion': False
    }


    def __init__(self, name, profession, group, is_player_controlled=False):
        self.name = name
        self.profession = profession
        self.is_player_controlled = is_player_controlled
        self.damage = self.random_in_range(self.damage_interval)
        self.original_damage = self.damage # store the original damage
        self.damage_type = ""
        self.defense = self.random_in_range(self.defense_interval)
        self.original_defense = self.defense # store the original defense
        self.magic_resistance = self.random_in_range(self.magic_resistance_interval)
        self.original_magic_resistance = self.magic_resistance # store the original magic resistance
        self.agility = self.random_in_range(self.agility_interval)
        self.original_agility = self.agility # store the original agility
        self.hp_max = self.random_in_range(self.hp_interval)
        self.hp = self.hp_max
        self.evasion_capability = 0
        self.skills = []
        self.group = group
        self.allies = []
        self.allies_self_excluded = []
        self.opponents = []

        # Status buff and debuff
        self.status = self.status.copy() # Copy the status dictionary for individual management
        self.stun_duration = 0 # Initialize stun duration
        self.poison_duration = 0
        self.burn_duration = 0
        self.cold_duration = 0
        self.frozen_duration = 0

        #duration buff and debuff
        self.damage_buff_duration = 0
        self.damage_debuff_duration = 0
        self.defense_buff_duration = 0
        self.defense_debuff_duration = 0
        self.magic_resistance_buff_duration = 0
        self.magic_resistance_debuff_duration = 0
        self.agility_buff_duration = 0
        self.agility_debuff_duration = 0
        self.shadow_word_pain_debuff_duration = 0
        self.poisoned_dagger_debuff_duration = 0
        self.sharp_blade_debuff_duration = 0
        self.shadow_evasion_buff_duration = 0

        self.armor_breaker_stacks = 0 # Track number of Armor Breaker applications
        self.defense_reduced_amount_by_armor_breaker = 0 # Track the amount of armor breaker
        self.shield_of_righteous_stacks = 0 # Track number of Shield of Righteous applications
        self.defense_increased_amount_by_shield_of_righteous = 0 # Track the amount of Shield of Righteous
        self.agility_reduced_amount_by_frost_bolt = 0 # Track the amount of Frost Bolt
        self.shadow_word_pain_continuous_damage = 0 # Track the continuous damage of Shadow Word Pain
        self.poisoned_dagger_continuous_damage = 0 # Track the continuous damage of Poisoned Dagger
        self.poisoned_dagger_stacks = 0 # Track number of Poisoned Dagger applications
        self.sharp_blade_continuous_damage = 0 # Track the continuous damage of Sharp Blade



    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])

    def show_info(self):
        skill_names = [skill.name for skill in self.skills]
        return (f"Hero: {self.name}\n"
                f"Group: {self.group}\n"
                f"Profession: {self.profession}\n"
                f"HP: {self.hp}/{self.hp_max}\n"
                f"Damage: {self.damage} ({self.damage_type})\n"
                f"Defense: {self.defense}\n"
                f"Magic Resistance: {self.magic_resistance}\n"
                f"Agility: {self.agility}\n"
                f"Skills: {', '.join(skill_names)}")

    def take_damage(self, damage_dealt):
          damage_dealt = max(0, damage_dealt)
          self.hp = self.hp - damage_dealt
          if self.hp < 0:
              self.hp = 0
          return f"{self.name} takes {damage_dealt} damage and has {self.hp} HP left."

    def take_healing(self, healing_amount):
        self.hp = min(self.hp_max, self.hp + healing_amount)
        return f"{self.name} takes {healing_amount} healing and has {self.hp} HP left."

    def add_skill(self, skill):
        self.skills.append(skill)

    def ai_choose_skill(self):
        available_skills = [skill for skill in self.skills if not skill.if_cooldown]
        chosen_skill = random.choice(available_skills)
        return chosen_skill

    def player_choose_skill(self, hero):
        self.hero = hero
        print('*******************************************************************************************')
        print(hero.name + ", please choose your skills:")
        available_skills = [skill for skill in self.skills if not skill.if_cooldown]
        for skill in available_skills:
            print(skill.name)  # Display skill names
        while True:
            skill_input = input("Enter the name of the skill you want to use: ").strip().lower()
            #print('********************************************')
            for skill in available_skills:
                if skill.name.lower() == skill_input:
                    return skill  # If input matches, return the skill object
            print("Invalid input, please try again.")  # Input doesn't match any skill name

    def player_choose_target(self, opponents, allies, chosen_skill, num_targets = 1):

        print("Available targets:")
        if chosen_skill.skill_type == "damage":
          for index, opponent in enumerate(opponents):
            print(f"{index + 1}:{opponent.name} HP: {opponent.hp}")
        elif chosen_skill.skill_type == "healing":
          if chosen_skill.name == "Binding Heal":
            filtered_allies = [ally for ally in allies if ally is not self]
            if len(filtered_allies) == 0:
              print(f"No allies available to heal. Binding Heal is casted on {self.name} himself")
              selected_targets = [self]
              print('*******************************************************************************************')
              return selected_targets
            else:
              for index, ally in enumerate(filtered_allies):
                print(f"{index + 1}:{ally.name} HP: {ally.hp}")
          else:
            for index, ally in enumerate(allies):
              print(f"{index + 1}:{ally.name} HP: {ally.hp}")

        selected_targets = []

        while len(selected_targets) < num_targets:

          if chosen_skill.skill_type == "damage":
            try:
              target_input = input(f"Enter the number of the target {len(selected_targets) + 1} you want to attack: ")
              target = opponents[int(target_input) - 1]
              if target in selected_targets:
                  print("You have already selected this target. Please choose a different one.")
              else:
                selected_targets.append(target)
            except (ValueError, IndexError):
              print("Invalid input, please try again")

          elif chosen_skill.skill_type == "healing":
            if chosen_skill.name == "Binding Heal":
                try:
                  target_input = input(f"Enter the number of the target {len(selected_targets) + 1} you want to heal: ")
                  target = filtered_allies[int(target_input) - 1]
                  if target in selected_targets:
                      print("You have already selected this target. Please choose a different one.")
                  else:
                    selected_targets.append(target)
                except (ValueError, IndexError):
                  print("Invalid input, please try again")
            else:
                try:
                  target_input = input(f"Enter the number of the target {len(selected_targets) + 1} you want to heal: ")
                  target = allies[int(target_input) - 1]
                  if target in selected_targets:
                      print("You have already selected this target. Please choose a different one.")
                  else:
                    selected_targets.append(target)
                except (ValueError, IndexError):
                  print("Invalid input, please try again")


        print('*******************************************************************************************')
        return selected_targets

    def ai_choose_target(self, chosen_skill, opponents, allies):
        if chosen_skill.skill_type == "damage":
          if chosen_skill.target_type == "single":
              chosen_opponent = random.choice(opponents)
          if chosen_skill.target_type == "multi":
              chosen_opponent = random.sample(opponents, chosen_skill.target_qty) if len(opponents) > chosen_skill.target_qty else opponents
          return chosen_opponent

        elif chosen_skill.skill_type == "healing":
          if chosen_skill.target_type == "single":
            if chosen_skill.name == "Binding Heal":
              if len(self.allies_self_excluded) == 0:
                  chosen_ally = self
              else:
                chosen_ally = random.choice(self.allies_self_excluded)
            else:
              chosen_ally = random.choice(self.allies)
          if chosen_skill.target_type == "multi":
              chosen_ally = allies
          return chosen_ally
        elif chosen_skill.skill_type == "buffs":
          if chosen_skill.target_qty == 0:
            return ['none']



    def ai_action(self, opponents, allies):

        if not self.status['stunned']:
            if self.skills:
                chosen_skill = self.ai_choose_skill()
                chosen_target = self.ai_choose_target(chosen_skill, opponents, allies)
                if opponents:
                    return chosen_skill.execute(chosen_target)
                else:
                    return f"{self.name} tries to use {chosen_skill}, but it's not implemented or no valid opponents."
            else:
                return f"{self.name} has no skills to use."
        else:
            return f"{self.name} can't move."

    def player_action(self, hero, opponents, allies):
        # Update all status effects at the beginning of the action
        self.hero = hero
        # Proceed with action if not stunned
        if not self.status['stunned']:
            if self.skills:
                chosen_skill = hero.player_choose_skill(hero)
                if len(opponents) > 1: #if their is plural enemy available
                  if chosen_skill.target_type == "multi":
                      chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)
                  elif chosen_skill.target_type == "single":
                    if chosen_skill.target_qty == 0:
                      chosen_targets = ['none']
                    else:
                      chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)[0]
                else: #if there is only one enemy available
                  if chosen_skill.target_qty == 0:
                    chosen_targets = ['none']
                  else:
                    chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)[0]

                if opponents:
                  if chosen_targets == ['none']:
                    print('*******************************************************************************************')
                    return chosen_skill.execute(chosen_targets)
                  else:
                    return chosen_skill.execute(chosen_targets)  # Pass opponents
                else:
                    return f"{self.name} tries to use {chosen_skill}, but it's not implemented or no valid opponents."
            else:
                return f"{self.name} has no skills to use."
        else:
            return f"{self.name} can't move."