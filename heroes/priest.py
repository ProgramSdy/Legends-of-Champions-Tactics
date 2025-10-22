import math
import random
from heroes import *
from skills import *

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Priest(Hero):

    faculty = "Priest"

    def __init__(self, sys_init, name, group, is_player_controlled, major):
            super().__init__(sys_init, name, group, is_player_controlled, major, faculty=self.__class__.faculty)
            self.hero_damage_type = "holy"

class Priest_Comprehensiveness(Priest):

    major = "Comprehensiveness"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major=self.__class__.major)
            self.add_skill(Skill(self, "Holy Smite", self.holy_smite, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shadow Word Pain", self.shadow_word_pain, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Binding Heal", self.binding_heal, "single", skill_type= "healing"))

    def holy_smite(self, other_hero):
        basic_damage = 19
        variation = random.randint(-3, 3)
        actual_damage = basic_damage + variation
        damage_dealt = actual_damage # holy damage ignore's opponents magic resistance
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        self.game.display_battle_info(f"{self.name} casts Holy Smite at {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def shadow_word_pain(self, other_hero):
        variation = random.randint(0, 5)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.shadow_resistance)*(1/2))
        if other_hero.status['shadow_word_pain'] == False:
            other_hero.status['shadow_word_pain'] = True
            other_hero.shadow_word_pain_debuff_duration = 5  # Effect lasts for 4 rounds
            if damage_dealt > 0:
              other_hero.shadow_word_pain_continuous_damage = round((actual_damage - other_hero.shadow_resistance)*(1/3))
            else:
              other_hero.shadow_word_pain_continuous_damage = random.randint(1, 10)
            self.game.display_battle_info(f"{self.name} uses Shadow Word Pain on {other_hero.name}. {other_hero.name} feels continuous pain")
        else:
            self.game.display_battle_info(f"{self.name} uses Shadow Word Pain on {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def binding_heal(self, other_hero):
        variation_1 = random.randint(-3, 3)
        variation_2 = random.randint(-3, 3)
        healing_amount_base_1 = 25
        healing_amount_base_2 = 20
        healing_amount_1 = healing_amount_base_1 + variation_1
        healing_amount_2 = healing_amount_base_2 + variation_2
        results = []
        if other_hero == self:
          self.game.display_battle_info(f"{self.name} casts Binding Heal on {other_hero.name}.")
          return other_hero.take_healing(healing_amount_1)
        else:
          self.game.display_battle_info(f"{self.name} casts Binding Heal on {other_hero.name}.")
          results.append(other_hero.take_healing(healing_amount_1))
          self.game.display_battle_info(f"{self.name} casts Binding Heal on {self.name}.")
          results.append(self.take_healing(healing_amount_2))
          return "\n".join(results)

class Priest_Shelter(Priest):

    major = "Shelter"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major = self.__class__.major)
            self.add_skill(Skill(self, "Holy Smite", self.holy_smite, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Holy Word Shell", self.holy_word_shell, "single", skill_type= "healing"))
            self.add_skill(Skill(self, "Purification and Cure", self.purification_and_cure, "single", skill_type= "healing"))

    def holy_smite(self, other_hero):
        basic_damage = 19
        variation = random.randint(-3, 3)
        actual_damage = basic_damage + variation
        damage_dealt = actual_damage # holy damage ignore's opponents magic resistance
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        self.game.display_battle_info(f"{self.name} casts Holy Smite at {other_hero.name}.")

        # Apply damage to the target
        result = other_hero.take_damage(damage_dealt)

        # If the priest has Holy Word Shell active, heal the lowest HP ally
        if self.status['holy_word_shell']:
          sorted_allies = sorted(self.allies, key=lambda hero: hero.hp, reverse=False)
          lowest_hp_ally = sorted_allies[0]
          if lowest_hp_ally:
              self.game.display_battle_info(f"{BLUE}{self.name} is under protection from Holy Word Shell, {self.name}'s Holy Smite heals {lowest_hp_ally.name}.{RESET}")
              self.game.display_battle_info(lowest_hp_ally.take_healing(damage_dealt))

        return result

    # randomly dispell maximum 3 nagtive magic or bleeding effect from one ally hero
    #list_status_debuff_magic = ['shadow_word_pain', 'poisoned_dagger', 'cold', 'holy_word_punishment', \
                                #'shadow_word_insanity', 'unholy_frenzy', 'curse_of_agony']
    #list_status_debuff_bleeding = ['bleeding_slash','bleeding_sharp_blade']
    def purification_and_cure(self, hero):
      hero_status_activated = [key for key, value in hero.status.items() if value == True]
      set_comb = set(self.list_status_debuff_magic) | set(self.list_status_debuff_bleeding) | set(self.list_status_debuff_disease) | set(self.list_status_debuff_toxic)
      equal_status = set(hero_status_activated) & set_comb
      status_list_for_action = list(equal_status)
      random.shuffle(status_list_for_action)
      #self.game.display_battle_info(f"Status all: {status_list_for_action}")
      if len(status_list_for_action) > 3:
        status_list_for_action = status_list_for_action[:3]
      if status_list_for_action:
        variation = random.randint(-2, 2)
        healing_amount_base = 10 * len(status_list_for_action)
        healing_amount = healing_amount_base + variation
        #self.game.display_battle_info(f"Status purificable: {status_list_for_action}")
        self.game.display_battle_info(f"{self.name} casts Purification and Cure on {hero.name}.")
        self.game.status_dispeller.dispell_status(status_list_for_action, hero)
        return f"{hero.name} gains healing from Purifification and Cure. {hero.take_healing(healing_amount)}"
      else:
        self.game.display_battle_info(f"{self.name} casts Purification and Cure on {hero.name}.")
        return f"{BLUE}But {hero.name} has no negative effect to be purified or cured.{RESET}"


    def holy_word_shell(self, other_hero):

        if other_hero.status['shield_of_protection'] == False:
          if other_hero.status['holy_word_shell'] == False:
            variation = random.randint(-2, 2)
            max_absorption = math.ceil(self.hp_max/2) + variation
            other_hero.holy_word_shell_absorption = max_absorption
            other_hero.status['holy_word_shell'] = True
            other_hero.holy_word_shell_duration = 2
            return f"{self.name} casts Holy Word Shell on {other_hero.name}. The shell will absorb {max_absorption} damage"
          else:
            accuracy = 100  # holy word shell has a 100% chance to override the previous shell
            roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
            if roll <= accuracy:
              variation = random.randint(-2, 2)
              max_absorption = math.ceil(self.hp_max/2) + variation
              other_hero.holy_word_shell_absorption = max_absorption
              other_hero.holy_word_shell_duration = 2
              return f"{self.name} casts Holy Word Shell on {other_hero.name}. It replace the previous Shell and will absorb {max_absorption} damage"
            else:
              return f"{self.name} tries to cast Holy Word Shell on {other_hero.name}. But {other_hero.name} has already been protected by a shell"
        else:
              return f"It is not possible to cast Holy Word Shell on {other_hero.name}, because they are in Shield of Protection status."

    # Battling Strategy_________________________________________________________

    def strategy_0(self):
        self.probability_holy_smite = 0.5
        self.probability_holy_word_shell = 0.5
        self.probability_purification_and_cure = 0

    def strategy_1(self):
        self.probability_holy_smite = 1
        self.probability_holy_word_shell = 0
        self.probability_purification_and_cure = 0

    def strategy_2(self):
        self.probability_holy_smite = 0
        self.probability_holy_word_shell = 1
        self.probability_purification_and_cure = 0

    def strategy_3(self):
        self.probability_holy_smite = 0
        self.probability_holy_word_shell = 0
        self.probability_purification_and_cure = 1

    def strategy_4(self):
        self.probability_holy_smite = 0.1
        self.probability_holy_word_shell = 0
        self.probability_purification_and_cure = 0.9

    def battle_analysis(self, opponents, allies):
      # Sort hp from low to high
      sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
      sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
      sorted_allies_excludes_self = sorted_allies.copy()
      for ally in sorted_allies_excludes_self:
        if ally == self:
          sorted_allies_excludes_self.remove(ally)
      # Priority targets tackling strategy

      # Find out if any opponant hero has hp < 16 and eliminate them from battle
      if sorted_opponents[0].hp < 16:
        self.strategy_1()
        return sorted_opponents[0]

      # Find out the hero with most active debuffs and do purification
      max_debuff_ally = max(
          allies,
          key=lambda ally: len(
              set([key for key, value in ally.status.items() if value == True]) &
              (set(self.list_status_debuff_magic) | set(self.list_status_debuff_bleeding))
          )
      )
      max_debuff_count = len(
          set([key for key, value in max_debuff_ally.status.items() if value == True]) &
          (set(self.list_status_debuff_magic) | set(self.list_status_debuff_bleeding))
      )
      if max_debuff_count >= 2: # purifying debuff if ally have 2+ debuffs
        self.strategy_3()
        return max_debuff_ally
      elif max_debuff_count == 1:
        accuracy = 25  # 25% chance purifying debuff if ally just have 1 debuff
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          self.strategy_3()
          return max_debuff_ally
        else:
          pass

      # Find lowest hp hero and apply shell
      if sorted_allies[0].status['holy_word_shell'] == False:
        self.strategy_2()
        return sorted_allies[0]
      # If self has no shell, add one
      if self.status['holy_word_shell'] == False:
        self.strategy_2()
        return self

      # If no priority targets, then choose lowest hp opponant and apply holy smite
      opponent = sorted_opponents[0]
      self.strategy_1()
      return opponent

    def ai_choose_skill(self, opponents, allies):
        self.strategy_1()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_holy_smite, self.probability_holy_word_shell, self.probability_purification_and_cure]
        #available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        #chosen_skill = random.choice(available_skills)
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent
    
class Priest_Discipline(Priest):

    major = "Discipline"

    def __init__(self, sys_init, name, group, is_player_controlled=False):
            super().__init__(sys_init, name, group, is_player_controlled, major = self.__class__.major)
            self.add_skill(Skill(self, "Penance", self.penance, "single", skill_type= "damage_healing"))
            self.add_skill(Skill(self, "Holy Word Redemption", self.holy_word_redemption, "single", skill_type= "buffs"))
            self.add_skill(Skill(self, "Holy Word Punishment", self.holy_word_punishment, target_type = "multi", skill_type= "damage", target_qty= 2))

    def penance(self, other_hero, target_type):
      healing_amount_base = 25
      results = []
      if target_type == "ally": # healing effect
        variation = random.randint(-4, 0)
        healing_amount = healing_amount_base + variation
        self.game.display_battle_info(f"{self.name} casts Penance on {other_hero.name}.")
        return other_hero.take_healing(healing_amount)

      elif target_type =="opponent": # damage effect
        variation = random.randint(-8, -4)
        actual_damage = healing_amount_base + variation
        damage_dealt = actual_damage #damage discard opponent's defense
        damage_dealt = max(damage_dealt, 0) # Ensure damage dealt is at least 0

        # Apply damage to the other hero's HP
        ally_with_buff = []
        for ally in self.allies:
          for buff in ally.buffs:
            if buff.name == "Holy Word Redemption" and buff.initiator == self:
              ally_with_buff.append(ally)
              break
        if ally_with_buff:
          self.game.display_battle_info(f"{self.name} casts Penance at {other_hero.name}.")
          self.game.display_battle_info(f"{other_hero.take_damage(damage_dealt)}")
          #print("Holy light shines upon ally heroes")
          buff_healing = round(buff.effect * damage_dealt)
          variation = random.randint(-1, 1)
          for ally in ally_with_buff:
              self.game.display_battle_info(f"{ally.name} is protected by Holy Word Redemption.")
              results.append(f"{ally.take_healing(buff_healing)}")
          return "\n".join(results)
        else:
          self.game.display_battle_info(f"{self.name} casts Penance at {other_hero.name}.")
          return f"{other_hero.take_damage(damage_dealt)}"

    def holy_word_punishment(self, other_hero):
        basic_damage = 9
        variation = random.randint(-2, 2)
        actual_damage = basic_damage + variation

        if not isinstance(other_hero, list):
          other_hero = [other_hero]
        results = []
        selected_opponents = other_hero
        damage_dealt = actual_damage
        for opponent in selected_opponents:
            if opponent.status['holy_word_punishment'] == False:
              opponent.status['holy_word_punishment'] = True
              for debuff in opponent.buffs_debuffs_recycle_pool:
                  if debuff.name == "Holy Word Punishment" and debuff.initiator == self:
                      opponent.buffs_debuffs_recycle_pool.remove(debuff)
                      debuff.duration = 4   # Effect lasts for 3 rounds
                      debuff.effect = round(1.3 * damage_dealt) # continuous damage equal to 1.3 times first damage
                      opponent.add_debuff(debuff)
                      results.append(f"{self.name} uses Holy Word Punishment on {opponent.name}. {opponent.name} is under punishment")
                      break
              else:
                  name='Holy Word Punishment'
                  duration = 4 # Effect lasts for 3 rounds
                  initiator = self
                  effect = math.ceil(1.3 * damage_dealt) # continuous damage equal to 1.3 times first damage
                  debuff = Debuff(name, duration, initiator, effect)
                  opponent.add_debuff(debuff)
                  results.append(f"{self.name} uses Holy Word Punishment on {opponent.name}. {opponent.name} is under punishment")
            else:
              results.append(f"{self.name} uses Holy Word Punishment on {opponent.name}.")
            # Apply initial damage
            results.append(opponent.take_damage(damage_dealt))

            # Check if Holy Word Redemption is on any allies and apply healing to them
            allies_with_buff = [ally for ally in self.allies if any(buff.name == "Holy Word Redemption" and buff.initiator == self for buff in ally.buffs)]
            if allies_with_buff:
              num_allies = len(allies_with_buff)
              for ally in allies_with_buff:
                for buff in ally.buffs:
                  if buff.name == "Holy Word Redemption" and buff.initiator == self:
                      buff_healing = math.ceil(buff.effect * actual_damage)
                      healing_variation = random.randint(-1, 1)
                      total_healing = round((buff_healing + healing_variation) * self.take_healing_coefficient(num_allies))
                      #total_healing = buff_healing + healing_variation
                      results.append(f"{ally.name} is protected by Holy Word Redemption. {ally.take_healing(total_healing)}")
                      #results.append(ally.take_healing(total_healing))

        return "\n".join(results)


    def holy_word_redemption(self, other_hero):
        if other_hero.status['holy_word_redemption'] == False:
            other_hero.status['holy_word_redemption'] = True
            for buff in other_hero.buffs_debuffs_recycle_pool:
                if buff.name == "Holy Word Redemption" and buff.initiator == self:
                    other_hero.buffs_debuffs_recycle_pool.remove(buff)
                    buff.duration = 5   # Effect lasts for 4 rounds
                    other_hero.add_buff(buff)
                    return f"{self.name} uses Holy Word Redemption on {other_hero.name}. {other_hero.name} feels being protected"

            buff = Buff(
                name='Holy Word Redemption',
                duration = 5,
                initiator = self,
                effect = 0.7
            )
            other_hero.add_buff(buff)
            return f"{self.name} uses Holy Word Redemption on {other_hero.name}. {other_hero.name} feels being protected"
        else:
            for buff in other_hero.buffs:
                if buff.name == "Holy Word Redemption" and buff.initiator == self:
                    buff.duration = 5   # Effect lasts for 4 rounds
            return f"{self.name} uses Holy Word Redemption on {other_hero.name} and refreshes it's duration"

# Battling Strategy_________________________________________________________
    def strategy_0(self):
        """Initial strategy probabilities."""
        self.probability_penance = 0.5
        self.probability_punishment = 0.5
        self.probability_redemption = 0

    def strategy_1(self):
        """Full focus on casting Holy Word Redemption."""
        self.probability_penance = 0
        self.probability_punishment = 0
        self.probability_redemption = 1

    def strategy_2(self):
        """Full focus on casting Holy Word Punishment."""
        self.probability_penance = 0
        self.probability_punishment = 1
        self.probability_redemption = 0

    def strategy_3(self):
        """Focus on Penance if Punishment is not an option."""
        self.probability_penance = 1
        self.probability_punishment = 0
        self.probability_redemption = 0

    def battle_analysis(self, opponents, allies):
        """
        Analyzes the battle situation and determines the next action based on conditions:
        - Redemption casting based on the number of alive allies.
        - Choose Penance or Punishment based on specific conditions.
        """
        # Check how many allies are alive
        alive_allies = [ally for ally in allies if ally.hp > 0]
        alive_allies_count = len(alive_allies)

        # Sort hp and resistance from low to high
        sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
        sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)

        # Find opponent heroes with/without Holy Word Punishment debuff
        opponents_with_punishment = [opponent for opponent in opponents if opponent.status.get('holy_word_punishment', False)]
        opponents_qty_with_punishment = len(opponents_with_punishment)
        opponents_without_punishment = [opponent for opponent in opponents if not any(debuff.name == "Holy Word Punishment" for debuff in opponent.debuffs)]
        opponents_qty_without_punishment = len(opponents_without_punishment)

        # Find ally heroes with/without Holy Word Redemption buff
        allies_with_redemption = [ally for ally in allies if ally.status.get('holy_word_redemption', False)]
        allies_qty_with_redemption = len(allies_with_redemption)
        allies_without_redemption = [ally for ally in allies if not any(buff.name == "Holy Word Redemption" for buff in ally.buffs)]
        allies_qty_without_redemption = len(allies_without_redemption)

        # Check if the previous action was Holy Word Redemption
        previous_action = self.previous_action if hasattr(self, "previous_action") else None

        # Eliminate low hp opponent
        if sorted_opponents[0].hp <= 17:
            self.strategy_3()
            return sorted_opponents[0]
        
        # 25% chance heal an low hp hero
        if sorted_allies[0].hp <= round(0.35 * sorted_allies[0].hp_max):
            if random.random() < 0.25:
                self.strategy_3()
                return sorted_allies[0]

        # Make sure holy word redemption will not be cast consecutively
        if previous_action == "Holy Word Redemption":
            if len(opponents) >= 2 and opponents_qty_with_punishment == 0:
                self.strategy_2()
                return random.sample(opponents, 2)
            elif len(opponents) > 2 and opponents_qty_with_punishment == 1:
                self.strategy_2()
                return random.sample(opponents_without_punishment, 2)
            else:
                self.strategy_3()
                return sorted_opponents[0]

        # Strategy to determine next move
        if alive_allies_count >= 3:
            if allies_qty_with_redemption == 0  or allies_qty_with_redemption == 1:
                # If none of the allies have Holy Word Redemption, cast it on a random ally
                self.strategy_1()
                return random.choice(allies_without_redemption)

            elif allies_qty_with_redemption == 2:
                # 30% chance to cast Holy Word Redemption, otherwise move to Punishment or Penance
                if random.random() < 0.3:
                    self.strategy_1()
                    return random.choice(allies_without_redemption)
                else:
                    if len(opponents) >= 2 and opponents_qty_with_punishment == 0:
                        self.strategy_2()
                        return random.sample(opponents, 2)
                    elif len(opponents) > 2 and opponents_qty_with_punishment == 1:
                        self.strategy_2()
                        return random.sample(opponents_without_punishment, 2)
                    else:
                        self.strategy_3()
                        return sorted_opponents[0]

            elif allies_qty_with_redemption >= 3:
                # If all have Redemption, choose either Penance or Punishment
                if len(opponents) >= 2 and opponents_qty_with_punishment == 0:
                        self.strategy_2()
                        return random.sample(opponents, 2)
                elif len(opponents) > 2 and opponents_qty_with_punishment == 1:
                    self.strategy_2()
                    return random.sample(opponents_without_punishment, 2)
                else:
                    self.strategy_3()
                    return sorted_opponents[0]

        if alive_allies_count == 2:
            if allies_qty_with_redemption == 0:
                # If none of the allies have Holy Word Redemption, cast it on a random ally
                self.strategy_1()
                return random.choice(allies_without_redemption)

            elif allies_qty_with_redemption == 1:
                # 30% chance to cast Holy Word Redemption, otherwise move to Punishment or Penance
                if random.random() < 0.3:
                    self.strategy_1()
                    return random.choice(allies_without_redemption)
                else:
                    if len(opponents) >= 2 and opponents_qty_with_punishment == 0:
                        self.strategy_2()
                        return random.sample(opponents, 2)
                    elif len(opponents) > 2 and opponents_qty_with_punishment == 1:
                        self.strategy_2()
                        return random.sample(opponents_without_punishment, 2)
                    else:
                        self.strategy_3()
                        return sorted_opponents[0]

            elif allies_qty_with_redemption > 1:
                # If all have Redemption, choose either Penance or Punishment
                if len(opponents) >= 2 and opponents_qty_with_punishment == 0:
                        self.strategy_2()
                        return random.sample(opponents, 2)
                elif len(opponents) > 2 and opponents_qty_with_punishment == 1:
                    self.strategy_2()
                    return random.sample(opponents_without_punishment, 2)
                else:
                    self.strategy_3()
                    return sorted_opponents[0]

        if alive_allies_count == 1:
            if allies_qty_with_redemption == 0:
                # If none of the allies have Holy Word Redemption, cast it on a random ally
                self.strategy_1()
                return random.choice(allies_without_redemption)
            else:
                # If all have Redemption, choose either Penance or Punishment
                if len(opponents) >= 2 and opponents_qty_with_punishment == 0:
                        self.strategy_2()
                        return random.sample(opponents, 2)
                elif len(opponents) > 2 and opponents_qty_with_punishment == 1:
                    self.strategy_2()
                    return random.sample(opponents_without_punishment, 2)
                else:
                    self.strategy_3()
                    return sorted_opponents[0]
        
        # Default behavior if less than 3 allies are alive or no conditions are met
        self.strategy_0()
        return random.choice(opponents)

    # AI chooses a skill based on current strategy
    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()  # Reset to default strategy at the beginning of each turn
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_penance, self.probability_redemption, self.probability_punishment]
        chosen_skill = random.choices(self.skills, weights=skill_weights)[0]
        self.previous_action = chosen_skill.name  # Track the previous action for future turns
        return chosen_skill

    # AI chooses the target for the chosen skill
    def ai_choose_target(self, chosen_skill, opponents, allies):
        chosen_opponent = self.preset_target
        return chosen_opponent

    # Helper method to find allies in critical health
    def find_critical_ally(self, sorted_allies):
        critical_hp_threshold = 0.3
        for ally in sorted_allies:
            if ally.hp / ally.hp_max < critical_hp_threshold:
                return ally
        return None
    
