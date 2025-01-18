import curses
from heroes import *
from skills import *
from game.game import Game
from game.hero_generator import HeroGenerator
from system.system_initialization import System_initialization
from system.game_interface import GameInterface

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Mock Hero class to simulate player and opponent heroes
class Hero:
    def __init__(self, name, hp, hp_max, buffs, debuffs):
        self.name = name
        self.hp = hp
        self.hp_max = hp_max
        self.buffs = buffs
        self.debuffs = debuffs

# Function to simulate a simple test environment
def test_interface(stdscr):
    # Initialize the interface
    interface = GameInterface()
    interface.init_windows(stdscr)

    # Create mock data for heroes
    player_heroes = [
        Hero("Warrior", 80, 100, ["Shield"], ["Burn"]),
        Hero("Mage", 50, 50, ["Focus"], []),
    ]
    opponent_heroes = [
        Hero("Rogue", 60, 60, [], ["Poison"]),
        Hero("Paladin", 120, 150, ["Blessing"], ["Slow"]),
    ]

    # Update the interface with the mock heroes
    interface.update_player_heroes(player_heroes)
    interface.update_opponent_heroes(opponent_heroes)

    # Simulate adding logs to the game log window
    for i in range(15):
        interface.update_game_log(f"Event {i + 1}: A test log entry.")

    # Refresh and display the interface
    interface.refresh_windows()

    # Keep displaying until the user presses 'q'
    while True:
        key = stdscr.getch()
        if key == ord('q'):  # Quit on 'q'
            break

# Run the test function
if __name__ == "__main__":
    curses.wrapper(test_interface)