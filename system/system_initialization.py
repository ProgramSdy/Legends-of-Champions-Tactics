import pandas as pd

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