class Priest_Shadow(Priest):

    major = "Shadow"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major = self.__class__.major)
            self.add_skill(Skill(self, "Vampire Feast", self.vampire_feast, "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shadow Word Pain", self.shadow_word_pain, "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shadow Word Insanity", self.shadow_word_insanity, "single", skill_type= "damage", is_control_skill = True))

    def vampire_feast(self, other_hero):
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.shadow_resistance) * (3/4))
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

        if other_hero.status['shadow_word_pain'] == True:
          if len(self.allies) > 1:
            not_self_allies = [ally for ally in self.allies if ally != self]
            additional_healing_target = random.choice(not_self_allies)
            self.game.display_battle_info(f"{self.name} casts Vampire Feast at {other_hero.name}.")
            self.game.display_battle_info(f"{other_hero.take_damage(damage_dealt)}")
            self.game.display_battle_info(f"{self.take_healing(healing_amount)}")
            self.game.display_battle_info(f"Vampires absorb the energy from {other_hero.name}' Shadow Word Pain and will heal an extra ally hero")
            return additional_healing_target.take_healing(healing_amount_extra_hero)
          else:
            self.game.display_battle_info(f"{self.name} casts Vampire Feast at {other_hero.name}.")
            self.game.display_battle_info(f"{other_hero.take_damage(damage_dealt)}")
            self.game.display_battle_info(f"{self.take_healing(healing_amount)}")
            self.game.display_battle_info(f"Vampires absorb the energy from {other_hero.name}' Shadow Word Pain and will heal an extra ally hero")
            return self.take_healing(healing_amount_extra_hero)
        else:
          self.game.display_battle_info(f"{self.name} casts Vampire Feast at {other_hero.name}.")
          self.game.display_battle_info(f"{other_hero.take_damage(damage_dealt)}")
          return self.take_healing(healing_amount)

    def shadow_word_pain(self, other_hero):
        variation = random.randint(0, 5)
        actual_damage = self.damage + variation
        damage_dealt = round((actual_damage - other_hero.shadow_resistance)*(1/2))
        if other_hero.status['shadow_word_pain'] == False:
            other_hero.status['shadow_word_pain'] = True
            other_hero.shadow_word_pain_debuff_duration = 5  # Effect lasts for 4 rounds
            if damage_dealt > 0:
              other_hero.shadow_word_pain_continuous_damage = round((actual_damage - other_hero.shadow_resistance)*(1/3))
            else:
              other_hero.shadow_word_pain_continuous_damage = random.randint(1, 10)
            self.game.display_battle_info(f"{self.name} uses Shadow Word Pain on {other_hero.name}. {other_hero.name} feels continuous pain")
        else:
            self.game.display_battle_info(f"{self.name} uses Shadow Word Pain on {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def shadow_word_insanity(self, other_hero):
      if other_hero.status['shadow_word_insanity'] == False:
        if other_hero.status['magic_casting'] == True:
          result = self.interrupt_magic_casting(other_hero)
          other_hero.status['shadow_word_insanity'] = True
          other_hero.shadow_word_insanity_duration = 1
          for skill in self.skills:
            if skill.name == "Shadow Word Insanity":
              skill.if_cooldown = True
              skill.cooldown = 3
          return f"{self.name} casts Shadow Word Insanity on {other_hero.name}. {other_hero.name} is insane. {result}"
        else:
          other_hero.status['shadow_word_insanity'] = True
          other_hero.shadow_word_insanity_duration = 1
          for skill in self.skills:
            if skill.name == "Shadow Word Insanity":
              skill.if_cooldown = True
              skill.cooldown = 3
          return f"{self.name} casts Shadow Word Insanity on {other_hero.name}. {other_hero.name} is insane."
      else:
        for skill in self.skills:
            if skill.name == "Shadow Word Insanity":
              skill.if_cooldown = True
              skill.cooldown = 3
        return f"{self.name} casts Shadow Word Insanity on {other_hero.name}. But {other_hero.name} has already been insane."

# Battling Strategy_________________________________________________________

    def strategy_0(self):
        self.probability_vampire_feast = 0.5
        self.probability_shadow_word_pain = 0.5
        self.probability_shadow_word_insanity = 0

    def strategy_1(self):
        self.probability_vampire_feast = 0
        self.probability_shadow_word_pain = 0
        self.probability_shadow_word_insanity = 1

    def strategy_2(self):
        self.probability_vampire_feast = 0.7
        self.probability_shadow_word_pain = 0.3
        self.probability_shadow_word_insanity = 0

    def strategy_3(self):
        self.probability_vampire_feast = 1
        self.probability_shadow_word_pain = 0
        self.probability_shadow_word_insanity = 0

    def strategy_4(self):
        self.probability_vampire_feast = 0
        self.probability_shadow_word_pain = 1
        self.probability_shadow_word_insanity = 0

    def battle_analysis(self, opponents, allies):
        # Define high-risk DPS hero list
        high_risk_dps_heroes = ['Mage_Comprehensiveness', 'Rogue_Comprehensiveness', 'Warrior_Comprehensiveness', 'Warlock_Destruction']

        # Sort hp and resistance from low to high
        sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
        sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
        sorted_opponents_resistance = sorted(opponents, key=lambda hero: hero.shadow_resistance, reverse=False)

        # Find heroes with shadow_word_pain or shadow_bolt debuffs
        opponents_with_pain = [opponent for opponent in opponents if opponent.status.get('shadow_word_pain', False)]
        sorted_opponents_with_pain_resistance = sorted(opponents_with_pain, key=lambda hero: hero.shadow_resistance, reverse=False)
        opponents_without_pain = [opponent for opponent in opponents if not opponent.status.get('shadow_word_pain', False)]
        opponents_with_bolt = [opponent for opponent in opponents if opponent.status.get('shadow_bolt', False)]

        # Eliminate low hp hero
        if sorted_opponents[0].hp < round((self.damage - sorted_opponents[0].shadow_resistance) * (3/4)):
          self.strategy_3()
          return sorted_opponents[0]

        # Prioritize using Shadow Word Insanity if it's available
        for skill in self.skills:
            if skill.name == "Shadow Word Insanity" and not skill.if_cooldown:
                # If an enemy is casting, interrupt them
                casting_opponents = [opponent for opponent in opponents if opponent.status.get('magic_casting', False)]
                if casting_opponents:
                    self.strategy_1()
                    return casting_opponents[0]

                # If no one is casting but there are high-risk DPS heroes, target them
                high_risk_targets = [opponent for opponent in opponents if opponent.__class__.__name__ in high_risk_dps_heroes]
                if high_risk_targets:
                    self.strategy_1()
                    return random.choice(high_risk_targets)

                # Cast Shadow Word Insanity to a random target
                self.strategy_1()
                return random.choice(opponents)

        # Prioritize attacking heroes with shadow bolt debuff
        if opponents_with_bolt:
            # Check if any of the heroes with shadow bolt also have a shadow word pain debuff
            for opponent in opponents_with_bolt:
                if opponent.status.get('shadow_word_pain', False):
                    self.strategy_3()  # Use strategy 3 when attacking this target with Vampire Feast
                    return opponent  # Return the target with both shadow bolt and shadow word pain debuff

            # If no hero with shadow bolt has a shadow word pain debuff, use strategy 2
            self.strategy_2()
            return opponents_with_bolt[0]  # Return the first hero with a shadow bolt debuff

        # Apply shadow word pain on the opponent with the lowest shadow resistance if no opponent in pain
        # Use Vampire Feast on heroes with shadow_word_pain 
        if opponents_with_pain:
          if opponents_without_pain:
            if random.random() < 0.25:
              self.strategy_4()
              return random.choice(opponents_without_pain)
          else:
            self.strategy_3()
            return sorted_opponents_with_pain_resistance[0]
        else:
            self.strategy_4()
            return sorted_opponents_resistance[0]

        # If no special conditions, attack the opponent with the lowest HP
        self.strategy_0()
        return sorted_opponents[0]

    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_vampire_feast, self.probability_shadow_word_pain, self.probability_shadow_word_insanity]
        chosen_skill = random.choices(self.skills, weights=skill_weights)[0]
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
        chosen_opponent = self.preset_target
        return chosen_opponent

