import pygame
import sys
from heroes import *
from skills import *
from game.game import Game
from game.hero_generator import HeroGenerator
from system.system_initialization import System_initialization
from system.game_interface import GameInterface
import os
from tqdm import tqdm

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class BattleSimulator_1v1:
    def __init__(self, sys_init):
        self.sys_init = sys_init
        self.hero_generator = HeroGenerator(self.sys_init)

    def simulate_battle(self, profession_A, profession_B, num_battles=3):
        results = {
            f"{profession_A.__name__}_Wins": 0,
            f"{profession_B.__name__}_Wins": 0,
            "Draws": 0
        }

        for _ in range(num_battles):
            # Generate heroes from specific professions
            group_A_hero = self.hero_generator.generate_heroes_specific_class("Group_A", [profession_A])[0]
            group_B_hero = self.hero_generator.generate_heroes_specific_class("Group_B", [profession_B])[0]

            # Initialize and play the game
            game = Game([group_A_hero], [group_B_hero], mode="simulation")
            #game.play_game()
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


            # Determine the result of the battle
            alive_groups = game.check_groups_status()
            if "Group_A" in alive_groups and "Group_B" not in alive_groups:
                results[f"{profession_A.__name__}_Wins"] += 1
            elif "Group_B" in alive_groups and "Group_A" not in alive_groups:
                results[f"{profession_B.__name__}_Wins"] += 1
            else:
                results["Draws"] += 1

        return results

class BattleTester_1v1:
    def __init__(self, sys_init, num_battles=10):
        self.sys_init = sys_init
        self.num_battles = num_battles
        self.professions = [
            Warrior_Comprehensiveness, Warrior_Defence, Warrior_Weapon_Master,
            Mage_Comprehensiveness, Mage_Water, Mage_Frost, Mage_Arcane, Mage_Fire, 
            Paladin_Retribution, Paladin_Protection, Paladin_Holy,
            Priest_Comprehensiveness, Priest_Shelter, Priest_Shadow, Priest_Discipline, Priest_Devine,
            Rogue_Comprehensiveness, Rogue_Assassination, Rogue_Toxicology, 
            Necromancer_Comprehensiveness, 
            Warlock_Comprehensiveness, Warlock_Destruction, Warlock_Affliction,
            Death_Knight_Frost, Death_Knight_Plague, Death_Knight_Blood
        ]

        """
        self.professions = [
            Priest_Shadow, Priest_Discipline, Paladin_Comprehensiveness, Necromancer_Comprehensiveness, Mage_Comprehensiveness, Warlock_Comprehensiveness, Warlock_Affliction, Warlock_Destruction
        ]
        """
    def format_results(self, overall_results, summary_results):
        print("\n====== Profession Battle Results ======\n")
        for profession_A, opponents in overall_results.items():
            print(f"Results for {profession_A}:")
            for profession_B, result in opponents.items():
                print(f"  vs {profession_B}:")
                print(f"    {profession_A} Wins: {result[f'{profession_A}_Wins']}")
                print(f"    {profession_B} Wins: {result[f'{profession_B}_Wins']}")
                print(f"    Draws: {result['Draws']}")
            print("\n--------------------------------------\n")

        print("\n====== Overall Summary (Sorted by Wins) ======\n")
        # Sort by Total_Wins descending
        sorted_summary = sorted(summary_results.items(), key=lambda x: x[1]['Total_Wins'], reverse=True)

        for i, (profession, summary) in enumerate(sorted_summary, start=1):
            # 🥇🥈🥉 medals for top 3
            if i == 1:
                rank_marker = f"{YELLOW}🥇{RESET}"
            elif i == 2:
                rank_marker = f"{CYAN}🥈{RESET}"
            elif i == 3:
                rank_marker = f"{MAGENTA}🥉{RESET}"
            else:
                rank_marker = ""

            print(f"{rank_marker} {profession}:")
            print(f"  {GREEN}Total Wins:   {summary['Total_Wins']}{RESET}")
            print(f"  {RED}Total Losses: {summary['Total_Losses']}{RESET}")
            print(f"  {BLUE}Total Draws:  {summary['Total_Draws']}{RESET}")
            print("\n--------------------------------------\n")

    def run_profession_tests(self):
        simulator = BattleSimulator_1v1(self.sys_init)
        overall_results = {}
        summary_results = {}

        # Initialize summary counters
        for profession in self.professions:
            summary_results[profession.__name__] = {
                "Total_Wins": 0,
                "Total_Losses": 0,
                "Total_Draws": 0
            }

        # Test each profession against all others
        #for profession_A in self.professions:
        for profession_A in tqdm(self.professions, desc="Testing Professions"):
            overall_results[profession_A.__name__] = {}
            for profession_B in self.professions:
                if profession_A != profession_B:
                    results = simulator.simulate_battle(profession_A, profession_B, self.num_battles)
                    overall_results[profession_A.__name__][profession_B.__name__] = results

                    # Update summary for profession_A
                    summary_results[profession_A.__name__]["Total_Wins"] += results[f'{profession_A.__name__}_Wins']
                    summary_results[profession_A.__name__]["Total_Losses"] += results[f'{profession_B.__name__}_Wins']
                    summary_results[profession_A.__name__]["Total_Draws"] += results['Draws']

                    # Update summary for profession_B (losses and wins are swapped)
                    summary_results[profession_B.__name__]["Total_Wins"] += results[f'{profession_B.__name__}_Wins']
                    summary_results[profession_B.__name__]["Total_Losses"] += results[f'{profession_A.__name__}_Wins']
                    summary_results[profession_B.__name__]["Total_Draws"] += results['Draws']

        # Format and display the results in a friendly format
        self.format_results(overall_results, summary_results)

        #return overall_results, summary_results
        return None

