import pandas as pd
import pygame
import sys
import re
import os

class System_initialization:

    def __init__(self):
        self.df_hero_basic_property = None
        self.df_hero_resistance = None
        # Define paths to your local .xlsx files
        self.file_path_hero_basic_property = 'data/Hero_basic_property.xlsx'
        self.file_path_hero_resistance = 'data/Hero_resistance.xlsx'

    def initialize(self):
        # Read Excel files from the local system
        self.df_hero_basic_property = pd.read_excel(self.file_path_hero_basic_property, sheet_name='Property List')
        self.df_hero_resistance = pd.read_excel(self.file_path_hero_resistance, sheet_name='Resistance List')
        
        # Set the index to the first column (typically hero name)
        self.df_hero_basic_property.set_index(self.df_hero_basic_property.columns[0], inplace=True)
        self.df_hero_resistance.set_index(self.df_hero_resistance.columns[0], inplace=True)

        # Loading images for each hero profession
        # Death Knight:
        image_path_Death_Knight_Frost = os.path.join("images", "icons_profession", "icon_death_knight_frost.png")
        image_Death_Knight_Frost = pygame.image.load(image_path_Death_Knight_Frost).convert_alpha()
        self.image_Death_Knight_Frost = pygame.transform.scale(image_Death_Knight_Frost, (150, 150))  # Resize here
        image_path_Death_Knight_Plague = os.path.join("images", "icons_profession", "icon_death_knight_plague.png")
        image_Death_Knight_Plague = pygame.image.load(image_path_Death_Knight_Plague).convert_alpha()
        self.image_Death_Knight_Plague = pygame.transform.scale(image_Death_Knight_Plague, (150, 150))  # Resize here
        image_path_Death_Knight_Blood = os.path.join("images", "icons_profession", "icon_death_knight_blood.png")
        image_Death_Knight_Blood = pygame.image.load(image_path_Death_Knight_Blood).convert_alpha()
        self.image_Death_Knight_Blood = pygame.transform.scale(image_Death_Knight_Blood, (150, 150))  # Resize here
        # Paladin:
        image_path_Paladin_Retribution = os.path.join("images", "icons_profession", "icon_paladin.webp")
        image_Paladin_Retribution = pygame.image.load(image_path_Paladin_Retribution).convert_alpha()
        self.image_Paladin_Retribution = pygame.transform.scale(image_Paladin_Retribution, (150, 150))  # Resize here
        image_path_Paladin_Protection = os.path.join("images", "icons_profession", "icon_paladin.webp")
        image_Paladin_Protection = pygame.image.load(image_path_Paladin_Protection).convert_alpha()
        self.image_Paladin_Protection = pygame.transform.scale(image_Paladin_Protection, (150, 150))  # Resize here
        image_path_Paladin_Holy = os.path.join("images", "icons_profession", "icon_paladin.webp")
        image_Paladin_Holy = pygame.image.load(image_path_Paladin_Holy).convert_alpha()
        self.image_Paladin_Holy = pygame.transform.scale(image_Paladin_Holy, (150, 150))  # Resize here
        # Warrior:
        image_path_Warrior_Comprehensiveness = os.path.join("images", "icons_profession", "icon_warrior.webp")
        image_Warrior_Comprehensiveness = pygame.image.load(image_path_Warrior_Comprehensiveness).convert_alpha()
        self.image_Warrior_Comprehensiveness = pygame.transform.scale(image_Warrior_Comprehensiveness, (150, 150))  # Resize here
        # Rogue:
        image_path_Rogue_Comprehensiveness = os.path.join("images", "icons_profession", "icon_rogue_comprehensiveness.png")
        image_Rogue_Comprehensiveness = pygame.image.load(image_path_Rogue_Comprehensiveness).convert_alpha()
        self.image_Rogue_Comprehensiveness = pygame.transform.scale(image_Rogue_Comprehensiveness, (150, 150))  # Resize here
        image_path_Rogue_Assassination = os.path.join("images", "icons_profession", "icon_rogue_assassination.png")
        image_Rogue_Assassination = pygame.image.load(image_path_Rogue_Assassination).convert_alpha()
        self.image_Rogue_Assassination = pygame.transform.scale(image_Rogue_Assassination, (150, 150))  # Resize here
        # Mage:
        image_path_Mage_Comprehensiveness = os.path.join("images", "icons_profession", "icon_mage_2.png")
        image_Mage_Comprehensiveness = pygame.image.load(image_path_Mage_Comprehensiveness).convert_alpha()
        self.image_Mage_Comprehensiveness = pygame.transform.scale(image_Mage_Comprehensiveness, (150, 150))  # Resize here
        # Priest:
        image_path_Priest_Comprehensiveness = os.path.join("images", "icons_profession", "icon_priest_comprehensiveness.png")
        image_Priest_Comprehensiveness = pygame.image.load(image_path_Priest_Comprehensiveness).convert_alpha()
        self.image_Priest_Comprehensiveness = pygame.transform.scale(image_Priest_Comprehensiveness, (150, 150))  # Resize here
        image_path_Priest_Discipline = os.path.join("images", "icons_profession", "icon_priest_discipline.png")
        image_Priest_Discipline = pygame.image.load(image_path_Priest_Discipline).convert_alpha()
        self.image_Priest_Discipline = pygame.transform.scale(image_Priest_Discipline, (150, 150))  # Resize here
        image_path_Priest_Shelter = os.path.join("images", "icons_profession", "icon_priest_shelter.png")
        image_Priest_Shelter = pygame.image.load(image_path_Priest_Shelter).convert_alpha()
        self.image_Priest_Shelter = pygame.transform.scale(image_Priest_Shelter, (150, 150))  # Resize here
        image_path_Priest_Shadow = os.path.join("images", "icons_profession", "icon_priest_shadow.png")
        image_Priest_Shadow = pygame.image.load(image_path_Priest_Shadow).convert_alpha()
        self.image_Priest_Shadow = pygame.transform.scale(image_Priest_Shadow, (150, 150))  # Resize here
        image_path_Priest_Devine = os.path.join("images", "icons_profession", "icon_priest_devine.png")
        image_Priest_Devine = pygame.image.load(image_path_Priest_Devine).convert_alpha()
        self.image_Priest_Devine = pygame.transform.scale(image_Priest_Devine, (150, 150))  # Resize here