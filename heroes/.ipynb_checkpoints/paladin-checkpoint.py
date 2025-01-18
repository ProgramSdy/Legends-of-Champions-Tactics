from heroes.hero import Hero  # Explicit import of Hero class
from skills.skill import Skill  # Explicit import of Skill class

class Paladin(Hero):

    profession = "Paladin"
    damage_interval = (60, 70)
    defense_interval = (45, 55)
    magic_resistance_interval = (30, 40)
    agility_interval = (5, 15)
    hp_interval = (105, 115)



    def __init__(self, name, group, is_player_controlled=False):
            super().__init__(name, self.profession, group, is_player_controlled)
            self.damage_type = "physical"
            self.add_skill(Skill(self, "Crusader Strike", self.crusader_strike, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shield of Righteous", self.shield_of_righteous, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Flash of Light", self.flash_of_light, "single", skill_type= "healing"))

    def crusader_strike(self, other_hero):
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        faces_dice = [1, 2, 3]
        roll = random.choice(faces_dice)
        damage_type = "physical"
        if roll == 3:
            damage_type = "magical"
            damage_dealt = actual_damage - other_hero.magic_resistance #33% chance turn into magical damage
        else:
            damage_dealt = actual_damage - other_hero.defense #66% chance attack as physical damage
        damage_dealt = max(damage_dealt, 0)
          # Apply damage to the other hero's HP
        print(f"{self.name} uses Crusader Strike on {other_hero.name} with {damage_type} damage.")
        return other_hero.take_damage(damage_dealt)

    def shield_of_righteous(self, other_hero):
        accuracy = 75  # Shield of Righteous has a 75% chance to activate the defense increasing effect
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          if self.shield_of_righteous_stacks < 2: #shield of righteous effect can stack for two times.
           defense_before_increasing = self.defense
           defense_increased_amount_by_shield_of_righteous_single = math.ceil(self.original_defense * 0.12)  # Increase hero's defense by 12%
           self.defense_increased_amount_by_shield_of_righteous = self.defense_increased_amount_by_shield_of_righteous + defense_increased_amount_by_shield_of_righteous_single  # Defense increase accumulated
           self.defense = self.defense + defense_increased_amount_by_shield_of_righteous_single
           self.shield_of_righteous_stacks += 1
           self.defense_buff_duration = 2
           print(f"{self.name} attacks {other_hero.name} with Shield of Righteous, defense of {self.name} has increased from {defense_before_increasing} to {self.defense}.")
          else:
            self.defense_buff_duration = 2
            print(f"{self.name} attacks {other_hero.name} with Shield of Righteous. Shield of Righteous buff duration refreshed")
        else:
            print(f"{self.name} attacks {other_hero.name} with Shield of Righteous.")
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.defense)/3*2)
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def flash_of_light(self, other_hero):
        variation = random.randint(-3, 3)
        healing_amount_base = 15
        healing_amount = healing_amount_base + variation
        print(f"{self.name} casts Flash of Light on {other_hero.name}.")

        return other_hero.take_healing(healing_amount)

    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])