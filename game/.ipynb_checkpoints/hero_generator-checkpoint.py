import random
from heroes import *
from skills.skill import Skill
from game.game import Game

class HeroGenerator:
    def __init__(self):
      self.hero_classes = {
            Warrior: ["Ragnar", "Thorin", "Wrathe"],
            Mage: ["Arcanis", "Eldoria", "Thalindra"],
            Paladin: ["Galahad", "Percival", "Bors"],
            Priest: ["Lioren", "Seraphina", "Aldric"],
            Rogue: ["Vanishan", "Nighthawk", "Venombane"]
      }
      self.used_names = set()

    def generate_hero(self, group, hero_class):
        available_name = [name for name in self.hero_classes[hero_class] if name not in self.used_names]
        if not available_name:
            raise ValueError(f"No more unique names available for {hero_class.__name__}.")
        name = random.choice(available_name)
        self.used_names.add(name)
        return hero_class(name, group)

    def generate_heroes(self, group, count = 2):
        heroes = []
        for _ in range(count):
            hero_class = random.choice(list(self.hero_classes.keys()))  # Select a random hero class
            heroes.append(self.generate_hero(group, hero_class))
        return heroes