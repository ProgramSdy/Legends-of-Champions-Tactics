from heroes.hero import Hero  # Explicit import of Hero class
from skills.skill import Skill  # Explicit import of Skill class

class Rogue(Hero):

    profession = "Rogue"
    damage_interval = (75, 85)
    defense_interval = (34, 40)
    magic_resistance_interval = (15, 25)
    agility_interval = (35, 45)
    hp_interval = (75, 85)


    def __init__(self, name, group, is_player_controlled=False):
            super().__init__(name, self.profession, group, is_player_controlled)
            self.damage_type = "physical"
            #self.skills = self.random_skills()
            self.add_skill(Skill(self, "Sharp Blade", self.sharp_blade, target_type = "single", skill_type= "damage",))
            self.add_skill(Skill(self, "Poisoned Dagger", self.poisoned_dagger, target_type = "single", skill_type= "damage"))
            self.add_skill(Skill(self, "Shadow Evasion", self.shadow_evasion, target_type = "single", skill_type= "buffs", target_qty= 0))

    def sharp_blade(self, other_hero):
        variation = random.randint(-5, 0)
        actual_damage = self.damage + variation
        damage_dealt = actual_damage - other_hero.defense
        accuracy = 50  # Bleeding effect has a 50% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy and other_hero.status['bleeding_sharp_blade'] == False:
            other_hero.status['bleeding_sharp_blade'] = True
            other_hero.status['normal'] = False
            other_hero.sharp_blade_debuff_duration = 3
            if damage_dealt > 0:
              other_hero.sharp_blade_continuous_damage = random.randint(8, 14)
            else:
              other_hero.sharp_blade_continuous_damage = random.randint(5, 10)
            print(f"{self.name} attacks {other_hero.name} with Sharp Blade, {other_hero.name} is bleeding.")
        else:
            print(f"{self.name} attacks {other_hero.name} with Sharp Blade")
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    def poisoned_dagger(self, other_hero): #poisoned dagger debuff can stack twice, and continuous damage from poison is a magial damage
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = int((actual_damage - other_hero.defense)/2)
        accuracy = 85  # Poinsed effect has a 85% chance to succeed
        roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
        if roll <= accuracy:
          if other_hero.status['poisoned_dagger'] == False:
              other_hero.status['poisoned_dagger'] = True
              other_hero.status['normal'] = False
              other_hero.poisoned_dagger_debuff_duration = 4
              other_hero.poisoned_dagger_stacks += 1
              if damage_dealt > 0:
                other_hero.poisoned_dagger_continuous_damage = math.ceil((actual_damage - other_hero.magic_resistance)/4)
              else:
                other_hero.poisoned_dagger_continuous_damage = random.randint(1, 10)
              print(f"{self.name} attacks {other_hero.name} with Poisoned Dagger, {other_hero.name} is poisoned.")
          elif other_hero.status['poisoned_dagger'] == True and other_hero.poisoned_dagger_stacks == 1:
              other_hero.poisoned_dagger_stacks += 1
              if damage_dealt > 0:
                other_hero.poisoned_dagger_continuous_damage += math.ceil((actual_damage - other_hero.magic_resistance)/4)
              else:
                other_hero.poisoned_dagger_continuous_damage += random.randint(1, 10)
              print(f"{self.name} attacks {other_hero.name} with Poisoned Dagger again, {other_hero.name}'s poisnoning has worsened.")
        else:
            print(f"{self.name} attacks {other_hero.name} with Poisoned Dagger")
        # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
        # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)



    def shadow_evasion(self):
        self.evasion_capability = 100
        self.status['shadow_evasion'] = True
        self.shadow_evasion_buff_duration = 1
        for skill in self.skills:
            if skill.name == "Shadow Evasion":
              skill.if_cooldown = True
              skill.cooldown = 2
        return f"{self.name} has used Shadow Evasion. {self.name}'s figure vanished on the battlefield"


    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])