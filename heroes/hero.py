import math
import random
from heroes import *
from skills import *

ORANGE = "\033[38;5;208m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Hero:
    # Class variables for ranges and skills - no specific values here
    # Magic resistance will be broken into: fire, frost, arcane, shadow, death, poison, nature,
    damage_interval = (0, 0)
    defense_interval = (0, 0)
    magic_resistance_compensation_interval = (0, 0)
    agility_interval = (0, 0)
    hp_interval = (0, 0)
    hero_basic_property_list = ['hp_interval', 'damage_interval', 'defense_interval', 'magic_resistance_compensation_interval', 'agility_interval']
    hero_resistance_list = ['fire', 'frost', 'arcane', 'shadow', 'death', 'poison', 'nature']
    status = {
        'normal':True,
        'burned':False,
        'poison':False,
        'frozen':False,

        'armor_breaker': False,
        'bleeding_slash': False,
        'magic_casting': False,
        'stunned':False,
        'cold': False,
        'shield_of_righteous': False,
        'shadow_word_pain':False,
        'poisoned_dagger':False,
        'bleeding_sharp_blade':False,
        'shadow_evasion':False,
        'holy_word_shell':False,
        'holy_word_redemption':False,
        'holy_word_punishment': False,
        'shadow_word_insanity': False,
        'holy_fire': False,
        'unholy_frenzy': False,
        'curse_of_agony': False,
        'fear': False,
        'shadow_bolt': False,
        'corrosion': False,
        'soul_siphon': False,
        'immolate': False,
        'void_connection': False,
        'holy_infusion': False,
        'hell_flame': False,
        'frost_fever': False,
        'icy_squall': False,
        'necrotic_decay': False,
        'virulent_infection': False,
        'blood_plague': False,
        'bleeding_crimson_cleave': False,
        'cumbrous_axe': False,
        'scoff': False
    }
    list_status_debuff_magic = ['shadow_word_pain', 'poisoned_dagger', 'cold', 'holy_word_punishment', \
                                'shadow_word_insanity', 'unholy_frenzy', 'curse_of_agony', 'fear', 'shadow_bolt', \
                                'corrosion','soul_siphon', 'immolate', 'icy_squall']
    list_status_debuff_disease = ['frost_fever', 'necrotic_decay', 'virulent_infection', 'blood_plague']
    list_status_debuff_physical  = ['armor_breaker', 'bleeding_slash','bleeding_sharp_blade']
    list_status_debuff_bleeding = ['bleeding_slash','bleeding_sharp_blade', 'bleeding_crimson_cleave']
    list_status_buff_magic = ['shield_of_righteous','holy_word_shell','holy_word_redemption', 'holy_fire', 'unholy_frenzy', 'holy_infusion', 'hell_flame', 'cumbrous_axe']
    list_status_buff_physical = []


    def __init__(self, sys_init, name, group, is_player_controlled, major, faculty):
        self.sys_init = sys_init
        self.name = name
        self.faculty = faculty
        self.major = major
        self.profession = self.faculty + "_" + self.major
        self.is_player_controlled = is_player_controlled
        self.game = None
        self.interface = None
        self.is_summoned = False
        self.summoned_unit = None
        self.actioned = False
        self.hero_basic_property_loader()
        self.hero_basic_property_generator()
        self.hero_resistance_loader()
        self.hero_resistance_generator()
        self.hero_resistance_compensation()

        self.original_damage = self.damage # store the original damage
        self.damage_type = ""
        self.original_defense = self.defense # store the original defense
        self.original_magic_resistance_compensation = self.magic_resistance_compensation # store the original magic resistance compensation
        self.original_agility = self.agility # store the original agility

        self.original_fire_resistance = self.fire_resistance # store the original fire resistance
        self.original_frost_resistance = self.frost_resistance # store the original frost resistance
        self.original_arcane_resistance = self.arcane_resistance # store the original arcane resistance
        self.original_shadow_resistance = self.shadow_resistance # store the original shadow resistance
        self.original_death_resistance = self.death_resistance # store the original death resistance
        self.original_poison_resistance = self.poison_resistance # store the original poison resistance
        self.original_nature_resistance = self.nature_resistance # store the original nature resistance

        self.hp = self.hp_max
        self.evasion_capability = 0
        self.skills = []
        self.group = group
        self.allies = []
        self.allies_self_excluded = []
        self.opponents = []
        self.buffs = []
        self.debuffs = []
        self.buffs_debuffs_recycle_pool = []
        self.casting_magic = None
        self.casting_magic_target = None
        self.healing_reduction_effects = {}
        self.healing_boost_effects = {}

        # Status buff and debuff
        self.status = self.status.copy() # Copy the status dictionary for individual management
        self.stun_duration = 0 # Initialize stun duration
        self.poison_duration = 0
        self.burn_duration = 0
        self.cold_duration = 0
        self.frozen_duration = 0
        self.magic_casting_duration = 0

        #duration buff and debuff
        self.damage_buff_duration = 0
        self.damage_debuff_duration = 0
        self.defense_buff_duration = 0
        self.defense_debuff_duration = 0
        self.magic_resistance_buff_duration = 0
        self.magic_resistance_debuff_duration = 0
        self.agility_buff_duration = 0
        self.agility_debuff_duration = 0

        self.armor_breaker_duration = 0
        self.shield_of_righteous_duration = 0
        self.bleeding_slash_duration = 0
        self.shadow_word_pain_debuff_duration = 0
        self.poisoned_dagger_debuff_duration = 0
        self.sharp_blade_debuff_duration = 0
        self.shadow_evasion_buff_duration = 0
        self.holy_word_shell_duration = 0
        self.holy_word_redemption_duration = 0
        self.shadow_word_insanity_duration = 0
        self.holy_fire_duration = 0
        self.curse_of_agony_duration = 0
        self.fear_duration = 0
        self.shadow_bolt_duration = 0
        self.corrosion_duration = 0
        self.soul_siphon_duration = 0
        self.holy_infusion_cooldown = 0
        self.hell_flame_cooldown = 0
        self.bleeding_crimson_cleave_duration = 0

        self.armor_breaker_stacks = 0 # Track number of Armor Breaker applications
        self.bleeding_slash_continuous_damage = 0 # Track the continuous damage of Bleeding Slash
        self.defense_reduced_amount_by_armor_breaker = 0 # Track the amount of armor breaker
        self.shield_of_righteous_stacks = 0 # Track number of Shield of Righteous applications
        self.defense_increased_amount_by_shield_of_righteous = 0 # Track the amount of Shield of Righteous
        self.agility_reduced_amount_by_frost_bolt = 0 # Track the amount of Frost Bolt
        self.shadow_word_pain_continuous_damage = 0 # Track the continuous damage of Shadow Word Pain
        self.poisoned_dagger_continuous_damage = 0 # Track the continuous damage of Poisoned Dagger
        self.poisoned_dagger_stacks = 0 # Track number of Poisoned Dagger applications
        self.sharp_blade_continuous_damage = 0 # Track the continuous damage of Sharp Blade
        self.holy_word_shell_absorption = 0 # Track the absorption of Holy Word Shell
        self.holy_fire_continuous_healing = 0 # Track the continuous healing of Holy Fire
        self.unholy_frenzy_continuous_damage = 0 # Track the continuous damage of Unholy Frenzy
        self.damage_increased_amount_by_unholy_frenzy = 0 # Track the amount of damage increased by unholy frenzy
        self.agility_increased_amount_by_unholy_frenzy = 0 # Track the amount of agility increased by unholy frenzy
        self.curse_of_agony_continuous_damage = [] # Track the continuous damage of Curse of Agony
        self.shadow_resistance_reduced_amount_by_shadow_bolt = 0 # Track the amount of magic resistance reduced by Shadow Bolt
        self.defense_reduced_amount_by_corrosion = 0 # Track the amount of defense reduced by Corrosion
        self.corrosion_continuous_damage = 0 # Track the continuous damage of Corrosion
        self.soul_siphon_continuous_damage = 0 # Track the continuous damage of Soul Siphon
        self.soul_siphon_healing_amount = 0 # Track the healing amount of Soul Siphon
        self.damage_reduced_amount_by_immolate = 0 # Track the amount of damage reduced by Immolate
        self.immolate_continuous_damage = 0 # Track the continuous damage of Immolate
        self.frost_fever_continuous_damage = 0 # Track the continuous damage of Frost Fever
        self.agility_reduced_amount_by_frost_fever = 0 # Track the amount of agility reduced by frost fever
        self.frost_resistance_reduced_amount_by_icy_squall = 0 #Track the amount of frost resistance reduced by icy squall
        self.healing_reduction_by_necrotic_decay = 0 #Track the amount of healing reduction by necrotic decay
        self.necrotic_decay_continuous_damage = 0
        self.virulent_infection_continuous_damage = 0
        self.blood_plague_continuous_damage = 0
        self.blood_plague_blood_drain = 0
        self.bleeding_crimson_cleave_continuous_damage = 0


    @classmethod
    def random_in_range(cls, value_range):
        return random.randint(value_range[0], value_range[1])

    @classmethod
    def definite_shuffle(cls, lst):
      if len(lst) <= 1:
          return lst  # No need to shuffle if the list has 0 or 1 element
      original_lst = lst[:]
      while True:
          random.shuffle(lst)
          if lst != original_lst:
              break

    def hero_basic_property_loader(self):
        self.hp_interval = (int(self.sys_init.df_hero_basic_property.loc['Hp_Min'][self.profession]), int(self.sys_init.df_hero_basic_property.loc['Hp_Max'][self.profession]))
        self.damage_interval = (int(self.sys_init.df_hero_basic_property.loc['Damage_Min'][self.profession]), int(self.sys_init.df_hero_basic_property.loc['Damage_Max'][self.profession]))
        self.defense_interval = (int(self.sys_init.df_hero_basic_property.loc['Defense_Min'][self.profession]), int(self.sys_init.df_hero_basic_property.loc['Defense_Max'][self.profession]))
        self.agility_interval = (int(self.sys_init.df_hero_basic_property.loc['Agility_Min'][self.profession]), int(self.sys_init.df_hero_basic_property.loc['Agility_Max'][self.profession]))
        self.magic_resistance_compensation_interval = (int(self.sys_init.df_hero_basic_property.loc['Magic_Resistance_Compensation_Min'][self.profession]), int(self.sys_init.df_hero_basic_property.loc['Magic_Resistance_Compensation_Max'][self.profession]))
        #print(type(self.hp_interval))
        #print(self.hp_interval)

    # hero_basic_property_list = ['hp_interval', 'damage_interval', 'defense_interval', 'magic_resistance_compensation_interval', 'agility_interval']
    def hero_basic_property_generator(self):
        first_property = random.choice(Hero.hero_basic_property_list[0:2])
        #print(first_property)
        second_property = random.choice(Hero.hero_basic_property_list[2:5])
        #print(second_property)
        if first_property == 'hp_interval':
          self.hp_max = self.random_in_range(self.hp_interval)
          hp_max_avg = round((self.hp_interval[0] + self.hp_interval[1]) / 2)
          damage_avg = round((self.damage_interval[0] + self.damage_interval[1]) / 2)
          deviation = self.hp_max - hp_max_avg
          deviation_abs = abs(deviation)
          if deviation >= 0:
            self.damage = damage_avg - deviation_abs
          else:
            self.damage = damage_avg + deviation_abs
        elif first_property == 'damage_interval':
          self.damage = self.random_in_range(self.damage_interval)
          hp_max_avg = round((self.hp_interval[0] + self.hp_interval[1]) / 2)
          damage_avg = round((self.damage_interval[0] + self.damage_interval[1]) / 2)
          deviation = self.damage - damage_avg
          deviation_abs = abs(deviation)
          if deviation >= 0:
            self.hp_max = hp_max_avg - deviation_abs
          else:
            self.hp_max = hp_max_avg + deviation_abs

        if second_property == 'defense_interval':
          self.defense = self.random_in_range(self.defense_interval)
          agility_avg = round((self.agility_interval[0] + self.agility_interval[1]) / 2)
          defense_avg = round((self.defense_interval[0] + self.defense_interval[1]) / 2)
          magic_resistance_compensation_avg = round((self.magic_resistance_compensation_interval[0] + self.magic_resistance_compensation_interval[1]) / 2)
          deviation = self.defense - defense_avg
          deviation_abs = abs(deviation)
          sub_deviation = self.random_in_range((0, deviation_abs))
          if deviation >= 0:
            self.agility = agility_avg - sub_deviation
            self.magic_resistance_compensation = magic_resistance_compensation_avg - (deviation_abs - sub_deviation)
          else:
            self.agility = agility_avg + sub_deviation
            self.magic_resistance_compensation = magic_resistance_compensation_avg + (deviation_abs - sub_deviation)
        elif second_property == 'magic_resistance_compensation_interval':
          self.magic_resistance_compensation = self.random_in_range(self.magic_resistance_compensation_interval)
          agility_avg = round((self.agility_interval[0] + self.agility_interval[1]) / 2)
          defense_avg = round((self.defense_interval[0] + self.defense_interval[1]) / 2)
          magic_resistance_compensation_avg = round((self.magic_resistance_compensation_interval[0] + self.magic_resistance_compensation_interval[1]) / 2)
          deviation = self.magic_resistance_compensation - magic_resistance_compensation_avg
          deviation_abs = abs(deviation)
          sub_deviation = self.random_in_range((0, deviation_abs))
          if deviation >= 0:
            self.defense = defense_avg - sub_deviation
            self.agility = agility_avg - (deviation_abs - sub_deviation)
          else:
            self.defense = defense_avg + sub_deviation
            self.agility = agility_avg + (deviation_abs - sub_deviation)
        elif second_property == 'agility_interval':
          self.agility = self.random_in_range(self.agility_interval)
          agility_avg = round((self.agility_interval[0] + self.agility_interval[1]) / 2)
          defense_avg = round((self.defense_interval[0] + self.defense_interval[1]) / 2)
          magic_resistance_compensation_avg = round((self.magic_resistance_compensation_interval[0] + self.magic_resistance_compensation_interval[1]) / 2)
          deviation = self.agility - agility_avg
          deviation_abs = abs(deviation)
          sub_deviation = self.random_in_range((0, deviation_abs))
          if deviation >= 0:
            self.magic_resistance_compensation = magic_resistance_compensation_avg - sub_deviation
            self.defense = defense_avg - (deviation_abs - sub_deviation)
          else:
            self.magic_resistance_compensation = magic_resistance_compensation_avg + sub_deviation
            self.defense = defense_avg + (deviation_abs - sub_deviation)

    def hero_resistance_loader(self):
        self.fire_resistance_interval = (int(self.sys_init.df_hero_resistance.loc['Fire_resistance_Min'][self.profession]), int(self.sys_init.df_hero_resistance.loc['Fire_resistance_Max'][self.profession]))
        self.frost_resistance_interval = (int(self.sys_init.df_hero_resistance.loc['Frost_resistance_Min'][self.profession]), int(self.sys_init.df_hero_resistance.loc['Frost_resistance_Max'][self.profession]))
        self.arcane_resistance_interval = (int(self.sys_init.df_hero_resistance.loc['Arcane_resistance_Min'][self.profession]), int(self.sys_init.df_hero_resistance.loc['Arcane_resistance_Max'][self.profession]))
        self.shadow_resistance_interval = (int(self.sys_init.df_hero_resistance.loc['Shadow_resistance_Min'][self.profession]), int(self.sys_init.df_hero_resistance.loc['Shadow_resistance_Max'][self.profession]))
        self.death_resistance_interval = (int(self.sys_init.df_hero_resistance.loc['Death_resistance_Min'][self.profession]), int(self.sys_init.df_hero_resistance.loc['Death_resistance_Max'][self.profession]))
        self.poison_resistance_interval = (int(self.sys_init.df_hero_resistance.loc['Poison_resistance_Min'][self.profession]), int(self.sys_init.df_hero_resistance.loc['Poison_resistance_Max'][self.profession]))
        self.nature_resistance_interval = (int(self.sys_init.df_hero_resistance.loc['Nature_resistance_Min'][self.profession]), int(self.sys_init.df_hero_resistance.loc['Nature_resistance_Max'][self.profession]))

    #hero_resistance_list = ['fire', 'frost', 'arcane', 'shadow', 'death', 'poison', 'nature']
    def hero_resistance_generator(self):
        first_resistance = random.choice(Hero.hero_resistance_list[0:3])
        #print(first_resistance)
        second_resistance = random.choice(Hero.hero_resistance_list[3:5])
        #print(second_resistance)
        third_resistance = random.choice(Hero.hero_resistance_list[5:7])
        #print(third_resistance)
        fire_resistance_avg = round((self.fire_resistance_interval[0] + self.fire_resistance_interval[1]) / 2)
        frost_resistance_avg = round((self.frost_resistance_interval[0] + self.frost_resistance_interval[1]) / 2)
        arcane_resistance_avg = round((self.arcane_resistance_interval[0] + self.arcane_resistance_interval[1]) / 2)
        shadow_resistance_avg = round((self.shadow_resistance_interval[0] + self.shadow_resistance_interval[1]) / 2)
        death_resistance_avg = round((self.death_resistance_interval[0] + self.death_resistance_interval[1]) / 2)
        poison_resistance_avg = round((self.poison_resistance_interval[0] + self.poison_resistance_interval[1]) / 2)
        nature_resistance_avg = round((self.nature_resistance_interval[0] + self.nature_resistance_interval[1]) / 2)

        if first_resistance == 'fire':
          self.fire_resistance = self.random_in_range(self.fire_resistance_interval)
          deviation = self.fire_resistance - fire_resistance_avg
          deviation_abs = abs(deviation)
          sub_deviation = self.random_in_range((0, deviation_abs))
          if deviation >= 0:
            self.frost_resistance = frost_resistance_avg - sub_deviation
            self.arcane_resistance = arcane_resistance_avg - (deviation_abs - sub_deviation)
          else:
            self.frost_resistance = frost_resistance_avg + sub_deviation
            self.arcane_resistance = arcane_resistance_avg + (deviation_abs - sub_deviation)
        elif first_resistance == 'frost':
          self.frost_resistance = self.random_in_range(self.frost_resistance_interval)
          deviation = self.frost_resistance - frost_resistance_avg
          deviation_abs = abs(deviation)
          sub_deviation = self.random_in_range((0, deviation_abs))
          if deviation >= 0:
            self.fire_resistance = fire_resistance_avg - sub_deviation
            self.arcane_resistance = arcane_resistance_avg - (deviation_abs - sub_deviation)
          else:
            self.fire_resistance = fire_resistance_avg + sub_deviation
            self.arcane_resistance = arcane_resistance_avg + (deviation_abs - sub_deviation)
        elif first_resistance == 'arcane':
          self.arcane_resistance = self.random_in_range(self.arcane_resistance_interval)
          deviation = self.arcane_resistance - arcane_resistance_avg
          deviation_abs = abs(deviation)
          sub_deviation = self.random_in_range((0, deviation_abs))
          if deviation >= 0:
            self.fire_resistance = fire_resistance_avg - sub_deviation
            self.frost_resistance = frost_resistance_avg - (deviation_abs - sub_deviation)
          else:
            self.fire_resistance = fire_resistance_avg + sub_deviation
            self.frost_resistance = frost_resistance_avg + (deviation_abs - sub_deviation)

        if second_resistance == 'shadow':
          self.shadow_resistance = self.random_in_range(self.shadow_resistance_interval)
          deviation = self.shadow_resistance - shadow_resistance_avg
          deviation_abs = abs(deviation)
          if deviation >= 0:
            self.death_resistance = death_resistance_avg - deviation_abs
          else:
            self.death_resistance = death_resistance_avg + deviation_abs
        elif second_resistance == 'death':
          self.death_resistance = self.random_in_range(self.death_resistance_interval)
          deviation = self.death_resistance - death_resistance_avg
          deviation_abs = abs(deviation)
          if deviation >= 0:
            self.shadow_resistance = shadow_resistance_avg - deviation_abs
          else:
            self.shadow_resistance = shadow_resistance_avg + deviation_abs

        if third_resistance == 'poison':
          self.poison_resistance = self.random_in_range(self.poison_resistance_interval)
          deviation = self.poison_resistance - poison_resistance_avg
          deviation_abs = abs(deviation)
          if deviation >= 0:
            self.nature_resistance = nature_resistance_avg - deviation_abs
          else:
            self.nature_resistance = nature_resistance_avg + deviation_abs
        elif third_resistance == 'nature':
          self.nature_resistance = self.random_in_range(self.nature_resistance_interval)
          deviation = self.nature_resistance - nature_resistance_avg
          deviation_abs = abs(deviation)
          if deviation >= 0:
            self.poison_resistance = poison_resistance_avg - deviation_abs
          else:
            self.poison_resistance = poison_resistance_avg + deviation_abs


    def hero_resistance_compensation(self):
        hero_resistance_list_random = Hero.hero_resistance_list.copy()
        random.shuffle(hero_resistance_list_random)
        #print(f"hero_resistance_list_random = {hero_resistance_list_random}")
        '''
        resistance_values = {
            'fire': self.fire_resistance,
            'frost': self.frost_resistance,
            'arcane': self.arcane_resistance,
            'shadow': self.shadow_resistance,
            'death': self.death_resistance,
            'poison': self.poison_resistance,
            'nature': self.nature_resistance
        }
        '''
        if self.magic_resistance_compensation > 0:
          for i in range(self.magic_resistance_compensation):
            resistance_type = hero_resistance_list_random[i]
            #resistance_values[hero_resistance_list_random[i]] += 1
            #print(f"{resistance_type}_resistance = {getattr(self, f'{resistance_type}_resistance')}")
            setattr(self, f"{resistance_type}_resistance", getattr(self, f"{resistance_type}_resistance") + 1)
            #print(f"{resistance_type}_resistance plus one")
            #print(f"{resistance_type}_resistance = {getattr(self, f'{resistance_type}_resistance')}")
        elif self.magic_resistance_compensation < 0:
          for i in range(abs(self.magic_resistance_compensation)):
            resistance_type = hero_resistance_list_random[i]
            #resistance_values[hero_resistance_list_random[i]] += 1
            #print(f"{resistance_type}_resistance = {getattr(self, f'{resistance_type}_resistance')}")
            setattr(self, f"{resistance_type}_resistance", getattr(self, f"{resistance_type}_resistance") - 1)
            #print(f"{resistance_type}_resistance minus one")
            #print(f"{resistance_type}_resistance = {getattr(self, f'{resistance_type}_resistance')}")
        else:
          pass


    def take_game_instance(self, game):
        self.game = game

    def take_interface(self, interface):
        self.interface = interface

    def show_info(self):
        skill_names = [skill.name for skill in self.skills]
        return (f"Hero: {self.name}\n"
                f"Group: {self.group}\n"
                f"Faculty: {self.faculty}\n"
                f"Major: {self.major}\n"
                f"Profession: {self.profession}\n"
                f"HP: {self.hp}/{self.hp_max}\n"
                f"Damage: {self.damage}\n"
                f"Defense: {self.defense}\n"
                f"Magic Resistance Compensation: {self.magic_resistance_compensation}\n"
                f"Agility: {self.agility}\n"
                f"Fire Resistance: {self.fire_resistance}\n"
                f"Frost Resistance: {self.frost_resistance}\n"
                f"Arcane Resistance: {self.arcane_resistance}\n"
                f"Shadow Resistance: {self.shadow_resistance}\n"
                f"Death Resistance: {self.death_resistance}\n"
                f"Poison Resistance: {self.poison_resistance}\n"
                f"Nature Resistance: {self.nature_resistance}\n"
                f"Skills: {', '.join(skill_names)}")

    def check_if_defeated(self):
        results = []
        if self.hp <= 0:
          results.append(f"{RED}{self.name} has been defeated!{RESET}")
          if self.is_summoned == True:
            self.master.summoned_unit = None
          if self.summoned_unit != None and self.summoned_unit.hp > 0:
            self.summoned_unit.hp = 0
            '''
            for player_hero in self.game.player_heroes:
                if self == player_hero:
                  self.game.player_heroes.remove(self.summoned_unit)
                  self.game.heroes.remove(self.summoned_unit)
                  break
                else:
                  self.game.opponent_heroes.remove(self.summoned_unit)
                  self.game.heroes.remove(self.summoned_unit)
            '''
            results.append(f"{RED}{self.summoned_unit.name} has lost their master and vanished from the battle field.{RESET}")
          if self.status['soul_siphon'] == True:
            for debuff in self.debuffs:
              if debuff.name == "Soul Siphon" and debuff.initiator.hp > 0:
                results.append(f"{BLUE}{debuff.initiator.name} has gain life through Soul Siphon. {debuff.initiator.take_healing(self.soul_siphon_healing_amount)}{RESET}")
                debuff.duration = 0
                self.soul_siphon_continuous_damage = 0
                self.soul_siphon_healing_amount = 0
                self.status['soul_siphon'] = False
                self.debuffs.remove(debuff)
                self.buffs_debuffs_recycle_pool.append(debuff)
          if self.status['necrotic_decay']:
            for debuff in self.debuffs:
              if debuff.name == "Necrotic Decay":
                 damage = debuff.initiator.damage
            possible_targets = [ally for ally in self.allies if not ally.status['necrotic_decay']]
            if possible_targets:
                spread_target = random.choice(possible_targets)
                if random.randint(1, 100) <= 100:  # 25% chance
                    spread_target.status['necrotic_decay'] = True
                    new_debuff = Debuff(
                        name='Necrotic Decay',
                        duration=4,
                        initiator=self,
                        effect=0.8
                    )
                    spread_target.add_debuff(new_debuff)
                    spread_target.healing_reduction_effects['necrotic_decay'] = 0.3 
                    basic_damage = round((damage - spread_target.death_resistance) * 1/5)
                    variation = random.randint(-1, 1)
                    actual_damage = max(1, basic_damage + variation)
                    spread_target.necrotic_decay_continuous_damage = round(actual_damage * debuff.effect)
                    results.append(f"{spread_target.name} is infected with Necrotic Decay as {self.name} falls in battle!")
          return "\n".join(results)
        else:
          results = "0"
          return results

    def take_damage(self, damage_dealt):
      #Check if void connection is activated
      if self.status['void_connection'] == True and self.summoned_unit != None and self.summoned_unit.hp > 0:
        results = []
        results.append(self.take_damage_action(damage_dealt))
        result_defeated_1 = self.check_if_defeated()
        result_defeated_2 = self.summoned_unit.check_if_defeated()
        if result_defeated_1 == "0" and result_defeated_2 == "0":
          return "".join(results)
        elif result_defeated_1 == "0" and result_defeated_2 != "0":
          results.append(result_defeated_2)
          return "\n".join(results)
        elif result_defeated_1 != "0" and result_defeated_2 == "0":
          results.append(result_defeated_1)
          return "\n".join(results)
        else:
          results.append(result_defeated_1)
          results.append(result_defeated_2)
          return "\n".join(results)
      else: # normal sitation
          results = []
          results.append(self.take_damage_action(damage_dealt))
          result_defeated_1 = self.check_if_defeated()
          if result_defeated_1 == "0":
            return "".join(results)
          else:
            results.append(result_defeated_1)
            return "\n".join(results)


    def take_damage_action(self, damage_dealt):
          damage_dealt = max(0, damage_dealt)
          accuracy = 30  # any attack has 30% chance to interrupt fear effect
          if self.status['holy_word_shell'] == True:
            if damage_dealt < self.holy_word_shell_absorption:
              self.holy_word_shell_absorption -= damage_dealt
              return f"{self.name}'s Holy Word Shell absorbs {damage_dealt} damage. {self.name} has {self.hp} HP left."
            elif damage_dealt == self.holy_word_shell_absorption:
              self.holy_word_shell_absorption -= damage_dealt
              self.status['holy_word_shell'] = False
              self.holy_word_shell_duration = 0
              return f"{self.name}'s Holy Word Shell absorbs {damage_dealt} damage, the Shell breaks. {self.name} has {self.hp} HP left."
            else:
              damage_dealt -= self.holy_word_shell_absorption
              absorbed_damage = self.holy_word_shell_absorption
              self.holy_word_shell_absorption = 0
              self.status['holy_word_shell'] = False
              self.holy_word_shell_duration = 0
              if self.status['fear'] == True:
                roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
                if roll <= accuracy:
                  self.status['fear'] = False
                  for debuff in self.debuffs:
                      if debuff.name == "Curse of Fear":
                        debuff.duration = 0
                        for skill in debuff.initiator.skills:
                          if skill.name == "Curse of Fear":
                            skill.is_available = True
                  if self.status['void_connection'] == True and self.summoned_unit != None and self.summoned_unit.hp > 0:
                    for buff in self.buffs:
                      if buff.name == "Void Connection":
                        buff.initiator.hp = buff.initiator.hp - round(damage_dealt * buff.effect)
                        self.hp = self.hp - (damage_dealt - round(damage_dealt * buff.effect))
                        if self.hp < 0:
                            self.hp = 0
                        if buff.initiator.hp <= 0:
                          buff.initiator.hp = 0
                        return f"{self.name}'s Holy Word Shell absorbs {absorbed_damage} damage, the Shell breaks. {self.name} takes {damage_dealt - round(damage_dealt * buff.effect)} damage and recovers from fear. {self.name} has {self.hp} HP left.{buff.initiator.name} takes {round(damage_dealt * buff.effect)} damage. {buff.initiator.name} has {buff.initiator.hp} HP left."
                  else:
                    self.hp = self.hp - damage_dealt
                  if self.hp < 0:
                      self.hp = 0
                  return f"{self.name}'s Holy Word Shell absorbs {absorbed_damage} damage, the Shell breaks. {self.name} takes {damage_dealt} damage and recovers from fear. {self.name} has {self.hp} HP left."
                else:
                  if self.status['void_connection'] == True and self.summoned_unit != None and self.summoned_unit.hp > 0:
                    for buff in self.buffs:
                      if buff.name == "Void Connection":
                        buff.initiator.hp = buff.initiator.hp - round(damage_dealt * buff.effect)
                        self.hp = self.hp - (damage_dealt - round(damage_dealt * buff.effect))
                        if self.hp < 0:
                            self.hp = 0
                        if buff.initiator.hp <= 0:
                          buff.initiator.hp = 0
                        return f"{self.name}'s Holy Word Shell absorbs {absorbed_damage} damage, the Shell breaks. {self.name} takes {damage_dealt - round(damage_dealt * buff.effect)} damage. {self.name} has {self.hp} HP left.{buff.initiator.name} takes {round(damage_dealt * buff.effect)} damage. {buff.initiator.name} has {buff.initiator.hp} HP left."
                  else:
                    self.hp = self.hp - damage_dealt
                    if self.hp < 0:
                        self.hp = 0
                    return f"{self.name}'s Holy Word Shell absorbs {absorbed_damage} damage, the Shell breaks. {self.name} takes {damage_dealt} damage and has {self.hp} HP left."
              else:
                if self.status['void_connection'] == True and self.summoned_unit != None and self.summoned_unit.hp > 0:
                    for buff in self.buffs:
                      if buff.name == "Void Connection":
                        buff.initiator.hp = buff.initiator.hp - round(damage_dealt * buff.effect)
                        self.hp = self.hp - (damage_dealt - round(damage_dealt * buff.effect))
                        if self.hp < 0:
                            self.hp = 0
                        if buff.initiator.hp <= 0:
                          buff.initiator.hp = 0
                        return f"{self.name}'s Holy Word Shell absorbs {absorbed_damage} damage, the Shell breaks. {self.name} takes {damage_dealt - round(damage_dealt * buff.effect)} damage. {self.name} has {self.hp} HP left.{buff.initiator.name} takes {round(damage_dealt * buff.effect)} damage. {buff.initiator.name} has {buff.initiator.hp} HP left."
                else:
                  self.hp = self.hp - damage_dealt
                  if self.hp < 0:
                    self.hp = 0
                  return f"{self.name}'s Holy Word Shell absorbs {absorbed_damage} damage, the Shell breaks. {self.name} takes {damage_dealt} damage and has {self.hp} HP left."
          else:
            if self.status['fear'] == True:
              roll = random.randint(1, 100)  # Simulate a roll of 100-sided dice
              if roll <= accuracy:
                self.status['fear'] = False
                for debuff in self.debuffs:
                      if debuff.name == "Curse of Fear":
                        debuff.duration = 0
                        for skill in debuff.initiator.skills:
                          if skill.name == "Curse of Fear":
                            skill.is_available = True
                if self.status['void_connection'] == True and self.summoned_unit != None and self.summoned_unit.hp > 0:
                  for buff in self.buffs:
                    if buff.name == "Void Connection":
                      buff.initiator.hp = buff.initiator.hp - round(damage_dealt * buff.effect)
                      self.hp = self.hp - (damage_dealt - round(damage_dealt * buff.effect))
                      if self.hp < 0:
                          self.hp = 0
                      if buff.initiator.hp <= 0:
                        buff.initiator.hp = 0
                      return f"{self.name} takes {damage_dealt - round(damage_dealt * buff.effect)} damage and recovers from fear. {self.name} has {self.hp} HP left.{buff.initiator.name} takes {round(damage_dealt * buff.effect)} damage. {buff.initiator.name} has {buff.initiator.hp} HP left."
                else:
                  self.hp = self.hp - damage_dealt
                  if self.hp < 0:
                      self.hp = 0
                  return f"{self.name} takes {damage_dealt} damage and recovers from fear. {self.name} has {self.hp} HP left."
              else:
                if self.status['void_connection'] == True and self.summoned_unit != None and self.summoned_unit.hp > 0:
                  for buff in self.buffs:
                    if buff.name == "Void Connection":
                      buff.initiator.hp = buff.initiator.hp - round(damage_dealt * buff.effect)
                      self.hp = self.hp - (damage_dealt - round(damage_dealt * buff.effect))
                      if self.hp < 0:
                          self.hp = 0
                      if buff.initiator.hp <= 0:
                        buff.initiator.hp = 0
                      return f"{self.name} takes {damage_dealt - round(damage_dealt * buff.effect)} damage. {self.name} has {self.hp} HP left.{buff.initiator.name} takes {round(damage_dealt * buff.effect)} damage. {buff.initiator.name} has {buff.initiator.hp} HP left."
                else:
                  self.hp = self.hp - damage_dealt
                  if self.hp < 0:
                      self.hp = 0
                  return f"{self.name} takes {damage_dealt} damage and has {self.hp} HP left."
            else:
              if self.status['void_connection'] == True and self.summoned_unit != None and self.summoned_unit.hp > 0:
                  for buff in self.buffs:
                    if buff.name == "Void Connection":
                      buff.initiator.hp = buff.initiator.hp - round(damage_dealt * buff.effect)
                      self.hp = self.hp - (damage_dealt - round(damage_dealt * buff.effect))
                      if self.hp < 0:
                          self.hp = 0
                      if buff.initiator.hp <= 0:
                        buff.initiator.hp = 0
                      return f"{self.name} takes {damage_dealt - round(damage_dealt * buff.effect)} damage. {self.name} has {self.hp} HP left.{buff.initiator.name} takes {round(damage_dealt * buff.effect)} damage. {buff.initiator.name} has {buff.initiator.hp} HP left."
              else:
                self.hp = self.hp - damage_dealt
                if self.hp < 0:
                    self.hp = 0
                return f"{self.name} takes {damage_dealt} damage and has {self.hp} HP left."

    def add_buff(self, buff):
        self.buffs.append(buff)
       # buff.apply_effect(self)

    def add_debuff(self, debuff):
        self.debuffs.append(debuff)

    def take_healing(self, healing_amount):
      total_boost = sum(self.healing_boost_effects.values())  # Sum all healing boosts
      total_reduction = sum(self.healing_reduction_effects.values())  # Sum all healing reductions
      total_reduction = min(total_reduction, 1)  # Cap reduction at 100% to avoid negative healing
      net_modifier = 1 + total_boost - total_reduction
      net_modifier = max(0, net_modifier)  # Ensure healing is not negative
      final_healing = round(healing_amount * net_modifier)
      self.hp = min(self.hp_max, self.hp + final_healing)
      return f"{self.name} takes {final_healing} healing and has {self.hp} HP left."

    def take_healing_coefficient(self, num_allies):
        if num_allies == 1:
            return 1
        elif num_allies == 2:
            return 0.9
        elif num_allies == 3:
            return 0.8
        else:
            return 0.7

    def magic_casting(self, skill, other_hero = None):
      self.casting_magic = skill
      self.casting_magic_target = other_hero
      return f"{self.name} need to keep casting {skill.name} for {self.magic_casting_duration} rounds."

    def interrupt_magic_casting(self, other_hero):
      other_hero.status['magic_casting'] = False
      return f"{other_hero.name}'s magic casting has been interrupted"

    def add_skill(self, skill):
        self.skills.append(skill)

    def remove_skill(self, skill_name):
      for skill in self.skills:
        if skill.name == skill_name:
          self.skills.remove(skill)


    def ai_choose_skill(self, opponents, allies):
        available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        chosen_skill = random.choice(available_skills)
        return chosen_skill

    def player_choose_skill(self, hero):
        # Command line choose skill
        '''
        self.hero = hero
        print('***************************************************************************************************************')
        print(hero.name + ", please choose your skills:")
        available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        for index, skill in enumerate(available_skills):
            print(f"{index + 1}: {skill.name}")  # Display skill names
        while True:
          try:
            skill_input = input(f"Enter the number of the skill you want to use: ")
            selected_skill = available_skills[int(skill_input) - 1]
            return selected_skill
          except (ValueError, IndexError):
            print("Invalid input, please try again")
        '''
        """
        Allow the player to choose a skill using the game interface.
        :param interface: GameInterface instance to handle the interaction.
        :return: Selected skill object.
        """
        available_skills = [skill for skill in self.skills if not skill.if_cooldown and skill.is_available]
        if not available_skills:
            print(f"{self.name} has no available skills!")
            return None

        # Let the interface handle skill selection
        selected_skill_index = self.interface.select_skill(self, available_skills)

        if selected_skill_index is not None:
            return available_skills[selected_skill_index]
        else:
            print("No skill selected.")
            return None

    def player_choose_target(self, opponents, allies, chosen_skill, num_targets = 1):
        # Command line choose target
        '''
        print("Available targets:")
        if chosen_skill.skill_type == "damage":
          if chosen_skill.name == 'Rain of Fire':
            selected_targets = random.sample(opponents, chosen_skill.target_qty) if len(opponents) > chosen_skill.target_qty else opponents
            print('***************************************************************************************************************')
            return selected_targets
          else:
            for index, opponent in enumerate(opponents):
              print(f"{index + 1}: {opponent.name} HP: {opponent.hp}/{opponent.hp_max}")
        elif chosen_skill.skill_type == "healing" or chosen_skill.skill_type == 'buffs':
          if chosen_skill.name == "Binding Heal":
            filtered_allies = [ally for ally in allies if ally is not self]
            if len(filtered_allies) == 0:
              print(f"No allies available to heal. Binding Heal is casted on {self.name} himself")
              selected_targets = [self]
              print('***************************************************************************************************************')
              return selected_targets
            else:
              for index, ally in enumerate(filtered_allies):
                print(f"{index + 1}: {ally.name} HP: {ally.hp}/{ally.hp_max}")
          elif chosen_skill.name == "Holy Word Prayer":
              selected_targets = self.allies
              print('***************************************************************************************************************')
              return selected_targets
          else:
            for index, ally in enumerate(allies):
              print(f"{index + 1}:{ally.name} HP: {ally.hp}/{ally.hp_max}")

        elif chosen_skill.skill_type == "damage_healing":
          print("opponent heroes:")
          for index, opponent in enumerate(opponents):
              print(f"{index + 1}: {opponent.name} HP: {opponent.hp}/{opponent.hp_max}")
          print("ally heroes:")
          for index, ally in enumerate(allies):
              print(f"{len(opponents) + index + 1}: {ally.name} HP: {ally.hp}/{ally.hp_max}")

        selected_targets = []

        while len(selected_targets) < min(num_targets, len(opponents)):

          try:
            if chosen_skill.skill_type == "damage":
              if chosen_skill.target_type == "single":
                  target_input = input(f"Enter the number of the target you want to attack: ")
                  target = opponents[int(target_input) - 1]
                  if target in selected_targets:
                      print("You have already selected this target. Please choose a different one.")
                  else:
                      selected_targets.append(target)
              else:
                  target_input = input(f"Enter the number of the target {len(selected_targets) + 1} you want to attack: ")
                  target = opponents[int(target_input) - 1]
                  if target in selected_targets:
                      print("You have already selected this target. Please choose a different one.")
                  else:
                      selected_targets.append(target)

            elif chosen_skill.skill_type == "healing":
              if chosen_skill.target_type == "single":
                if chosen_skill.name == "Binding Heal":
                    target_input = input(f"Enter the number of the target you want to heal: ")
                    target = filtered_allies[int(target_input) - 1]
                    if target in selected_targets:
                        print("You have already selected this target. Please choose a different one.")
                    else:
                        selected_targets.append(target)
                else:
                    target_input = input(f"Enter the number of the target  you want to heal: ")
                    target = allies[int(target_input) - 1]
                    if target in selected_targets:
                        print("You have already selected this target. Please choose a different one.")
                    else:
                        selected_targets.append(target)
              else:
                  target_input = input(f"Enter the number of the target {len(selected_targets) + 1} you want to heal: ")
                  target = opponents[int(target_input) - 1]
                  if target in selected_targets:
                      print("You have already selected this target. Please choose a different one.")
                  else:
                      selected_targets.append(target)

            elif chosen_skill.skill_type == "buffs":
                if chosen_skill.target_type == "single":
                  target_input = input(f"Enter the number of the target you want to apply buff magic: ")
                  target = allies[int(target_input) - 1]
                  if target in selected_targets:
                      print("You have already selected this target. Please choose a different one.")
                  else:
                      selected_targets.append(target)
                else:
                  target_input = input(f"Enter the number of the target {len(selected_targets) + 1} you want to apply buff magic: ")
                  target = allies[int(target_input) - 1]
                  if target in selected_targets:
                      print("You have already selected this target. Please choose a different one.")
                  else:
                      selected_targets.append(target)

            elif chosen_skill.skill_type == "damage_healing":
                target_input = input(f"Enter the number of the target you want to attack / heal: ")
                target_index = int(target_input) - 1
                if target_index < len(opponents):
                    target = opponents[target_index]
                else:
                    target = allies[target_index - len(opponents)]
                if target in selected_targets:
                    print("You have already selected this target. Please choose a different one.")
                else:
                    selected_targets.append(target)

          except (ValueError, IndexError):
              print("Invalid input, please try again")

        print('***************************************************************************************************************')
        return selected_targets
        '''
        """
        Determine valid targets based on skill logic and call the interface for player selection.
        :param opponents: List of opponent heroes.
        :param allies: List of ally heroes.
        :param chosen_skill: The selected skill to determine valid targets.
        :param num_targets: Number of targets required.
        :return: List of selected targets.
        """
        available_targets = []
        auto_selected_targets = []

        # Determine valid targets based on skill type
        if chosen_skill.skill_type == "damage":
            if chosen_skill.name == "Rain of Fire":
                # Automatic targeting for multi-target skill
                auto_selected_targets = random.sample(opponents, chosen_skill.target_qty) if len(opponents) > chosen_skill.target_qty else opponents
            else:
                available_targets.extend(opponents)
        elif chosen_skill.skill_type in ["healing", "buffs"]:
            if chosen_skill.name == "Binding Heal":
                available_targets = [ally for ally in allies if ally is not self]
                if not available_targets:
                    # Automatically apply to self if no allies are available
                    return [self]
            elif chosen_skill.name == "Holy Word Prayer":
                # Automatically applies to all allies
                return allies
            else:
                available_targets.extend(allies)
        elif chosen_skill.skill_type == "damage_healing":
            available_targets.extend(opponents + allies)

        # If there are auto-selected targets, return them immediately
        if auto_selected_targets:
            return auto_selected_targets
        
        # Call the game interface to let the player select targets
        return self.interface.select_target(self, available_targets, num_targets)
        

    def ai_choose_target(self, chosen_skill, opponents, allies):
        if chosen_skill.skill_type == "damage":
          if chosen_skill.target_type == "single":
              chosen_opponent = random.choice(opponents)
          if chosen_skill.target_type == "multi":
              chosen_opponent = random.sample(opponents, chosen_skill.target_qty) if len(opponents) > chosen_skill.target_qty else opponents
          return chosen_opponent

        elif chosen_skill.skill_type == "healing":
          if chosen_skill.target_type == "single":
            if chosen_skill.name == "Binding Heal":
              if len(allies) < 2:
                  chosen_ally = self
              else:
                allies_self_excluded = [h for h in allies if h != self]
                chosen_ally = random.choice(allies_self_excluded)
            else:
              chosen_ally = random.choice(allies)
          if chosen_skill.target_type == "multi":
              chosen_ally = allies
          return chosen_ally

        if chosen_skill.skill_type == "damage_healing":
          if chosen_skill.target_type == "single":
            target_list = opponents + allies
            chosen_opponent = random.choice(target_list)
            return chosen_opponent

        elif chosen_skill.skill_type == "buffs":
          if chosen_skill.target_qty == 0:
            return ['none']
          elif chosen_skill.target_type == "single":
            chosen_ally = random.choice(allies)
            return chosen_ally


    def ai_action(self, opponents, allies):

        if self.status['stunned'] == False:
          if self.status['fear'] == False:
            if self.status['scoff'] == False:
              if self.status['magic_casting'] == False:
                if self.skills:
                    chosen_skill = self.ai_choose_skill(opponents, allies)
                    chosen_target = self.ai_choose_target(chosen_skill, opponents, allies)
                    if opponents:
                        return chosen_skill.execute(chosen_target)
                    else:
                        return f"{self.name} tries to use {chosen_skill}, but it's not implemented or no valid opponents."
                else:
                    return f"{self.name} has no skills to use."
              elif self.status['magic_casting'] == True and self.magic_casting_duration == 0:
                return self.casting_magic.execute(self.casting_magic_target)
              elif self.status['magic_casting'] == True and self.magic_casting_duration > 0:
                return f"{self.name} is casting {self.casting_magic.name}."
            else:
               for debuff in self.debuffs:
                if debuff.name == "Scoff":
                   damage_skills = [skill for skill in self.skills if skill.target_type == "single" and skill.skill_type in ["damage", "damage_healing"] and skill.if_cooldown == False]
                   chosen_skill = random.choice(damage_skills) if damage_skills else None
                   chosen_target = debuff.initiator
                   return chosen_skill.execute(chosen_target)
          else:
            return f"{self.name} is running in fear."
        else:
            return f"{self.name} can't move."

    def player_action(self, hero, opponents, allies):
        # Update all status effects at the beginning of the action
        #self.update_status_effects()
        self.hero = hero
        # Proceed with action if not stunned
        if self.status['stunned']  == False:
          if self.status['fear'] == False:
            if self.status['magic_casting'] == False:
              if self.skills:
                  chosen_targets = 'Back to skill chosen'
                  while chosen_targets == 'Back to skill chosen':
                    chosen_skill = hero.player_choose_skill(hero)
                    if chosen_skill.skill_type == "damage" or chosen_skill.skill_type == "damage_healing":
                      if len(opponents) > 1: #if their is plural enemy available
                        if chosen_skill.target_type == "multi":
                            chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)
                        elif chosen_skill.target_type == "single":
                          if chosen_skill.target_qty == 0:
                            chosen_targets = ['none'] # for non target type skill such as Shadow Evation
                          else:
                            chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)[0]
                      else: #if there is only one enemy available
                        if chosen_skill.target_qty == 0:
                          chosen_targets = ['none']
                        else:
                          chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)[0]

                    if chosen_skill.skill_type == "healing" or chosen_skill.skill_type == "buffs":
                      if chosen_skill.target_type == "multi":
                          chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)
                      elif chosen_skill.target_type == "single":
                        if chosen_skill.target_qty == 0:
                          chosen_targets = ['none'] # for non target type skill such as Shadow Evation
                        else:
                          chosen_targets = hero.player_choose_target(opponents, allies, chosen_skill, num_targets = chosen_skill.target_qty)[0]
                    if chosen_skill.skill_type == "summon":
                      chosen_targets = ['none']

                  # Skill and Target chosen finish, start execution
                  if opponents:
                    if chosen_targets == ['none']:
                      print('***************************************************************************************************************')
                      return chosen_skill.execute(chosen_targets)
                    else:
                      return chosen_skill.execute(chosen_targets)  # Pass opponents
                  else:
                      return f"{self.name} tries to use {chosen_skill}, but it's not implemented or no valid opponents."
              else:
                  return f"{self.name} has no skills to use."
            elif self.status['magic_casting'] == True and self.magic_casting_duration == 0:
              return self.casting_magic.execute(self.casting_magic_target)
            elif self.status['magic_casting'] == True and self.magic_casting_duration > 0:
              return f"{self.name} is casting {self.casting_magic.name}."
          else:
            return f"{self.name} is running in fear."
        else:
            return f"{self.name} can't move."