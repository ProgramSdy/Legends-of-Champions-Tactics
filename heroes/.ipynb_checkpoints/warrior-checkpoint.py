from heroes.hero import Hero  # Explicit import of Hero class
from skills.skill import Skill  # Explicit import of Skill class

class Warrior(Hero):

    profession = "Warrior"
    damage_interval = (65, 75)
    defense_interval = (50, 60)
    magic_resistance_interval = (20, 30)
    agility_interval = (10, 20)
    hp_interval = (95, 105)
    #skills_list = ["slash", "shield_bash", "armor_breaker"]


    def __init__(self, name, group, is_player_controlled=False):
            super().__init__(name, self.profession, group, is_player_controlled)
            self.damage_type = "physical"
            #self.skills = self.random_skills()
            self.add_skill(Skill(self, "Slash", self.slash, target_type = "single", skill_type= "damage",))
            self.add_skill(Skill(self, "Shield Bash", self.shield_bash, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Armor Breaker", self.armor_breaker, target_type = "single", skill_type= "damage"))

    def slash(self, other_hero):
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        if self.damage_type == "physical":
            damage_dealt = actual_damage - other_hero.defense
        else:  # magic damage
            damage_dealt = actual_damage - other_hero.magic_resistance
            # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
          # Apply damage to the other hero's HP
        print(f"{self.name} attacks {other_hero.name} with Slash.")
        return other_hero.take_damage(damage_dealt)

    def shield_bash(self, other_hero):
        accuracy = 70  # Shield Bash has a 70% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
            other_hero.status['stunned'] = True
            other_hero.status['normal'] = False
            other_hero.stun_duration += 1
            print(f"{self.name} attacks {other_hero.name} with Shield Bash, {other_hero.name} is stunned.")
        else:
            print(f"{self.name} attacks {other_hero.name} with Shield Bash")
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        if self.damage_type == "physical":
            damage_dealt = int((actual_damage - other_hero.defense)/2)
        else:  # magic damage
            damage_dealt = actual_damage - other_hero.magic_resistance
            # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
          # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def armor_breaker(self, other_hero):
        damage_dealt = self.random_in_range((8, 14))  # Small damage
        if other_hero.armor_breaker_stacks < 3:
            defense_before_reducing = other_hero.defense
            defense_reduced_amount_by_armor_breaker_single = math.ceil(other_hero.original_defense * 0.15)  # Reduce target's defense by 15%
            other_hero.defense_reduced_amount_by_armor_breaker = other_hero.defense_reduced_amount_by_armor_breaker + defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
            #print(f"{RED}{other_hero.name}'s defense reduced amount:' {other_hero.defense_reduced_amount_by_armor_breaker}, original defense: {other_hero.original_defense}{RESET}")
            other_hero.defense = other_hero.defense - defense_reduced_amount_by_armor_breaker_single  # Reduce target's defense by 15%
            other_hero.armor_breaker_stacks += 1
            other_hero.defense_debuff_duration = 2  # Effect lasts for 2 rounds
            print(f"{self.name} uses Armor Breaker on {other_hero.name}, reducing their defense from {defense_before_reducing} to {other_hero.defense}.")
        else:
            other_hero.defense_debuff_duration = 2  # Effect lasts for 2 rounds
            print(f"{self.name} uses Armor Breaker on {other_hero.name}, but {other_hero.name}'s Armor Breaker effect cannot be further stacked. Armor Breaker debuff duration refreshed")
        return other_hero.take_damage(damage_dealt)

    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])