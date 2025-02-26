import random
from heroes import *
from skills import *
from game.game import Game

class HeroGenerator:

    def __init__(self, sys_init):

      self.warrior_names_list = ["Ragnar", "Thorin", "Wrathe"]
      self.mage_names_list = ["Arcanis", "Eldoria", "Thalindra"]
      self.priset_names_list = ["Lioren", "Seraphina", "Aldric"]
      self.paladin_names_list = ["Galahad", "Percival", "Bors"]
      self.rogue_names_list = ["Vanishan", "Nighthawk", "Venombane"]
      self.necromancer_names_list = ["Mortis Darkwood", "Lysander Shadowgrave", "Vespera Nightshade"]
      self.warlock_names_list = ["Draximus", "Morvina", "Thalrok"]
      self.death_knight_names_list = ["Mordrath the Fallen","Varkul Dreadbane","Xal'Thazar the Unyielding"  ]
      self.sys_init = sys_init

      self.hero_classes = {
            # Warrior
            Warrior_Comprehensiveness: self.warlock_names_list,
            # Mage
            Mage_Comprehensiveness: self.mage_names_list,
            # Priest
            Priest_Comprehensiveness: self.priset_names_list,
            Priest_Shelter: self.priset_names_list,
            Priest_Discipline: self.priset_names_list,
            Priest_Shadow: self.priset_names_list,
            Priest_Devine: self.priset_names_list,
            # Paladin
            Paladin_Comprehensiveness: self.paladin_names_list,
            # Rogue
            Rogue_Comprehensiveness: self.rogue_names_list,
            # Necromancer
            Necromancer_Comprehensiveness: self.necromancer_names_list,
            # Warlock
            Warlock_Comprehensiveness: self.warlock_names_list,
            Warlock_Affliction: self.warlock_names_list,
            Warlock_Destruction: self.warlock_names_list,
            # Death Knight
            Death_Knight_Frost: self.death_knight_names_list,
            Death_Knight_Plague: self.death_knight_names_list
            }
      self.hero_classes_list = list(self.hero_classes.keys())
      self.used_names = set()

    def generate_hero(self, group, hero_class):
        available_name = [name for name in self.hero_classes[hero_class] if name not in self.used_names]
        if not available_name:
            raise ValueError(f"No more unique names available for {hero_class.__name__}.")
        name = random.choice(available_name)
        self.used_names.add(name)
        return hero_class(self.sys_init, name, group, False)

    def generate_hero_simulation(self, group, hero_class): #Simulation system, name doesn't matter
        available_name = [name for name in self.hero_classes[hero_class]]
        name = random.choice(available_name)
        self.used_names.add(name)
        return hero_class(self.sys_init, name, group, False)

    def generate_heroes(self, group, count = 2):
        heroes = []
        for _ in range(count):
            random_list = list(self.hero_classes.keys())
            random.shuffle(random_list)
            hero_class = random.choice(random_list)  # Select a random hero class
            heroes.append(self.generate_hero(group, hero_class))
        return heroes

    def generate_heroes_specific_class(self, group, hero_class_list):
        count = len(hero_class_list)
        heroes = []
        for i in range(count):
            hero_class = hero_class_list[i]
            #heroes.append(self.generate_hero(group, hero_class)) # Normal Mode, no repeated names
            heroes.append(self.generate_hero_simulation(group, hero_class)) # Battle Simulation Mode, repeated names allowed
        return heroes