class BattleSimulator_2v2:
    def __init__(self, sys_init, allow_duplicates=False):
        self.sys_init = sys_init
        self.hero_generator = HeroGenerator(self.sys_init)
        self.allow_duplicates = allow_duplicates

    def simulate_battle(self, professions_A, professions_B, num_battles=3):
        """
        Simulate 2v2 battles.
        :param professions_A: tuple/list of 2 professions for Group A
        :param professions_B: tuple/list of 2 professions for Group B
        :param num_battles: number of battle iterations
        """
        results = {
            f"{'_'.join([p.__name__ for p in professions_A])}_Wins": 0,
            f"{'_'.join([p.__name__ for p in professions_B])}_Wins": 0,
            "Draws": 0
        }

        for _ in range(num_battles):
            # --- Generate heroes for each group ---
            if not self.allow_duplicates:
                if len(set(professions_A)) < len(professions_A) or len(set(professions_B)) < len(professions_B):
                    # Invalid combo, skip this battle
                    continue

            group_A_heroes = self.hero_generator.generate_heroes_specific_class("Group_A", list(professions_A))
            group_B_heroes = self.hero_generator.generate_heroes_specific_class("Group_B", list(professions_B))

            # --- Run the game ---
            game = Game(group_A_heroes, group_B_heroes, mode="simulation")
            running = True
            while running:
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

            # --- Determine the result ---
            alive_groups = game.check_groups_status()
            if "Group_A" in alive_groups and "Group_B" not in alive_groups:
                results[f"{'_'.join([p.__name__ for p in professions_A])}_Wins"] += 1
            elif "Group_B" in alive_groups and "Group_A" not in alive_groups:
                results[f"{'_'.join([p.__name__ for p in professions_B])}_Wins"] += 1
            else:
                results["Draws"] += 1

        return results

import itertools

