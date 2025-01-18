from heroes.hero import Hero  # Explicit import of Hero class
from skills.skill import Skill  # Explicit import of Skill class

class Priest(Hero):

    profession = "Priest"
    damage_interval = (55, 65)
    defense_interval = (30, 40)
    magic_resistance_interval = (40, 50)
    agility_interval = (15, 25)
    hp_interval = (85, 95)



    def __init__(self, name, group, is_player_controlled=False):
            super().__init__(name, self.profession, group, is_player_controlled)
            self.damage_type = "magical"
            self.add_skill(Skill(self, "Holy Smite", self.holy_smite, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shadow Word Pain", self.shadow_word_pain, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Binding Heal", self.binding_heal, "single", skill_type= "healing"))

    def holy_smite(self, other_hero):
        variation = random.randint(0, 5)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.magic_resistance
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        print(f"{self.name} casts Holy Smite at {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def shadow_word_pain(self, other_hero):
        variation = random.randint(0, 5)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.magic_resistance)*(1/2))
        if other_hero.status['shadow_word_pain'] == False:
            other_hero.status['shadow_word_pain'] = True
            #print(f"{RED}{other_hero.name}'s shadow word pain status is {other_hero.status['shadow_word_pain']}{RESET}")
            other_hero.shadow_word_pain_debuff_duration = 4  # Effect lasts for 3 rounds
            if damage_dealt > 0:
              other_hero.shadow_word_pain_continuous_damage = math.ceil(damage_dealt/2)
            else:
              other_hero.shadow_word_pain_continuous_damage = random.randint(1, 10)
            print(f"{self.name} uses Shadow Word Pain on {other_hero.name}. {other_hero.name} feels continuous pain")
        else:
            print(f"{self.name} uses Shadow Word Pain on {other_hero.name}.")
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
          print(f"{self.name} casts Binding Heal on {other_hero.name}.")
          return other_hero.take_healing(healing_amount_1)
        else:
          print(f"{self.name} casts Binding Heal on {other_hero.name}.")
          results.append(other_hero.take_healing(healing_amount_1))
          print(f"{self.name} casts Binding Heal on {self.name}.")
          results.append(self.take_healing(healing_amount_2))
          return "\n".join(results)

    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])