import pygame
import sys
from heroes import *
from skills import *
from game.game import Game
from game.hero_generator import HeroGenerator
from system.system_initialization import System_initialization
from system.game_interface import GameInterface
import os

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

def main():
    
    sys_init = System_initialization()
    sys_init.initialize()

    # Initialize the game interface
    interface = GameInterface(width=1200, height=800)
    interface.initialize_window()
  

    # Player hero generator__________________________________________
    '''
    generator_player = HeroGenerator(sys_init)
    name_list = ["Daoyu", "Yiquan", "Evelyn"]
    #name_list = ["Yiquan", "Evelyn"]
    player_heroes = generator_player.generate_heroes("Group_A", 2)
    i = 0
    for hero in player_heroes:
      hero.name = name_list[i]
      i += 1

    for hero in player_heroes:
      if hero.name == 'Player 1':
        hero.is_player_controlled = True
      if hero.name == 'Player 2':
        hero.is_player_controlled = False
      if hero.name == 'Player 3':
        hero.is_player_controlled = False
    '''
    Player_1 = Death_Knight_Frost(sys_init, "Arthas", "Group_A", True)
    Player_2 = Death_Knight_Plague(sys_init, "Shadow_eye", "Group_A", True)
    player_heroes = [Player_1, Player_2]

    

    # Opponent hero generator__________________________________________
    '''
    generator_ai = HeroGenerator(sys_init)
    opponent_heroes = generator_ai.generate_heroes("Group_B", 2)
    '''
    Galahad = Warrior_Comprehensiveness(sys_init, "Bors", "Group_B", False)
    Deepseer = Priest_Discipline(sys_init,"Deepseer", "Group_B", False)
    opponent_heroes = [Galahad, Deepseer]
    
    # Display heroes from both sides__________________________________________
    '''
    for player_hero in player_heroes:
      print(player_hero.show_info(), '\n')
    for opponent_hero in opponent_heroes:
      print(opponent_hero.show_info(), '\n')
    input("Press any key to continue...")
    '''

    game = Game(player_heroes, opponent_heroes, mode="manual", interface=interface)
    # Register the interface as an observer
    game.register_observer(interface)
    interface.update_display(game)
    
    # Mock data
    current_round = 3
    profession_icon = "⚔"  # Replace with actual profession icon
    hero_name = "Daoyu [Warrior]"
    special_events = ["Warlock is now in hell flame status, next rain of fire will be instant"]
    skills = ["Bash", "Shield Block", "Execute"]
    selected_skill_index = 0

    running = True
    while running:

        # Incrementally process the game state
        if game.game_state == "game_initialization":
            game.game_initialization()
        elif game.game_state == "round_start":
            game.start_round()
        elif game.game_state == "hero_action":
            game.hero_action()
        elif game.game_state == "round_end":
            game.end_round()
        elif game.game_state == "game_over":
            game.game_over()
            running = False

        interface.update_display(game)
        pygame.time.Clock().tick(60)  # Limit the frame rate



        # Update game state
        #game.notify_observers()  # Notify observers (like the interface) of state changes
        #interface.update_display(game)  # Pass the current game state for rendering
        
        # Draw the full layout
        #interface.draw_game_screen()
        #interface.draw_middle_section(current_round, profession_icon, hero_name, special_events, skills, selected_skill_index)
        #interface.update_display()
        #game.play_game()


    
    interface.close()
    sys.exit()



if __name__ == "__main__":
    main()