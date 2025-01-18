from heroes import *
from skills.skill import Skill
from game.game import Game
from game.hero_generator import HeroGenerator
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

def main():
    # Generate heroes for player and opponent
    Daoyu = Priest("Daoyu", "Group_A", True)
    Yiquan = Mage("Yiquan", "Group_A")
    Evelyn = Rogue("Evelyn", "Group_A")
    Wrathe = Warrior("Wrathe", "Group_B")
    Arcanis = Mage("Arcanis", "Group_B")
    Percival = Paladin("Percival", "Group_B")

    #Test Hero
    #opponent_heroes = [Wrathe, Arcanis, Percival]
    
    #Hero Generator
    generator = HeroGenerator()
    opponent_heroes = generator.generate_heroes("Group_B", 3)
    player_heroes = [Daoyu, Yiquan, Evelyn]
    game = Game(player_heroes, opponent_heroes)
    game.play_game()

if __name__ == "__main__":
    main()