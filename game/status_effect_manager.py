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

class StatusEffectManager:
    def __init__(self, game):
        self.game = game

    def check_heroes_status_effects(self, hero):
        if hero.hp > 0: # Only process heroes who are not defeated
            # Casting Magic Duration
            if hero.status['magic_casting'] == True and hero.hp > 0:
              hero.magic_casting_duration -=1
              self.game.display_status_updates(f"{BLUE}{hero.name} is casting {hero.casting_magic.name}. Casting remains {hero.magic_casting_duration} rounds{RESET}")
            
            # Purify Healing Buff Duration
            if hero.status['purify_healing'] and hero.hp > 0:
                for buff in hero.buffs:
                  if buff.name == "Purify Healing":
                      buff.duration -= 1
                      if buff.duration > 0:
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Purify Healing from {buff.initiator.name} lasts {buff.duration} rounds.{RESET}")
                          hero_status_activated = [key for key, value in hero.status.items() if value == True]
                          set_comb = set(hero.list_status_debuff_bleeding) | set(hero.list_status_debuff_disease) | set(hero.list_status_debuff_toxic)
                          equal_status = set(hero_status_activated) & set_comb
                          status_list_for_action = list(equal_status)
                          if status_list_for_action:
                            random.shuffle(status_list_for_action)
                            self.game.display_battle_info(f"{hero.name}'s Purify Healing is taking effect. {self.game.status_dispeller.dispell_status([status_list_for_action[0]], hero)}.")  
                      elif buff.duration == 0:
                          hero.status['purify_healing'] = False
                          hero.buffs.remove(buff)
                          hero.buffs_debuffs_recycle_pool.append(buff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Purify Healing from {buff.initiator.name} has disappeared.{RESET}")
            
            # Aqua Ring Buff Duration
            if hero.status['aqua_ring'] and hero.hp > 0:
                for buff in hero.buffs:
                  if buff.name == "Aqua Ring":
                      variation = random.randint(-2, 2)
                      basic_healing = 15
                      actual_healing = basic_healing + variation
                      buff.duration -= 1
                      if buff.duration > 0:
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Aqua Ring from {buff.initiator.name} lasts {buff.duration} rounds. {hero.take_healing(actual_healing)}{RESET}")
                          hero_status_activated = [key for key, value in hero.status.items() if value == True]
                          set_comb = set(hero.list_status_debuff_magic) |  set(hero.list_status_debuff_toxic)
                          equal_status = set(hero_status_activated) & set_comb
                          status_list_for_action = list(equal_status)
                          if status_list_for_action:
                            random.shuffle(status_list_for_action)
                            self.game.display_battle_info(f"{hero.name}'s Aqua Ring is taking effect. {self.game.status_dispeller.dispell_status([status_list_for_action[0]], hero)}.")  
                      elif buff.duration == 0:
                          hero.status['aqua_ring'] = False
                          hero.buffs.remove(buff)
                          hero.buffs_debuffs_recycle_pool.append(buff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Aqua Ring from {buff.initiator.name} has disappeared.{RESET}")

            # Handle Stun Duration
            if hero.status['stunned'] and hero.hp > 0:
                if hero.stun_duration > 0:
                    hero.stun_duration -= 1
                    self.game.display_status_updates(f"{BLUE}{hero.name} is stunned and can't move.{RESET}")
                elif hero.stun_duration == 0:
                    hero.status['stunned'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer stunned.{RESET}")

            # Handle Frost Bolt Cold Debuff Duration
            if hero.status['cold'] and hero.hp > 0:
                hero.cold_duration -=1
                if hero.cold_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is feeling cold and moving slowly. {hero.name}'s Frost Bolt debuff duration is {hero.cold_duration} rounds{RESET}")
                elif hero.cold_duration == 0:
                    hero.agility = hero.agility + hero.agility_reduced_amount_by_frost_bolt  # Restore original agility
                    hero.agility_reduced_amount_by_frost_bolt = 0 # Reset the amount of agility reduced by frost bolt
                    hero.status['cold'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer feeling cold. {hero.name}'s agility has returned to {hero.agility}.{RESET}")

            # Handle Armor Breaker Debuff
            if hero.status['armor_breaker'] and hero.hp > 0:
                hero.armor_breaker_duration -= 1
                self.game.display_status_updates(f"{BLUE}{hero.name}'s Armor Breaker has {hero.armor_breaker_stacks} stacks, and will remain {hero.armor_breaker_duration} rounds.{RESET}")
                if hero.armor_breaker_duration == 0:
                    hero.status['armor_breaker'] = False
                    hero.defense = hero.defense + hero.defense_reduced_amount_by_armor_breaker  # Add back the reduce amount of defense by armor breaker
                    hero.defense_reduced_amount_by_armor_breaker = 0 # Reset the amount of defense reduced by armor breaker
                    hero.armor_breaker_stacks = 0 # Reset stack count
                    self.game.display_status_updates(f"{BLUE}Armor Breaker effect has faded away from {hero.name}. {hero.name}'s defense has returned to {hero.defense}{RESET}")

            # Handle Bleeding_Slash
            if hero.status['bleeding_slash'] and hero.hp > 0:
                hero.bleeding_slash_duration -=1
                if hero.bleeding_slash_duration > 0:
                    variation = random.randint(-2, 2)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s bleeding effect from Slash is {hero.bleeding_slash_duration} rounds. {hero.take_damage(hero.bleeding_slash_continuous_damage + variation)}{RESET}")
                elif hero.bleeding_slash_duration == 0:
                    hero.bleeding_slash_continuous_damage = 0
                    hero.status['bleeding_slash'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} has stopped bleeding. Their wound from Slash has recovered.{RESET}")

            # Handle Shield of Righteous Buff
            if hero.status['shield_of_righteous'] and hero.hp > 0:
              if hero.shield_of_righteous_duration > 0:
                  hero.shield_of_righteous_duration -= 1
                  self.game.display_status_updates(f"{BLUE}{hero.name}'s Shield of Righteous effect duration is {hero.shield_of_righteous_duration} rounds{RESET}")
                  if hero.shield_of_righteous_duration == 0:
                      hero.defense = hero.defense - hero.defense_increased_amount_by_shield_of_righteous  # Restore original defense
                      hero.defense_increased_amount_by_shield_of_righteous = 0 # Reset the amount of defense increased by shield of righteous
                      hero.shield_of_righteous_stacks = 0 # Reset stack count
                      hero.status['shield_of_righteous'] = False
                      self.game.display_status_updates(f"{BLUE}Shield of Righteous effect has faded away from {hero.name}. {hero.name}'s defense has returned to {hero.defense}{RESET}")

            # Handle Shadow Word Pain Debuff Duration
            if hero.status['shadow_word_pain'] and hero.hp > 0:
                hero.shadow_word_pain_debuff_duration -=1
                if hero.shadow_word_pain_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Shadow Word Pain debuff duration is {hero.shadow_word_pain_debuff_duration} rounds. {hero.take_damage(hero.shadow_word_pain_continuous_damage + variation)}{RESET}")
                elif hero.shadow_word_pain_debuff_duration == 0:
                    hero.shadow_word_pain_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['shadow_word_pain'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer feeling pain. Shadow Word Pain effect has faded away from {hero.name}.{RESET}")

            # Handle Poison Dagger Debuff Duration
            if hero.status['poisoned_dagger'] and hero.hp > 0:
                hero.poisoned_dagger_debuff_duration -=1
                if hero.poisoned_dagger_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    if hero.poisoned_dagger_stacks == 1:
                        hero.poisoned_dagger_continuous_damage = math.ceil((hero.poisoned_dagger_applier_damage - hero.poison_resistance)/4)
                    elif hero.poisoned_dagger_stacks == 2:
                        hero.poisoned_dagger_continuous_damage = math.ceil((hero.poisoned_dagger_applier_damage - hero.poison_resistance)/2)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Poisoned Dagger duration is {hero.poisoned_dagger_debuff_duration} rounds. {hero.take_damage(hero.poisoned_dagger_continuous_damage + variation)}{RESET}")
                elif hero.poisoned_dagger_debuff_duration == 0:
                    hero.poisoned_dagger_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['poisoned_dagger'] = False
                    hero.poisoned_dagger_stacks = 0
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer poisoned.{RESET}")

            # Handle Paralyze Blade Debuff Duration
            if hero.status['paralyze_blade'] and hero.hp > 0:
                hero.paralyze_blade_debuff_duration -=1
                if hero.paralyze_blade_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    hero.paralyze_blade_continuous_damage = math.ceil((hero.paralyze_blade_applier_damage - hero.poison_resistance)/6)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Paralyze Blade duration is {hero.paralyze_blade_debuff_duration} rounds. {hero.take_damage(hero.paralyze_blade_continuous_damage + variation)}{RESET}")
                elif hero.paralyze_blade_debuff_duration == 0:
                    hero.paralyze_blade_continuous_damage = 0
                    hero.agility = hero.agility + hero.agility_reduced_amount_by_paralyze_blade  # Restore original agility
                    hero.agility_reduced_amount_by_paralyze_blade = 0
                    hero.status['paralyze_blade'] = False
                    hero.paralyze_blade_stacks = 0
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer effected by Paralyze Blade. {hero.name}'s agility has come back to {hero.agility}. {RESET}")

            # Handle Mixed Venom Debuff Duration
            if hero.status['mixed_venom'] and hero.hp > 0:
                hero.mixed_venom_debuff_duration -= 1
                if hero.mixed_venom_debuff_duration > 0:
                    self.game.display_battle_info(f"{BLUE}{hero.name} is suffering from a Mixed Venom effect. {hero.name}'s Mixed Venom effect is {hero.mixed_venom_debuff_duration} rounds.{RESET}")
                elif hero.mixed_venom_debuff_duration == 0:
                    hero.status['mixed_venom'] = False
                    hero.poison_resistance = hero.poison_resistance + hero.poison_resistance_reduced_amount_by_mixed_venom
                    hero.poison_resistance_reduced_amount_by_mixed_venom = 0
                    self.game.display_battle_info(f"{BLUE}{hero.name} is no longer suffering from a Mixed Venom effect. {hero.name}'s poison resistance has returned to {hero.poison_resistance}.{RESET}")

            # Handle Paralyzed Debuff Duration
            if hero.status['paralyzed'] and hero.hp > 0:
                hero.paralyzed_duration -= 1
                if hero.paralyzed_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is paralyzed and unable to move. Paralyzed duration is {hero.paralyzed_duration} rounds.{RESET}")
                elif hero.paralyzed_duration == 0:
                    hero.status['paralyzed'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from paralysis.{RESET}")

            # Handle Acid Bomb Debuff Duration
            if hero.status['acid_bomb'] and hero.hp > 0:
                hero.acid_bomb_debuff_duration -= 1
                if hero.acid_bomb_debuff_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s weapon is melted. Acid Bomb duration is {hero.acid_bomb_duration} rounds.{RESET}")
                elif hero.acid_bomb_debuff_duration == 0:
                    hero.status['acid_bomb'] = False
                    hero.damage = hero.damage + hero.damage_reduced_amount_by_acid_bomb  # Restore original damage
                    hero.damage_reduced_amount_by_acid_bomb = 0
                    self.game.display_status_updates(f"{BLUE}Acid Bomb effect has faded away from {hero.name}. {hero.name}'s damage has returned to {hero.damage}.{RESET}")

            # Handle Unstable Compound Debuff Duration
            if hero.status['unstable_compound'] and hero.hp > 0:
                hero.unstable_compound_debuff_duration -= 1
                if hero.unstable_compound_debuff_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is affected by Unstable Compound. The effect lasts {hero.unstable_compound_debuff_duration} rounds.{RESET}")
                elif hero.unstable_compound_debuff_duration == 0:
                    variation = random.randint(-2, 2)
                    hero.status['unstable_compound'] = False
                    hero.unstable_compound_damage = hero.unstable_compound_damage + variation
                    self.game.display_status_updates(f"{ORANGE}Unstable Compound from {hero.name} has exploded. {hero.take_damage(hero.sharp_blade_continuous_damage + variation)}{RESET}")

            # Handle Sharp Blade Debuff Duration
            if hero.status['bleeding_sharp_blade'] and hero.hp > 0:
                hero.sharp_blade_debuff_duration -=1
                if hero.sharp_blade_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s bleeding effect from Sharp Blade is {hero.sharp_blade_debuff_duration} rounds. {hero.take_damage(hero.sharp_blade_continuous_damage + variation)}{RESET}")
                elif hero.sharp_blade_debuff_duration == 0:
                    hero.sharp_blade_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['bleeding_sharp_blade'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer bleeding. Their wound from Sharp Blade has recovered.{RESET}")

            # Shadow Evasion Buff Duration
            if hero.status['shadow_evasion'] and hero.hp > 0:
                hero.shadow_evasion_buff_duration -=1
                if hero.shadow_evasion_buff_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is hiding in shadow. {RESET}")
                elif hero.shadow_evasion_buff_duration == 0:
                    hero.status['shadow_evasion'] = False
                    hero.evasion_capability = 0
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s figure slowly emerged from the darkness.{RESET}")

            # Holy Word Shell Buff Duration
            if hero.status['holy_word_shell'] and hero.hp > 0:
                hero.holy_word_shell_duration -=1
                if hero.holy_word_shell_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is protected by Holy Word Shell. The Shell lasts {hero.holy_word_shell_duration} rounds.{RESET}")
                elif hero.holy_word_shell_duration == 0:
                    hero.status['holy_word_shell'] = False
                    hero.holy_word_shell_absorption = 0
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Holy Word Shell has disappeared.{RESET}")

            # Holy Word Redemption Buff Duration
            if hero.status['holy_word_redemption'] and hero.hp > 0:
                for buff in hero.buffs:
                  if buff.name == "Holy Word Redemption":
                      buff.duration -= 1
                      if buff.duration > 0:
                          self.game.display_status_updates(f"{BLUE}{hero.name} is protected by Holy Word Redemption from {buff.initiator.name}. The effect lasts {buff.duration} rounds.{RESET}")
                      elif buff.duration == 0:
                          hero.status['holy_word_redemption'] = False
                          hero.buffs.remove(buff)
                          hero.buffs_debuffs_recycle_pool.append(buff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Holy Word Redemption from {buff.initiator.name} has disappeared.{RESET}")

            # Holy Word Punishment Debuff Duration
            if hero.status['holy_word_punishment'] and hero.hp > 0:
                for debuff in hero.debuffs:
                  if debuff.name == "Holy Word Punishment":
                      debuff.duration -= 1
                      if debuff.duration > 0:
                        variation = random.randint(-1, 1)
                        actual_damage = debuff.effect + variation
                        self.game.display_status_updates(f"{BLUE}{hero.name}'s Holy Word Punishment debuff duration is {debuff.duration} rounds. {hero.take_damage(actual_damage)}{RESET}")

                        # Check any ally hero with Holy Word Redemption from same caster
                        allies_with_buff = [ally for ally in debuff.initiator.allies if ally.hp > 0 and any(buff.name == "Holy Word Redemption" and buff.initiator == debuff.initiator for buff in ally.buffs)]
                        if allies_with_buff:
                          num_allies = len(allies_with_buff)
                          for ally in allies_with_buff:
                            for buff in ally.buffs:
                              if buff.name == "Holy Word Redemption":
                                  buff_healing = math.ceil(buff.effect * actual_damage)
                                  healing_variation = random.randint(-1, 1)
                                  total_healing = round((buff_healing + healing_variation) * hero.take_healing_coefficient(num_allies))
                                  self.game.display_status_updates(f"{BLUE}{ally.name} is protected by Holy Word Redemption. {ally.take_healing(total_healing)}{RESET}")

                      elif debuff.duration == 0:
                          hero.status['holy_word_punishment'] = False
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Holy Word Punishment has disappeared.{RESET}")

            # Shadow Word Insanity Duration
            if hero.shadow_word_insanity_duration > 0 and hero.hp > 0:
              if hero.status['shadow_word_insanity']:
                  self.game.display_status_updates(f"{BLUE}{hero.name} is in an insane state, and unable to distinguish between friends and enemies.{RESET}")
              else:
                  hero.shadow_word_insanity_duration -=1
                  self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from insanity.{RESET}")


            # Handle Holy Fire Duration
            if hero.status['holy_fire'] and hero.hp > 0:
                hero.holy_fire_duration -=1
                if hero.holy_fire_duration > 0:
                    variation = random.randint(-1, 2)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Holy Fire duration is {hero.holy_fire_duration} rounds. {hero.take_healing(hero.holy_fire_continuous_healing + variation)}{RESET}")
                elif hero.holy_fire_duration == 0:
                    hero.holy_fire_continuous_healing = 0 # Reset holy fire continuous healing
                    hero.status['holy_fire'] = False
                    self.game.display_status_updates(f"{BLUE}Holy Fire effect has faded away from {hero.name}. {hero.name} is no longer receiving healing.{RESET}")

            # Handle Summoned Unit
            if hero.is_summoned and hero.hp > 0:
              hero.duration -= 1
              if hero.duration > 0:
                self.game.display_status_updates(f"{BLUE}{hero.name} will vanish in {hero.duration} rounds.{RESET}")
              elif hero.duration == 0:
                hero.hp = 0
                for player_hero in self.game.player_heroes:
                  if hero.name == player_hero.name:
                    self.game.player_heroes.remove(hero)
                    self.game.heroes.remove(hero)
                    break
                else:
                  self.game.opponent_heroes.remove(hero)
                  self.game.heroes.remove(hero)
                if hero.master.status['void_connection']:
                  for buff in hero.master.buffs:
                    if buff.name == "Void Connection":
                      buff.effect = 0
                      hero.master.status['void_connection'] = False
                      hero.master.buffs.remove(buff)
                      hero.master.buffs_debuffs_recycle_pool.append(buff)
                      self.game.display_status_updates(f"{BLUE}{hero.name} has vanished from the battle field. The void connection with {hero.master.name} has been terminated{RESET}")
                else:
                  self.game.display_status_updates(f"{BLUE}{hero.name} has vanished from the battle field.{RESET}")

            # Unholy Frenzy Duration
            if hero.status['unholy_frenzy'] and hero.hp > 0:
                for buff in hero.buffs:
                  if buff.name == "Unholy Frenzy":
                      buff.duration -= 1
                      if buff.duration > 0:
                        variation = random.randint(-1, 1)
                        actual_damage = hero.unholy_frenzy_continuous_damage + variation
                        self.game.display_status_updates(f"{BLUE}{hero.name}'s unholy frenzy duration is {buff.duration} rounds. {hero.take_damage(actual_damage)}{RESET}")

                      elif buff.duration == 0:
                          hero.status['unholy_frenzy'] = False
                          hero.unholy_frenzy_continuous_damage = 0
                          hero.damage = hero.damage - hero.damage_increased_amount_by_unholy_frenzy  # Restore original damage
                          hero.damage_increased_amount_by_unholy_frenzy = 0 # Reset the amount of damage increased by unholy frenzy
                          hero.agility = hero.agility - hero.agility_increased_amount_by_unholy_frenzy  # Restore original damage
                          hero.agility_increased_amount_by_unholy_frenzy = 0 # Reset the amount of damage increased by unholy frenzy
                          hero.buffs.remove(buff)
                          hero.buffs_debuffs_recycle_pool.append(buff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Unholy Frenzy has disappeared. {hero.name}'s damage has returned to {hero.damage}, {hero.name}'s agility has returned to {hero.agility}{RESET}")

            # Handle Curse of Agony DOT Duration
            if hero.status['curse_of_agony'] and hero.hp > 0:
                hero.curse_of_agony_duration -=1
                if hero.curse_of_agony_duration > 0:
                    index = abs(hero.curse_of_agony_duration -4)
                    damage_dealt = hero.curse_of_agony_continuous_damage[index]
                    variation = random.randint(-1, 1)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Curse of Agony duration is {hero.curse_of_agony_duration} rounds. {hero.take_damage(damage_dealt + variation)}{RESET}")
                elif hero.curse_of_agony_duration == 0:
                    hero.curse_of_agony_continuous_damage = [0, 0, 0, 0] # Reset shadow word pain continuous_damage
                    hero.status['curse_of_agony'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Curse of Agony duration is {hero.curse_of_agony_duration} rounds. Curse of Agony has faded away from {hero.name}.{RESET}")

            # Handle Curse of Fear Duration
            if hero.status['fear'] == True and hero.hp > 0:
               for debuff in hero.debuffs:
                  if debuff.name == "Curse of Fear":
                    debuff.duration -=1
                    if debuff.duration > 0:
                        self.game.display_status_updates(f"{BLUE}{hero.name} is in fear. Fear lasts {debuff.duration} rounds{RESET}")
                    else:
                        hero.status['fear'] = False
                        for skill in debuff.initiator.skills:
                              if skill.name == "Curse of Fear":
                                skill.is_available = True
                        hero.debuffs.remove(debuff)
                        hero.buffs_debuffs_recycle_pool.append(debuff)
                        self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from fear.{RESET}")

            # Handle Shadow Bolt Debuff Duration
            if hero.status['shadow_bolt'] and hero.hp > 0:
                hero.shadow_bolt_duration -=1
                if hero.shadow_bolt_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is vulnerable towards shadow attack. {hero.name}'s Shadow Bolt debuff duration is {hero.shadow_bolt_duration} rounds{RESET}")
                elif hero.shadow_bolt_duration == 0:
                    hero.shadow_resistance = hero.shadow_resistance + hero.shadow_resistance_reduced_amount_by_shadow_bolt
                    hero.shadow_resistance_reduced_amount_by_shadow_bolt = 0
                    hero.status['shadow_bolt'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer vulnerable towards shadow attack. {hero.name}'s shadow resistance has returned to {hero.shadow_resistance}.{RESET}")

            # Handle Corrosion Duration
            if hero.status['corrosion'] and hero.hp > 0:
                hero.corrosion_duration -=1
                if hero.corrosion_duration > 0:
                    variation = random.randint(-1, 1)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Corrosion duration is {hero.corrosion_duration} rounds. {hero.take_damage(hero.corrosion_continuous_damage + variation)}{RESET}")
                elif hero.corrosion_duration == 0:
                    hero.corrosion_continuous_damage = 0
                    hero.defense = hero.defense + hero.defense_reduced_amount_by_corrosion
                    hero.defense_reduced_amount_by_corrosion = 0
                    hero.status['corrosion'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer corroded. {hero.name}'s defense has returned to {hero.defense}.{RESET}")

            # Handle Soul Siphon
            if hero.status['soul_siphon'] and hero.hp > 0:
                for debuff in hero.debuffs:
                  if debuff.name == "Soul Siphon":
                      debuff.duration -= 1
                      if debuff.duration > 0:
                          variation = random.randint(-1, 1)
                          damage_dealt = hero.soul_siphon_continuous_damage + variation
                          hero.soul_siphon_healing_amount += round(damage_dealt * 0.75)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Soul Siphon duration is {debuff.duration} rounds. {hero.take_damage(damage_dealt)}{RESET}")
                          #hero.check_if_defeated()
                      elif debuff.duration == 0:
                          hero.soul_siphon_continuous_damage = 0
                          hero.status['soul_siphon'] = False
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s soul has stopped hurting. Soul Siphon effect has faded away from {hero.name}.{RESET}")
                          if debuff.initiator.hp > 0:
                            self.game.display_status_updates(f"{BLUE}{debuff.initiator.name} has gain life through Soul Siphon. {debuff.initiator.take_healing(hero.soul_siphon_healing_amount)}{RESET}")
                          hero.soul_siphon_healing_amount = 0

            # Handle Immolate Duration
            if hero.status['immolate'] and hero.hp > 0:
              for debuff in hero.debuffs:
                  if debuff.name == "Immolate":
                      debuff.duration -= 1
                      if debuff.duration > 0:
                        variation = random.randint(-1, 1)
                        damage_dealt = hero.immolate_continuous_damage + variation
                        debuff.initiator.immolate_accumulate_damage += damage_dealt
                        self.game.display_status_updates(f"{BLUE}{hero.name}'s Immolate duration is {debuff.duration} rounds. {hero.take_damage(damage_dealt)}{RESET}")
                        if debuff.initiator.immolate_accumulate_damage > debuff.initiator.hell_flame_threshold and debuff.initiator.hp > 0:
                          debuff.initiator.status['hell_flame'] = True
                          debuff.initiator.immolate_accumulate_damage = 0
                          if debuff.initiator.status['magic_casting']:
                            self.game.display_status_updates(f"{YELLOW}{debuff.initiator.name} gains the power from hell flame through Immolate. Their next Rain of Fire becomes much powerful{RESET}")
                          else:
                            self.game.display_status_updates(f"{YELLOW}{debuff.initiator.name} gains the power from hell flame through Immolate. Their next Rain of Fire becomes instant{RESET}")
                      elif debuff.duration == 0:
                          hero.immolate_continuous_damage = 0
                          hero.damage = hero.damage + hero.damage_reduced_amount_by_immolate
                          hero.damage_reduced_amount_by_immolate = 0
                          hero.status['immolate'] = False
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{BLUE}{hero.name} is no longer burned. Immolate effect has faded away from {hero.name}.{RESET}")

            # Handle Void Connection Duration
            if hero.status['void_connection'] and hero.hp > 0 :
              if hero.summoned_unit != None and hero.summoned_unit.hp > 0:
                for buff in hero.buffs:
                    if buff.name == "Void Connection":
                        buff.duration -= 1
                        if buff.duration > 0:
                          self.game.display_status_updates(f"{BLUE}{hero.name} is void connecting with {buff.initiator.name}. The connection is {buff.duration} rounds. {RESET}")
                        elif buff.duration == 0:
                          buff.effect = 0
                          hero.status['void_connection'] = False
                          hero.buffs.remove(buff)
                          hero.buffs_debuffs_recycle_pool.append(buff)
                          self.game.display_status_updates(f"{BLUE}{hero.name} is no longer connecting with {buff.initiator.name}. The connection has finished. {RESET}")
              else:
                for buff in hero.buffs:
                    if buff.name == "Void Connection":
                      buff.effect = 0
                      hero.status['void_connection'] = False
                      hero.buffs.remove(buff)
                      hero.buffs_debuffs_recycle_pool.append(buff)
                      self.game.display_status_updates(f"{BLUE}The void connection with {hero.name} has terminated.{RESET}")

            # Handle Hell Flame Status
            if hero.status['hell_flame'] and hero.hp > 0:
              if hero.status['magic_casting']:
                self.game.display_status_updates(f"{BLUE}{hero.name} is in Hell Flame Status, their next Rain of Fire becomes much powerful.{RESET}")
              else:
                self.game.display_status_updates(f"{BLUE}{hero.name} is in Hell Flame Status, their next Rain of Fire becomes instant.{RESET}")

            # Handle Holy InfusionStatus
            if hero.holy_infusion_cooldown > 0 and hero.hp > 0:
              hero.holy_infusion_cooldown -= 1
              if hero.status['holy_infusion']:
                self.game.display_status_updates(f"{BLUE}{hero.name} is in Holy Infusion Status, their next Powerful Healing becomes instant.{RESET}")

            # Frost Fever Duration
            if hero.status['frost_fever'] and hero.hp > 0:
                for debuff in hero.debuffs:
                  if debuff.name == "Frost Fever":
                      debuff.duration -= 1
                      if debuff.duration > 0:
                        basic_damage = round((debuff.initiator.original_damage - hero.frost_resistance) * 1/5)
                        variation = random.randint(-1, 1)
                        actual_damage = max(1, basic_damage + variation)
                        hero.frost_fever_continuous_damage = round(actual_damage * debuff.effect)
                        self.game.display_status_updates(f"{BLUE}{hero.name}'s Frost Fever duration is {debuff.duration} rounds. {hero.take_damage(hero.frost_fever_continuous_damage)}{RESET}")

                      elif debuff.duration == 0:
                          hero.status['frost_fever'] = False
                          hero.frost_fever_continuous_damage = 0
                          hero.agility = hero.agility + hero.agility_reduced_amount_by_frost_fever  # Restore original agility
                          hero.agility_reduced_amount_by_frost_fever = 0 
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Frost Fever has disappeared. {hero.name}'s agility has returned to {hero.agility}.{RESET}")
                          if random.randint(1, 100) <= 30:  # 30% chance infect another target
                            possible_targets = [ally for ally in hero.allies if not ally.status['frost_fever'] and ally is not hero]
                            if possible_targets:
                                spread_target = random.choice(possible_targets)
                                spread_target.status['frost_fever'] = True
                                agility_before_reducing = spread_target.agility
                                spread_target.agility_reduced_amount_by_frost_fever = round(spread_target.original_agility * 0.30)  # Reduce target's agility by 30%
                                spread_target.agility = spread_target.agility - spread_target.agility_reduced_amount_by_frost_fever
                                new_debuff = Debuff(
                                    name='Frost Fever',
                                    duration = 4, # frost fever lasts for 3 rounds
                                    initiator = debuff.initiator,
                                    effect = 0.8
                                    )
                                spread_target.add_debuff(new_debuff)
                                basic_damage = round((debuff.initiator.original_damage - spread_target.frost_resistance) * 1/5)
                                variation = random.randint(-1, 1)
                                actual_damage = max(1, basic_damage + variation)
                                spread_target.frost_fever_continuous_damage = round(actual_damage * new_debuff.effect)
                                self.game.display_status_updates(f"{BLUE}{spread_target.name} is infected with Frost Fever! Their agility is reduced from {agility_before_reducing} to {spread_target.agility}.{RESET}")

            # Icy Squall Duration
            if hero.status['icy_squall'] and hero.hp > 0:
                for debuff in hero.debuffs:
                  if debuff.name == "Icy Squall":
                      debuff.duration -= 1
                      if debuff.duration > 0:
                         self.game.display_status_updates(f"{BLUE}{hero.name} is vulnerable towards frost attack. {hero.name}'s Icy Squall debuff duration is {debuff.duration} rounds.{RESET}")
                      elif debuff.duration == 0:
                          hero.status['icy_squall'] = False
                          hero.frost_resistance = hero.frost_resistance + hero.frost_resistance_reduced_amount_by_icy_squall
                          hero.frost_resistance_reduced_amount_by_icy_squall = 0
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{BLUE}{hero.name} is no longer vulnerable towards frost attack. {hero.name}'s frost resistance has returned to {hero.frost_resistance}.{RESET}")

            # Handle Necrotic Decay Debuff
            if hero.status['necrotic_decay'] and hero.hp > 0:
                for debuff in hero.debuffs:
                    if debuff.name == "Necrotic Decay":
                        debuff.duration -= 1
                        if debuff.duration > 0:
                            basic_damage = round((debuff.initiator.original_damage - hero.death_resistance) * 1/5)
                            variation = random.randint(-1, 1)
                            actual_damage = max(1, basic_damage + variation)
                            hero.necrotic_decay_continuous_damage = round(actual_damage * debuff.effect)
                            self.game.display_status_updates(f"{BLUE}{hero.name}'s Necrotic Decay duration is {debuff.duration} rounds. {hero.take_damage(hero.necrotic_decay_continuous_damage)}.{RESET}")
                        elif debuff.duration == 0:
                            hero.status['necrotic_decay'] = False
                            hero.necrotic_decay_continuous_damage = 0
                            if 'necrotic_decay' in hero.healing_reduction_effects:  # Ensure it is removed when expired
                              del hero.healing_reduction_effects['necrotic_decay']
                            hero.debuffs.remove(debuff)
                            hero.buffs_debuffs_recycle_pool.append(debuff)
                            self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from Necrotic Decay.{RESET}")

            # Handle Virulent Infection Debuff
            if hero.status['virulent_infection'] and hero.hp > 0:
                for debuff in hero.debuffs:
                    if debuff.name == "Virulent Infection":
                        debuff.duration -= 1
                        if debuff.duration > 0:
                            # Apply continuous poison damage
                            basic_damage = round((debuff.initiator.original_damage - hero.poison_resistance) * debuff.effect)
                            variation = random.randint(-1, 1)
                            hero.virulent_infection_continuous_damage = max(1, basic_damage + variation)
                            self.game.display_status_updates(f"{BLUE}{hero.name}'s Virulent Infection is {debuff.duration} rounds. {hero.take_damage(hero.virulent_infection_continuous_damage)}.{RESET}")

                            # Spread Mechanic (Every Other Round)
                            if debuff.duration % 2 == 0:  # Spread occurs on even rounds
                                possible_targets = [ally for ally in hero.allies if not ally.status['virulent_infection'] and ally is not hero]
                                
                                if possible_targets:
                                    spread_target = min(possible_targets, key=lambda e: e.poison_resistance)  # Find lowest poison resistance enemy
                                    spread_chance = round(min(1, 10/(spread_target.poison_resistance + 0.01)) * 100)  # Prevent division by zero
                                    print(f"{RED}Debug: spread chance = {spread_chance}{RESET}")
                                    if random.random() * 100 <= spread_chance:  # Convert to percentage chance
                                        spread_target.status['virulent_infection'] = True
                                        new_debuff = Debuff(
                                            name='Virulent Infection',
                                            duration=4,
                                            initiator=debuff.initiator,
                                            effect=0.4
                                        )
                                        spread_target.add_debuff(new_debuff)
                                        spread_target.virulent_infection_continuous_damage = hero.virulent_infection_continuous_damage
                                        self.game.display_status_updates(f"{spread_target.name} is infected with Virulent Infection as it spreads!")
                        elif debuff.duration == 0:
                            hero.status['virulent_infection'] = False
                            hero.virulent_infection_continuous_damage = 0
                            hero.debuffs.remove(debuff)
                            hero.buffs_debuffs_recycle_pool.append(debuff)
                            self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from Virulent Infection.{RESET}")

            # Handle Blood Plague Debuff
            if hero.status['blood_plague'] and hero.hp > 0:
                for debuff in hero.debuffs:
                    if debuff.name == "Blood Plague":
                        debuff.duration -= 1
                        if debuff.duration > 0:
                            # Apply continuous damage
                            basic_damage = round((debuff.initiator.damage - hero.shadow_resistance) * 1/5)
                            variation = random.randint(-1, 1)
                            actual_damage = max(1, basic_damage + variation)
                            hero.blood_plague_continuous_damage = round(actual_damage * debuff.effect)
                            hero.blood_plague_blood_drain = hero.blood_plague_continuous_damage * debuff.effect
                            self.game.display_status_updates(f"{BLUE}{hero.name}'s Blood Plague is {debuff.duration} rounds. {hero.take_damage(hero.blood_plague_continuous_damage)}.{RESET}")
                            if debuff.initiator.hp > 0:
                              self.game.display_status_updates(f"{BLUE}{debuff.initiator.name} is draining blood. {debuff.initiator.take_healing(hero.blood_plague_blood_drain)}{RESET}")

                            # Spread Mechanic (odd rounds)
                            if debuff.duration == 3 or debuff.duration == 1:  # Spread occurs on odd rounds
                                possible_targets = [ally for ally in hero.allies if not ally.status['blood_plague'] and ally is not hero]
                                definite_targets = [ally for ally in possible_targets if ally.status['bleeding_slash'] or ally.status['bleeding_sharp_blade'] or ally.status['bleeding_crimson_cleave'] ]
                                
                                if definite_targets:
                                   spread_target = random.choice(definite_targets)
                                   spread_target.status['blood_plague'] = True
                                   new_debuff = Debuff(
                                     name='Blood Plague',
                                     duration=4,
                                     initiator=debuff.initiator,
                                     effect=0.8
                                   )
                                   spread_target.add_debuff(new_debuff)
                                   spread_target.blood_plague_continuous_damage = hero.blood_plague_continuous_damage
                                   spread_target.blood_plague_blood_drain = spread_target.blood_plague_continuous_damage * debuff.effect
                                   self.game.display_status_updates(f"{BLUE}{spread_target.name} is infected with Blood Plague due to their bleeding!{RESET}")
                                elif possible_targets:
                                    spread_target = min(possible_targets, key=lambda e: e.shadow_resistance)  # Find lowest shadow resistance enemy
                                    spread_chance = round(min(1, 10/(spread_target.shadow_resistance + 0.01)) * 100)  # Prevent division by zero
                                    print(f"{RED}Debug: spread chance = {spread_chance}{RESET}")
                                    if random.random() * 100 <= spread_chance:  # Convert to percentage chance
                                        spread_target.status['blood_plague'] = True
                                        new_debuff = Debuff(
                                            name='Blood Plague',
                                            duration=4,
                                            initiator=debuff.initiator,
                                            effect=0.8
                                        )
                                        spread_target.add_debuff(new_debuff)
                                        spread_target.blood_plague_continuous_damage = hero.blood_plague_continuous_damage
                                        spread_target.blood_plague_blood_drain = spread_target.blood_plague_continuous_damage * debuff.effect
                                        self.game.display_status_updates(f"{BLUE}{spread_target.name} is infected with Blood Plague as it is spreading!{RESET}")
                        elif debuff.duration == 0:
                            hero.status['blood_plague'] = False
                            hero.blood_plague_continuous_damage = 0
                            hero.blood_plague_blood_drain = 0
                            hero.debuffs.remove(debuff)
                            hero.buffs_debuffs_recycle_pool.append(debuff)
                            self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from Blood Plague.{RESET}")   

            # Handle Bleeding_Crimson_Cleave
            if hero.status['bleeding_crimson_cleave'] and hero.hp > 0:
                hero.bleeding_crimson_cleave_duration -=1
                if hero.bleeding_crimson_cleave_duration > 0:
                    variation = random.randint(-2, 2)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s bleeding effect from Crimson Cleave is {hero.bleeding_crimson_cleave_duration} rounds. {hero.take_damage(hero.bleeding_crimson_cleave_continuous_damage + variation)}{RESET}")
                elif hero.bleeding_crimson_cleave_duration == 0:
                    hero.bleeding_crimson_cleave_continuous_damage = 0
                    hero.status['bleeding_crimson_cleave'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} has stopped bleeding. Their wound from Crimson Cleave has recovered.{RESET}")     

            # Handle Cumbrous Axe Buff
            if hero.status['cumbrous_axe'] and hero.hp > 0:
                for buff in hero.buffs:
                    if buff.name == "Cumbrous Axe":
                        buff.duration -= 1
                        if buff.duration > 0:
                            self.game.display_status_updates(f"{BLUE}{hero.name}'s Cumbrous Axe duration is {buff.duration} rounds. The healing {hero.name} receives is boost.{RESET}")
                        elif buff.duration == 0:
                            hero.status['cumbrous_axe'] = False
                            if 'cumbrous_axe' in hero.healing_boost_effects:  # Ensure it is removed when expired
                              del hero.healing_boost_effects['cumbrous_axe']
                            hero.buffs.remove(buff)
                            hero.buffs_debuffs_recycle_pool.append(buff)
                            self.game.display_status_updates(f"{BLUE}{hero.name}'s Cumbrous Axe effect has disappeared. {hero.name} has stopped receiving boost healing.{RESET}")    

            # Handle Scoff debuff
            for debuff in hero.debuffs:
                if debuff.name == "Scoff":
                  if debuff.duration == 1 and hero.hp > 0:
                      if hero.status['scoff']:
                        self.game.display_status_updates(f"{RED}{hero.name} is in an scoff state, {hero.name} has a deep hatred toward {debuff.initiator.name}.{RESET}")
                        print(f"Debuff Duration = {debuff.duration}")
                      else:
                          debuff.duration -=1
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{RED}{hero.name} has recovered from scoff.{RESET}")  

            # Handle Hammer of Revenge Debuff Duration
            if hero.status['hammer_of_revenge'] and hero.hp > 0:
                hero.hammer_of_revenge_duration -=1
                if hero.hammer_of_revenge_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} feels powerless. {hero.name}'s Hammer of Revenge debuff duration is {hero.hammer_of_revenge_duration} rounds{RESET}")
                elif hero.hammer_of_revenge_duration == 0:
                    hero.damage = hero.damage + hero.damage_reduced_amount_by_hammer_of_revenge
                    hero.damage_reduced_amount_by_hammer_of_revenge = 0
                    hero.status['hammer_of_revenge'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer feeling powerless. {hero.name}'s damage has returned to {hero.damage}.{RESET}")   

            # Handle Shield of Protection Duration
            if hero.status['shield_of_protection'] and hero.hp > 0:
                hero.shield_of_protection_duration -=1
                if hero.shield_of_protection_duration > 0:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is protected by Holy Light and immune towards all damage. {hero.name}'s Shield of Protection duration is {hero.shield_of_protection_duration} rounds. {RESET}")
                elif hero.shield_of_protection_duration == 0:
                    hero.status['shield_of_protection'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer protected by Holy Light, Shield of Protection has disappeared.{RESET}")  
            
            # Handle Wound Backstab Duration
            if hero.status['wound_backstab'] and hero.hp > 0:
                hero.wound_backstab_debuff_duration -= 1
                if hero.wound_backstab_debuff_duration > 0:
                    variation = random.randint(-1, 1)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s wound from Backstab is {hero.wound_backstab_debuff_duration} rounds. {hero.take_damage(hero.wound_backstab_continuous_damage + variation)}{RESET}")
                elif hero.wound_backstab_debuff_duration == 0:
                    hero.wound_backstab_continuous_damage = 0
                    hero.agility = hero.agility + hero.agility_reduced_amount_by_wound_backstab
                    hero.wound_backstab_stacks = 0
                    hero.status['wound_backstab'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from Backstab wound. Their agility has returned to {hero.agility}.{RESET}")

            # Vanish Duration
            if hero.faculty == 'Rogue':
                if hero.is_after_vanish:
                    hero.is_after_vanish = False
            if hero.status['vanish'] and hero.hp > 0:
                hero.vanish_duration -=1
                if hero.vanish_duration == 1:
                    self.game.display_status_updates(f"{BLUE}{hero.name} is hiding in the dark.{RESET}")
                elif hero.vanish_duration == 0:
                    hero.evasion_capability = 0
                    hero.status['vanish'] = False
                    hero.is_after_vanish = True
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s figure slowly emerged from the darkness.{RESET}")
            
            # Water Arrow Duration
            if hero.status['water_arrow'] and hero.hp > 0:
                for buff in hero.buffs:
                  if buff.name == "Water Arrow":
                      buff.duration -= 1
                      if buff.duration > 0:
                        self.game.display_status_updates(f"{BLUE}{hero.name}'s water arrow duration is {buff.duration} rounds.{RESET}")

                      elif buff.duration == 0:
                          hero.status['water_arrow'] = False
                          hero.damage = hero.damage - hero.damage_increased_amount_by_water_arrow  # Restore original damage
                          hero.damage_increased_amount_by_water_arrow = 0 # Reset the amount of damage increased by water arrow
                          hero.agility = hero.agility - hero.agility_increased_amount_by_water_arrow  # Restore original damage
                          hero.agility_increased_amount_by_water_arrow = 0 # Reset the amount of damage increased by water arrow
                          hero.buffs.remove(buff)
                          hero.buffs_debuffs_recycle_pool.append(buff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Water Arrow Buff has disappeared. {hero.name}'s damage has returned to {hero.damage}, {hero.name}'s agility has returned to {hero.agility}{RESET}")
                
            # Glacier Duration
            if hero.status['glacier'] and hero.hp > 0:
                for buff in hero.buffs:
                  if buff.name == "Glacier":
                      buff.duration -= 1
                      if buff.duration > 0:
                        self.game.display_status_updates(f"{BLUE}{hero.name} is frozen and cannot move. {hero.name}'s Glacier duration is {buff.duration} rounds.{RESET}")

                      elif buff.duration == 0:
                          hero.status['glacier'] = False
                          hero.buffs.remove(buff)
                          hero.buffs_debuffs_recycle_pool.append(buff)
                          self.game.display_status_updates(f"{BLUE}{hero.name} has recovered from frozen and started moving slowly. {RESET}")

            # Anti Magic Shield Duration
            if hero.status['anti_magic_shield'] and hero.hp > 0:
                for buff in hero.buffs:
                    if buff.name == "Anti Magic Shield":
                        buff.duration -= 1
                        if buff.duration > 0:
                            self.game.display_status_updates(f"{BLUE}{hero.name} is immuned against all magical effect. {hero.name}'s Anti Magic Shield duration is {buff.duration} rounds.{RESET}")

                        elif buff.duration == 0:
                            hero.status['anti_magic_shield'] = False
                            hero.buffs.remove(buff)
                            hero.buffs_debuffs_recycle_pool.append(buff)
                            self.game.display_status_updates(f"{BLUE}{hero.name}'s Anti Magic Shield effect has disappeared. {RESET}")

            # Scorchbrand Duration
            if hero.status['scorchbrand'] and hero.hp > 0:
                for debuff in hero.debuffs:
                  if debuff.name == "Scorchbrand":
                      variation = random.randint(-2, 2)
                      actual_damage = debuff.initiator.damage + variation
                      hero.scorchbrand_continuous_damage = round((actual_damage - hero.fire_resistance)*(1/3))
                      if hero.scorchbrand_continuous_damage <= 0:
                        hero.scorchbrand_continuous_damage = random.randint(3, 8)
                      debuff.duration -= 1
                      if debuff.duration > 0:
                         self.game.display_status_updates(f"{BLUE}{hero.name} is vulnerable towards fire attack. {hero.name}'s Scorchbrand debuff duration is {debuff.duration} rounds. {hero.take_damage(hero.scorchbrand_continuous_damage)}{RESET}")
                      elif debuff.duration == 0:
                          hero.status['scorchbrand'] = False
                          hero.fire_resistance = hero.fire_resistance + hero.fire_resistance_reduced_amount_by_scorchbrand
                          hero.fire_resistance_reduced_amount_by_scorchbrand = 0
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{BLUE}{hero.name} is no longer vulnerable towards fire attack. {hero.name}'s fire resistance has returned to {hero.fire_resistance}.{RESET}")