class Priest_Devine(Priest):

    major = "Devine"

    def __init__(self, sys_init, name, group, is_player_controlled):
            super().__init__(sys_init, name, group, is_player_controlled, major = self.__class__.major)
            self.add_skill(Skill(self, "Holy Fire", self.holy_fire, "single", skill_type= "damage_healing"))
            self.add_skill(Skill(self, "Powerful Healing", self.powerful_healing, "single", skill_type= "healing",is_instant_skill = False))
            self.add_skill(Skill(self, "Holy Word Prayer", self.holy_word_prayer, "multi", skill_type= "healing"))

    def holy_fire(self, other_hero, target_type):
      healing_amount_base = 13
      variation = random.randint(-2, 2)
      if target_type == "ally": # healing effect
        if other_hero.status['holy_fire'] == False:
          other_hero.status['holy_fire'] = True
          other_hero.holy_fire_duration = 2
          healing_amount = healing_amount_base + variation
          other_hero.holy_fire_continuous_healing = round(healing_amount * 0.7)
          self.game.display_battle_info(f"{self.name} casts Holy Fire on {other_hero.name}. {other_hero.name} is receiving continuous healing.")
          return other_hero.take_healing(healing_amount)
        else:
          healing_amount = healing_amount_base + variation
          other_hero.holy_fire_duration = 2
          self.game.display_battle_info(f"{self.name} casts Holy Fire on {other_hero.name}.")
          return other_hero.take_healing(healing_amount)
      elif target_type =="opponent": # damage effect
        variation = random.randint(-2, 2)
        actual_damage = healing_amount_base + variation
        damage_dealt = actual_damage #damage discard opponent's defense
        damage_dealt = max(damage_dealt, 0) # Ensure damage dealt is at least 0
        self.game.display_battle_info(f"{self.name} casts Holy Fire at {other_hero.name}.")
        return f"{other_hero.take_damage(damage_dealt)}"

    def powerful_healing(self, other_hero):
      healing_amount = round(self.hp_max * 0.5)
      # If in Holy Infusion status, cast instantly
      if self.status['holy_infusion']:
        self.game.display_battle_info(f"{self.name} casts Powerful Healing instantly on {other_hero.name} due to Holy Infusion!")
        self.status['holy_infusion'] = False  # Reset the status after use
        return other_hero.take_healing(healing_amount)

      if self.status['magic_casting'] == False:
        self.status['magic_casting'] = True
        self.game.display_battle_info(f"{self.name} is casting Powerful Healing on {other_hero.name}.")
        self.magic_casting_duration = 1
        for skill in self.skills:
         if skill.name == "Powerful Healing":
          return self.magic_casting(skill, other_hero)

      elif self.status['magic_casting'] == True:
        self.status['magic_casting'] = False
        if other_hero.hp > 0:
          self.game.display_battle_info(f"{self.name} casts Powerful Healing on {other_hero.name}.")
          return other_hero.take_healing(healing_amount)
        else:
          return f"{self.name} tries to cast Powerful Healing on {other_hero.name}, but {other_hero.name} has already been defeated."

    def holy_word_prayer(self, other_heroes):
      basic_healing = round(self.hp_max / 3.5)
      self.game.display_battle_info(f"{self.name} casts Holy Word Prayer on all allies")

      # Check for Holy Infusion chance
      if self.hp <= 0.50 * self.hp_max and not self.status['holy_infusion'] and self.holy_infusion_cooldown == 0:
        accuracy = 90  # 90% chance activating Holy Infusion
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          self.status['holy_infusion'] = True
          self.holy_infusion_cooldown = 4  # Set cooldown for Holy Infusion
          results  = []
          for skill in self.skills:
            if skill.name == "Holy Word Prayer":
              skill.if_cooldown = True
              skill.cooldown = 3
          for hero in other_heroes:
            variation = random.randint(-2, 2)
            healing_amount = basic_healing + variation
            results.append(hero.take_healing(healing_amount))
          string = " ".join(results)
          results = []
          results.append(string)
          results.append(f"{YELLOW}To deal with the critical situation, {self.name} enters Holy Infusion state! their next Powerful Healing becomes instant.{RESET}")
          return "\n".join(results)

        else:
          results  = []
          for skill in self.skills:
            if skill.name == "Holy Word Prayer":
              skill.if_cooldown = True
              skill.cooldown = 3
          for hero in other_heroes:
            variation = random.randint(-2, 2)
            healing_amount = basic_healing + variation
            results.append(hero.take_healing(healing_amount))
          return " ".join(results)
      else:
        results  = []
        for skill in self.skills:
          if skill.name == "Holy Word Prayer":
            skill.if_cooldown = True
            skill.cooldown = 3
        for hero in other_heroes:
          variation = random.randint(-2, 2)
          healing_amount = basic_healing + variation
          results.append(hero.take_healing(healing_amount))
        return " ".join(results)

