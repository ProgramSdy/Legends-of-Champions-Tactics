import random
import math
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

class StatusDispell:
    def __init__(self, game):
        self.game = game

    def dispell_status(self, status_list_for_action, hero):
        for status in status_list_for_action:
          if status == 'cold':
            hero.cold_duration = 0
            hero.agility = hero.agility + hero.agility_reduced_amount_by_frost_bolt  # Restore original agility
            hero.agility_reduced_amount_by_frost_bolt = 0 # Reset the amount of agility reduced by frost bolt
            hero.status['cold'] = False
            self.game.display_battle_info(f"{BLUE}{hero.name}'s cold effect has been dispelled. {hero.name}'s agility has returned to {hero.agility}.{RESET}")
          elif status == 'shadow_word_pain':
            hero.shadow_word_pain_debuff_duration = 0
            hero.shadow_word_pain_continuous_damage = 0 # Reset shadow word pain continuous_damage
            hero.status['shadow_word_pain'] = False
            self.game.display_battle_info(f"{BLUE}{hero.name}'s Shadow Word Pain effect has been dispelled. {hero.name} is no longer feeling pain.{RESET}")
          elif status == 'poisoned_dagger':
            hero.poisoned_dagger_debuff_duration = 0
            hero.poisoned_dagger_continuous_damage = 0 # Reset shadow word pain continuous_damage
            hero.status['poisoned_dagger'] = False
            hero.poisoned_dagger_stacks = 0
            self.game.display_battle_info(f"{BLUE}{hero.name}'s Poisoned Dagger effect has been dispelled. {hero.name} is no long poisoned.{RESET}")
          elif status == 'holy_word_punishment':
            hero.status['holy_word_punishment'] = False
            for debuff in hero.debuffs:
              if debuff.name == "Holy Word Punishment":
                debuff.duration = 0
                hero.debuffs.remove(debuff)
                hero.buffs_debuffs_recycle_pool.append(debuff)
                self.game.display_battle_info(f"{BLUE}{hero.name}'s Holy Word Punishment effect has been dispelled. {hero.name} is no long under punishment.{RESET}")
          elif status == 'shadow_word_insanity':
            hero.status['shadow_word_insanity'] = False
            hero.shadow_word_insanity_duration = 0
            self.game.display_battle_info(f"{BLUE}{hero.name}'s Shadow Word Insanity effect has been dispelled. {hero.name} is no long insane.{RESET}")
          elif status == 'unholy_frenzy':
            for buff in hero.buffs:
              if buff.name == "Unholy Frenzy":
                buff.duration = 0
                hero.buffs.remove(buff)
                hero.buffs_debuffs_recycle_pool.append(buff)
                hero.status['unholy_frenzy'] = False
                hero.unholy_frenzy_continuous_damage = 0
                hero.damage = hero.damage - hero.damage_increased_amount_by_unholy_frenzy  # Restore original damage
                hero.damage_increased_amount_by_unholy_frenzy = 0 # Reset the amount of damage increased by unholy frenzy
                hero.agility = hero.agility - hero.agility_increased_amount_by_unholy_frenzy  # Restore original damage
                hero.agility_increased_amount_by_unholy_frenzy = 0 # Reset the amount of damage increased by unholy frenzy
                self.game.display_battle_info(f"{BLUE}{hero.name}'s Unholy Frenzy effect has been dispelled. {hero.name}'s damage has returned to {hero.damage}, {hero.name}'s agility has returned to {hero.agility}{RESET}")
          elif status == 'curse_of_agony':
            hero.status['curse_of_agony'] = False
            hero.curse_of_agony_duration = 0
            i = random.randint(0, 3)
            hero.curse_of_agony_continuous_damage = [0, 0, 0, 0] # Reset shadow word pain continuous_damage
            self.game.display_battle_info(f"{BLUE}{hero.name}'s Curse of Agony effect has been dispelled. {hero.name} has recovered from agony{RESET}")
          elif status == 'bleeding_slash':
            hero.status['bleeding_slash'] = False
            hero.bleeding_slash_duration = 0
            hero.bleeding_slash_continuous_damage = 0
            self.game.display_battle_info(f"{BLUE}{hero.name}'s bleeding from slash has stopped. {hero.name}'s wound has been cured{RESET}")
          elif status == 'bleeding_sharp_blade':
            hero.status['bleeding_sharp_blade'] = False
            hero.sharp_blade_debuff_duration = 0
            hero.sharp_blade_continuous_damage = 0
            self.game.display_battle_info(f"{BLUE}{hero.name}'s bleeding from sharp blade has stopped. {hero.name}'s wound has been cured{RESET}")
          elif status == 'fear':
            hero.status['fear'] = False
            for debuff in hero.debuffs:
              if debuff.name == "Curse of Fear":
                debuff.duration = 0
                for skill in debuff.initiator.skills:
                      if skill.name == "Curse of Fear":
                        skill.is_available = True
                hero.debuffs.remove(debuff)
                hero.buffs_debuffs_recycle_pool.append(debuff)
                self.game.display_battle_info(f"{BLUE}{hero.name} has recovered from fear.{RESET}")
          elif status == 'shadow_bolt':
            hero.shadow_bolt_duration = 0
            hero.shadow_resistance = hero.shadow_resistance + hero.shadow_resistance_reduced_amount_by_shadow_bolt
            hero.shadow_resistance_reduced_amount_by_shadow_bolt = 0
            hero.status['shadow_bolt'] = False
            self.game.display_battle_info(f"{BLUE}{hero.name} is no longer vulnerable towards shadow attack. {hero.name}'s shadow resistance has returned to {hero.shadow_resistance}.{RESET}")
          elif status == 'corrosion':
            hero.corrosion_duration = 0
            hero.corrosion_continuous_damage = 0
            hero.defense = hero.defense + hero.defense_reduced_amount_by_corrosion
            hero.defense_reduced_amount_by_corrosion = 0
            hero.status['corrosion'] = False
            self.game.display_battle_info(f"{BLUE}{hero.name} is no longer corroded. Corrosion effect has faded away from {hero.name}.{RESET}")
          elif status == 'soul_siphon':
            hero.status['soul_siphon'] = False
            for debuff in hero.debuffs:
              if debuff.name == "Soul Siphon":
                debuff.duration = 0
                hero.soul_siphon_continuous_damage = 0
                hero.debuffs.remove(debuff)
                hero.buffs_debuffs_recycle_pool.append(debuff)
                self.game.display_battle_info(f"{BLUE}{hero.name}'s soul has stopped hurting. Soul Siphon effect has faded away from {hero.name}.{RESET}")
                if debuff.initiator.hp > 0:
                  self.game.display_battle_info(f"{BLUE}{debuff.initiator.name} has gain life through Soul Siphon. {debuff.initiator.take_healing(hero.soul_siphon_healing_amount)}{RESET}")
                hero.soul_siphon_healing_amount = 0
          elif status == 'immolate':
              hero.status['immolate'] = False
              for debuff in hero.debuffs:
                if debuff.name == "Immolate":
                  debuff.duration = 0
                  hero.immolate_continuous_damage = 0
                  hero.damage = hero.damage + hero.damage_reduced_amount_by_immolate
                  hero.damage_reduced_amount_by_immolate = 0
                  hero.debuffs.remove(debuff)
                  hero.buffs_debuffs_recycle_pool.append(debuff)
                  self.game.display_battle_info(f"{BLUE}{hero.name} is no longer burned. Immolate effect has faded away from {hero.name}.{RESET}")
          elif status == 'void_connection':
            for buff in hero.buffs:
              if buff.name == "Void Connection":
                  buff.duration = 0
                  buff.effect = 0
                  hero.status['void_connection'] = False
                  hero.buffs.remove(buff)
                  hero.buffs_debuffs_recycle_pool.append(buff)
                  self.game.display_status_updates(f"{BLUE}{hero.name} is no longer connecting with {buff.initiator.name}. The connection has finished. {RESET}")
          elif status == 'hell_flame':
            hero.status['hell_flame'] = False
            self.game.display_status_updates(f"{BLUE}{hero.name} is no longer in Hell Flame status.{RESET}")
          elif status == 'holy_infusion':
            hero.status['holy_infusion'] = False
            self.game.display_status_updates(f"{BLUE}{hero.name} is no longer in Holy Infusion status.{RESET}")
          elif status == 'frost_fever':
            hero.status['frost_fever'] = False
            for debuff in hero.debuffs:
              if debuff.name == "Frost Fever":
                debuff.duration = 0
                hero.frost_fever_continuous_damage = 0
                hero.agility = hero.agility + hero.agility_reduced_amount_by_frost_fever  # Restore original agility
                hero.agility_reduced_amount_by_frost_fever = 0 
                hero.debuffs.remove(debuff)
                hero.buffs_debuffs_recycle_pool.append(debuff)
                self.game.display_status_updates(f"{BLUE}{hero.name}'s Frost Fever has disappeared. {hero.name}'s agility has returned to {hero.agility}.{RESET}")
          elif status == 'icy_squall':
            for debuff in hero.debuffs:
              if debuff.name == "Icy Squall":
                  debuff.duration = 0
                  hero.status['icy_squall'] = False
                  hero.frost_resistance = hero.frost_resistance + hero.frost_resistance_reduced_amount_by_icy_squall
                  hero.frost_resistance_reduced_amount_by_icy_squall = 0
                  hero.debuffs.remove(debuff)
                  hero.buffs_debuffs_recycle_pool.append(debuff)
                  self.game.display_status_updates(f"{BLUE}{hero.name} is no longer vulnerable towards frost attack. {hero.name}'s frost resistance has returned to {hero.frost_resistance}.{RESET}")
          elif status == 'necrotic_decay':
            for debuff in hero.debuffs:
                if debuff.name == "Necrotic Decay":
                  debuff.duration = 0
                  hero.status['necrotic_decay'] = False
                  hero.necrotic_decay_continuous_damage = 0
                  if 'necrotic_decay' in hero.healing_reduction_effects:  # Ensure it is removed when expired
                    del hero.healing_reduction_effects['necrotic_decay']
                  hero.debuffs.remove(debuff)
                  hero.buffs_debuffs_recycle_pool.append(debuff)
                  self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from Necrotic Decay.{RESET}")
          elif status == 'virulent_infection':
            for debuff in hero.debuffs:
                if debuff.name == "Virulent Infection":
                  debuff.duration = 0
                  hero.status['virulent_infection'] = False
                  hero.virulent_infection_continuous_damage = 0
                  hero.debuffs.remove(debuff)
                  hero.buffs_debuffs_recycle_pool.append(debuff)
                  self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from Virulent Infection.{RESET}")
          elif status == 'blood_plague':
            print("blood plague detected")
            for debuff in hero.debuffs:
                if debuff.name == "Blood Plague":
                  debuff.duration = 0
                  hero.status['blood_plague'] = False
                  hero.blood_plague_continuous_damage = 0
                  hero.blood_plague_blood_drain = 0
                  hero.debuffs.remove(debuff)
                  hero.buffs_debuffs_recycle_pool.append(debuff)
                  self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from Blood Plague.{RESET}")   
          elif status == 'bleeding_crimson_cleave':
              print("bleeding crimson cleave detected")
              hero.bleeding_crimson_cleave_duration = 0
              hero.bleeding_crimson_cleave_continuous_damage = 0
              hero.status['bleeding_crimson_cleave'] = False
              self.game.display_status_updates(f"{BLUE}{hero.name} has stopped bleeding. Their wound from Crimson Cleave has recovered.{RESET}") 
          elif status == 'cumbrous_axe':
            for buff in hero.buffs:
                if buff.name == "Cumbrous Axe":
                  buff.duration = 0
                  hero.status['cumbrous_axe'] = False
                  if 'cumbrous_axe' in hero.healing_boost_effects:  # Ensure it is removed when expired
                    del hero.healing_boost_effects['cumbrous_axe']
                  hero.buffs.remove(buff)
                  hero.buffs_debuffs_recycle_pool.append(buff)
                  self.game.display_status_updates(f"{BLUE}{hero.name}'s Cumbrous Axe effect has disappeared. {hero.name} has stopped receiving boost healing.{RESET}")    
          elif status == 'scoff':
            hero.status['scoff'] = False
            for debuff in hero.debuffs:
              if debuff.name == "Scoff":
                debuff.duration = 0
                hero.debuffs.remove(debuff)
                hero.buffs_debuffs_recycle_pool.append(debuff)
                self.game.display_status_updates(f"{RED}{hero.name} has recovered from scoff.{RESET}")  
          elif status == 'hammer_of_revenge':
              hero.hammer_of_revenge_duration = 0
              hero.damage = hero.damage + hero.damage_reduced_amount_by_hammer_of_revenge
              hero.damage_reduced_amount_by_hammer_of_revenge = 0
              hero.status['hammer_of_revenge'] = False
              self.game.display_status_updates(f"{BLUE}{hero.name} is no longer feeling powerless. {hero.name}'s damage has returned to {hero.damage}.{RESET}")  
          elif status == 'purify_healing':
            for buff in hero.buffs:
              if buff.name == "Purify Healing":
                buff.duration = 0
                hero.status['purify_healing'] = False
                hero.buffs.remove(buff)
                hero.buffs_debuffs_recycle_pool.append(buff)
                self.game.display_status_updates(f"{BLUE}{hero.name}'s Purify Healing from {buff.initiator.name} has disappeared.{RESET}")
          elif status == 'shield_of_protection':
                hero.shield_of_protection_duration = 0
                hero.status['shield_of_protection'] = False
                self.game.display_status_updates(f"{BLUE}{hero.name} is no longer protected by Holy Light, Shield of Protection has disappeared.{RESET}")  





