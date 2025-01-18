from heroes.hero import Hero  # Explicit import of Hero class
from skills.skill import Skill  # Explicit import of Skill class

class Mage(Hero):

    profession = "Mage"
    damage_interval = (70, 80)  # Mages usually have high damage potential
    defense_interval = (25, 35)  # Mages have lower physical defense
    magic_resistance_interval = (45, 55)  # Mages excel in magical resistance
    agility_interval = (20, 30) # Mages have lower agility
    hp_interval = (70, 80)  # Mages typically have less HP than warriors
    #skills_list = ["fireball", "ice_blast", "arcane_shield"]

    def __init__(self, name, group, is_player_controlled=False):
        super().__init__(name, self.profession, group, is_player_controlled)
        self.damage_type = "magical"
        # define skills
        self.add_skill(Skill(self, "Fireball", self.fireball, target_type = "single", skill_type= "damage"))
        self.add_skill(Skill(self, "Arcane Missiles", self.arcane_missiles, target_type = "multi", skill_type= "damage", target_qty= 2))
        self.add_skill(Skill(self, "Frost Bolt", self.frost_bolt, target_type = "single", skill_type= "damage"))

    def fireball(self, other_hero):
        variation = random.randint(-5, 5)
        actual_damage = self.damage + variation
        if self.damage_type == "physical":
            damage_dealt = actual_damage - other_hero.defense
        else:  # magic damage
            damage_dealt = actual_damage - other_hero.magic_resistance
            # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
          # Apply damage to the other hero's HP
        print(f"{self.name} casts Fireball at {other_hero.name}.")
        return other_hero.take_damage(damage_dealt)

    def arcane_missiles(self, other_heros):
        if not isinstance(other_heros, list):
          other_heros = [other_heros]
        results = []
        variation = random.randint(-3, 3)
        actual_damage = self.damage + variation
        selected_opponents = other_heros
        #selected_opponents = random.sample(other_heros, 2) if len(other_heros) > 1 else other_heros
        for opponent in selected_opponents:
            damage_dealt = math.ceil((actual_damage - opponent.magic_resistance) * 2/3)
            print(f"{self.name} casts Arcane Missiles at {opponent.name}.")
            results.append(opponent.take_damage(damage_dealt))
        return "\n".join(results)

    def frost_bolt(self, other_hero):
        if other_hero.status['cold'] == False:
          agility_before_reducing = other_hero.agility
          other_hero.agility_reduced_amount_by_frost_bolt = math.ceil(other_hero.original_agility * 0.70)  # Reduce target's agility by 70%
          #print(f"{RED} {other_hero.name}'s agility_reduced_amount_by_frost_bolt is {} ")
          other_hero.agility = other_hero.agility - other_hero.agility_reduced_amount_by_frost_bolt
          other_hero.status['cold'] = True
          other_hero.status['normal'] = False
          other_hero.cold_duration = 2
          print(f"{self.name} attacks {other_hero.name} with Frost Bolt, {other_hero.name} is feeling cold and their agility is reduced from {agility_before_reducing} to {other_hero.agility}.")
        else:
            print(f"{self.name} attacks {other_hero.name} with Frost Bolt")
        variation = random.randint(-2, 2)
        actual_damage = self.damage + variation
        damage_dealt = math.ceil((actual_damage - other_hero.magic_resistance) * 4/5)
            # Ensure damage dealt is at least 0
        damage_dealt = max(damage_dealt, 0)
          # Apply damage to the other hero's HP
        return other_hero.take_damage(damage_dealt)

    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])