# Battling Strategy_________________________________________________________

    def strategy_0(self):
      self.probability_holy_fire = 0.4
      self.probability_powerful_healing = 0.3
      self.probability_holy_word_prayer = 0.3

    def strategy_1(self):
      self.probability_holy_fire = 1
      self.probability_powerful_healing = 0
      self.probability_holy_word_prayer = 0

    def strategy_2(self):
      self.probability_holy_fire = 0
      self.probability_powerful_healing = 1
      self.probability_holy_word_prayer = 0

    def strategy_3(self):
      self.probability_holy_fire = 0
      self.probability_powerful_healing = 0
      self.probability_holy_word_prayer = 1

    def strategy_4(self):
      self.probability_holy_fire = 0.1
      self.probability_powerful_healing = 0
      self.probability_holy_word_prayer = 0.9

    def battle_analysis(self, opponents, allies):
      # Sort hp from low to high
      sorted_opponents = sorted(opponents, key=lambda hero: hero.hp, reverse=False)
      sorted_allies = sorted(allies, key=lambda hero: hero.hp, reverse=False)
      sorted_allies_excludes_self = sorted_allies.copy()
      for ally in sorted_allies_excludes_self:
        if ally == self:
          sorted_allies_excludes_self.remove(ally)
      # Priority targets tackling strategy
      if self.status['holy_infusion'] == True:
        self.strategy_2()
        ally = sorted_allies[0]
        return ally

      for skill in self.skills:
        if skill.name == "Holy Word Prayer":
          if skill.if_cooldown == False:
            if len(sorted_allies) >= 2:
              if sorted_allies[0].hp <= round(0.65 * sorted_allies[0].hp_max) and sorted_allies[1].hp <= round(0.65 * sorted_allies[1].hp_max):
                self.strategy_3()
                ally = sorted_allies
                return ally

      if len(sorted_allies_excludes_self) >= 1:
        if self.hp >= round(0.85 * self.hp_max) and sorted_allies_excludes_self[0].hp <= round(0.50 * sorted_allies_excludes_self[0].hp_max):
          self.strategy_2()
          ally = sorted_allies_excludes_self[0]
          return ally

      if len(sorted_allies) >= 1:
        if sorted_allies[0].hp <= round(0.50 * sorted_allies[0].hp_max):
          self.strategy_1()
          ally = sorted_allies[0]
          opponent = sorted_opponents[0]
          accuracy = 70
          roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
          if roll <= accuracy:
            return ally
          else:
            return opponent


      # If no priority targets, then random choose one target and utilize corresponding strategy
      opponent = sorted_opponents[0]
      self.strategy_1()
      return opponent


    def ai_choose_skill(self, opponents, allies):
        self.strategy_0()
        self.preset_target = self.battle_analysis(opponents, allies)
        skill_weights = [self.probability_holy_fire, self.probability_powerful_healing, self.probability_holy_word_prayer]
        #available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        chosen_skill = random.choices(self.skills, weights = skill_weights)[0]
        #chosen_skill = random.choice(available_skills)
        return chosen_skill

    def ai_choose_target(self, chosen_skill, opponents, allies):
          chosen_opponent = self.preset_target
          return chosen_opponent