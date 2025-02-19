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
                    self.game.display_status_updates(f"{BLUE}{hero.name} has stopped bleeding.{RESET}")

            # Handle Shield of Righteous Buff
            if hero.status['shield_of_righteous'] and hero.hp > 0:
              if hero.shield_of_righteous_duration > 0:
                  hero.shield_of_righteous_duration -= 1
                  self.game.display_status_updates(f"{BLUE}{hero.name}'s Shield of Righteous effect duration is {hero.shield_of_righteous_duration} rounds{RESET}")
                  if hero.shield_of_righteous_duration == 0:
                      hero.defense = hero.defense - hero.defense_increased_amount_by_shield_of_righteous  # Restore original defense
                      hero.defense_increased_amount_by_shield_of_righteous = 0 # Reset the amount of defense increased by shield of righteous
                      hero.shield_of_righteous_stacks = 0 # Reset stack count
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
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s Poisoned Dagger duration is {hero.poisoned_dagger_debuff_duration} rounds. {hero.take_damage(hero.poisoned_dagger_continuous_damage + variation)}{RESET}")
                elif hero.poisoned_dagger_debuff_duration == 0:
                    hero.poisoned_dagger_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['poisoned_dagger'] = False
                    hero.poisoned_dagger_stacks = 0
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer poisoned.{RESET}")

            # Handle Sharp Blade Debuff Duration
            if hero.status['bleeding_sharp_blade'] and hero.hp > 0:
                hero.sharp_blade_debuff_duration -=1
                if hero.sharp_blade_debuff_duration > 0:
                    variation = random.randint(-2, 2)
                    self.game.display_status_updates(f"{BLUE}{hero.name}'s bleeding effect from Sharp Blade is {hero.sharp_blade_debuff_duration} rounds. {hero.take_damage(hero.sharp_blade_continuous_damage + variation)}{RESET}")
                elif hero.sharp_blade_debuff_duration == 0:
                    hero.sharp_blade_continuous_damage = 0 # Reset shadow word pain continuous_damage
                    hero.status['bleeding_sharp_blade'] = False
                    self.game.display_status_updates(f"{BLUE}{hero.name} is no longer bleeding.{RESET}")

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

            # Casting Magic Duration
            if hero.status['magic_casting'] == True and hero.hp > 0:
              hero.magic_casting_duration -=1
              self.game.display_status_updates(f"{BLUE}{hero.name} is casting {hero.casting_magic.name}. Casting remains {hero.magic_casting_duration} rounds{RESET}")

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
                        basic_damage = round((debuff.initiator.original_damage - hero.frost_resistance) * 1/3)
                        variation = random.randint(-1, 1)
                        actual_damage = max(1, basic_damage + variation)
                        hero.frost_fever_continuous_damage = round(actual_damage * debuff.effect)
                        self.game.display_status_updates(f"{BLUE}{hero.name}'s Frost Fever duration is {debuff.duration} rounds. {hero.take_damage(hero.frost_fever_continuous_damage)}{RESET}")

                      elif buff.duration == 0:
                          hero.status['frost_fever'] = False
                          hero.frost_fever_continuous_damage = 0
                          hero.agility = hero.agility + hero.agility_reduced_amount_by_frost_fever  # Restore original agility
                          hero.agility_reduced_amount_by_frost_fever = 0 
                          hero.debuffs.remove(debuff)
                          hero.buffs_debuffs_recycle_pool.append(debuff)
                          self.game.display_status_updates(f"{BLUE}{hero.name}'s Frost Fever has disappeared. {hero.name}'s agility has returned to {hero.agility}{RESET}")

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

                