class BattleTester_2v2:
    def __init__(self, sys_init, num_battles=10, allow_duplicates=False):
        self.sys_init = sys_init
        self.num_battles = num_battles
        self.allow_duplicates = allow_duplicates
        self.professions = [
            Warrior_Comprehensiveness, Warrior_Defence, Warrior_Weapon_Master,
            Mage_Comprehensiveness, Mage_Water, Mage_Frost, Mage_Arcane, Mage_Fire, 
            Paladin_Retribution, Paladin_Protection, Paladin_Holy,
            Priest_Comprehensiveness, Priest_Shelter, Priest_Shadow, Priest_Discipline, Priest_Devine,
            Rogue_Comprehensiveness, Rogue_Assassination, Rogue_Toxicology, 
            Necromancer_Comprehensiveness, 
            Warlock_Comprehensiveness, Warlock_Destruction, Warlock_Affliction,
            Death_Knight_Frost, Death_Knight_Plague, Death_Knight_Blood
        ]

    def format_results(self, overall_results, summary_results):
        print("\n====== 2v2 Overall Summary (Sorted by Wins) ======\n")
        sorted_summary = sorted(summary_results.items(), key=lambda x: x[1]["Total_Wins"], reverse=True)

        for profession_combo, summary in sorted_summary:
            print(f"{profession_combo}:")
            print(f"  Total Wins:   {summary['Total_Wins']}")
            print(f"  Total Losses: {summary['Total_Losses']}")
            print(f"  Total Draws:  {summary['Total_Draws']}")
            print("\n--------------------------------------\n")

    def run_profession_tests(self):
        simulator = BattleSimulator_2v2(self.sys_init, allow_duplicates=self.allow_duplicates)
        overall_results = {}
        summary_results = {}

        # --- Generate team combinations ---
        if self.allow_duplicates:
            team_combos = itertools.combinations_with_replacement(self.professions, 2)
        else:
            team_combos = itertools.combinations(self.professions, 2)

        team_combos = list(team_combos)

        # --- Initialize summary counters ---
        for combo in team_combos:
            name = "_".join([p.__name__ for p in combo])
            summary_results[name] = {"Total_Wins": 0, "Total_Losses": 0, "Total_Draws": 0}

        # --- Test each team against every other ---
        for team_A in team_combos:
            overall_results["_".join([p.__name__ for p in team_A])] = {}
            for team_B in team_combos:
                if team_A != team_B:
                    results = simulator.simulate_battle(team_A, team_B, self.num_battles)
                    overall_results["_".join([p.__name__ for p in team_A])]["_".join([p.__name__ for p in team_B])] = results

                    # Update summary for team A
                    name_A = "_".join([p.__name__ for p in team_A])
                    name_B = "_".join([p.__name__ for p in team_B])
                    summary_results[name_A]["Total_Wins"] += results[f"{name_A}_Wins"]
                    summary_results[name_A]["Total_Losses"] += results[f"{name_B}_Wins"]
                    summary_results[name_A]["Total_Draws"] += results["Draws"]

                    # Update summary for team B
                    summary_results[name_B]["Total_Wins"] += results[f"{name_B}_Wins"]
                    summary_results[name_B]["Total_Losses"] += results[f"{name_A}_Wins"]
                    summary_results[name_B]["Total_Draws"] += results["Draws"]

        # --- Print formatted results ---
        self.format_results(overall_results, summary_results)
        return None



def main():
    sys_init = System_initialization()
    interface = GameInterface(width=1200, height=800)
    sys_init.initialize()
    interface.initialize_window(sys_init)

    mode = sys.argv[1] if len(sys.argv) > 1 else "1v1"

    if mode == "1v1":
        battle_tester = BattleTester_1v1(sys_init, num_battles=100)
        battle_tester.run_profession_tests()
    elif mode == "2v2":
        battle_tester = BattleTester_2v2(sys_init, num_battles=30, allow_duplicates=False)
        battle_tester.run_profession_tests()
    else:
        print("Invalid mode. Use '1v1' or '2v2'.")




if __name__ == "__main__":
    main()