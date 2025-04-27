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

        image_path_Death_Knight = os.path.join("images", "icons_profession", "icon_death_knight_3.jpg")
        image_Death_Knight = pygame.image.load(image_path_Death_Knight).convert_alpha()
        self.image_Death_Knight = pygame.transform.scale(image_Death_Knight, (150, 150))  # Resize here
        image_path_Paladin = os.path.join("images", "icons_profession", "icon_paladin.webp")
        image_Paladin = pygame.image.load(image_path_Paladin).convert_alpha()
        self.image_Paladin = pygame.transform.scale(image_Paladin, (150, 150))  # Resize here
        image_path_Warrior = os.path.join("images", "icons_profession", "icon_warrior.webp")
        image_Warrior = pygame.image.load(image_path_Warrior).convert_alpha()
        self.image_Warrior = pygame.transform.scale(image_Warrior, (150, 150))  # Resize here
        image_path_Mage = os.path.join("images", "icons_profession", "icon_mage_1.png")
        image_Mage = pygame.image.load(image_path_Mage).convert_alpha()
        self.image_Mage = pygame.transform.scale(image_Mage, (150, 150))  # Resize here