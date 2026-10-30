/* This file is generated from content/hero-gallery/*.yaml. Do not edit it directly. */
import type { HeroGalleryContentRegistry } from "./heroGalleryContentTypes";

export const heroGalleryContent = {
  "hero.mage.comprehensiveness": {
    "introduction": "An arcane scholar who commands elemental and arcane attacks.",
    "battleStyle": "Uses ranged magic to exploit opponents and control their pace.",
    "skills": {
      "skill.mage.fireball": {
        "introduction": "A ranged fire attack against one enemy."
      },
      "skill.mage.arcane_missiles": {
        "introduction": "Arcane projectiles directed at multiple enemies."
      },
      "skill.mage.frost_bolt": {
        "introduction": "A ranged frost attack that can inflict Cold."
      }
    }
  },
  "hero.paladin.holy": {
    "introduction": "A paladin who possesses a strong faith in the Holy Light.",
    "battleStyle": "A flexible front-line role focused on healing, cleansing, protection, and ranged holy pressure.",
    "skills": {
      "skill.paladin.purify_healing": {
        "introduction": "Restores one ally and applies a Purify Healing buff to the target. The buff lasts two rounds; on each effective round, it removes one bleeding, disease, or toxic debuff."
      },
      "skill.paladin.holy_blast": {
        "introduction": "Her strong faith in the Holy Light allows her to launch a powerful holy missile at up to two enemies."
      },
      "skill.paladin.shield_of_protection": {
        "introduction": "The Holy Light protects the Paladin from incoming attacks and instantly dispels harmful debuffs. This effect cannot be dispelled."
      }
    }
  },
  "hero.paladin.protection": {
    "introduction": "A resilient paladin who provides regular restore to team, withstands harm and protects the line.",
    "battleStyle": "A control tank who supports team by providing small amount of regular healing over time. Scoff high threatening target and retaliating to debuffs.",
    "skills": {
      "skill.paladin.hammer_of_revenge": {
        "introduction": "Paladin through his hammer to a target, applies distant physical damage.\n>> Special Effect:\n     - Based on the quantity of debuff that is activated on Paladin, Hammer of Revenge applies extra holy damage towards target. 1 debuff: 3-5, 2 debuffs: 6-8, 3 or more debuffs: 9-11.\n     - If Paladin is in Shield of Righteous status, Hammer of Revenge applies a debuff on target that reduces target damage by 20%."
      },
      "skill.paladin.shield_of_righteous": {
        "introduction": "Paladin bash a nearby enemy with his grand shield. This attack will build Shield of Righteous buff on paladin which stacks max 2 times. Each stack increases paladin's defence by 15%. Keep using this skill will refresh buff duration."
      },
      "skill.paladin.heroric_charge": {
        "introduction": "A ranged charge that can applies scoff status and disrupt target casting. Providing a immediate healing effect to Paladin."
      },
      "skill.paladin.holy_aura": {
        "introduction": "Passive: while alive, restores each living teammate at round start."
      }
    }
  },
  "hero.paladin.retribution": {
    "introduction": "A versatile paladin who pressures enemies and heals allies with holy power.",
    "battleStyle": "A front line role who is a combination of a healer and a Dpser.",
    "skills": {
      "skill.paladin.hammer_of_anger": {
        "introduction": "Summons a holy hammer from the sky to smash on any target in the battle field."
      },
      "skill.paladin.crusader_strike": {
        "introduction": "Paladin wields his huge hammer and applies a melee strike on a target. This attack will build Wrath of Crusader buff on paladin which stacks max 2 times. Each stack increases paladin's agility by 75%. Keep using this skill will refresh buff duration."
      },
      "skill.paladin.flash_of_light": {
        "introduction": "Holy light shines on an ally restores their Hp."
      },
      "skill.paladin.wrath_of_crusader": {
        "introduction": "When Paladin is buffed with Wrath of Crusader, Hammer of Anger and Flash of Light apply extra damage/healing to the target.\n1 stack Wrath of Crusader:\n - Hammer of Anger applies extra 3-5 holy damage.\n - Flash of Light applies extra 5-7 healing.\n2 stack Wrath of Crusader:\n - Hammer of Anger applies extra 6-8 holy damage.\n - Flash of Light applies extra 11-13 healing."
      }
    }
  },
  "hero.priest.comprehensiveness": {
    "introduction": "A versatile priest who balances holy restoration with shadow pressure.",
    "battleStyle": "A rear line healer who masters both holy and shadow arts to support allies and weaken enemies.",
    "skills": {
      "skill.priest.holy_smite": {
        "introduction": "A direct holy light strike against one enemy."
      },
      "skill.priest.shadow_word_pain": {
        "introduction": "Marks one enemy with a continuing shadow affliction."
      },
      "skill.priest.binding_heal": {
        "introduction": "Restores an ally and also heals the caster."
      }
    }
  },
  "hero.priest.discipline": {
    "introduction": "A disciplined priest who turns holy conviction toward allies or enemies.",
    "battleStyle": "A rear line healer who turns holy damage on enemies into healing for allies.",
    "skills": {
      "skill.priest.penance": {
        "introduction": "Utilize holy energy to heal an ally or damages an enemy."
      },
      "skill.priest.holy_word_redemption": {
        "introduction": "Places a restorative holy effect on one ally who receives healing whenever the Priest damages an enemy with one of her other skills."
      },
      "skill.priest.holy_word_punishment": {
        "introduction": "Pressures 2 enemies with a continuous holy damage effect."
      },
      "skill.priest.holy_concentration": {
        "introduction": "Priest concentrate on the guide from holy light. Holy Word Redemption will protect an extra hero if priest's hp is equal to or less than 75%."
      }
    }
  },
  "hero.rogue.comprehensiveness": {
    "introduction": "An agile rogue who masters assassination with dual daggers and evasion to control the battlefield.",
    "battleStyle": "An active Dpser who is flexible in both frontline and backline positions.",
    "skills": {
      "skill.rogue.sharp_blade": {
        "introduction": "A swift melee dagger strike that has 50% chance to cause bleeding."
      },
      "skill.rogue.poisoned_dagger": {
        "introduction": "Rogue sneak to a ranged target and perform an attack with poisoned dagger that has 85% chance to apply poison. Poison starts working on the next turn if successful. Poison debuff max 2 stacks."
      },
      "skill.rogue.shadow_evasion": {
        "introduction": "Enable Rogue to dodge all coming attack in the current round."
      }
    }
  },
  "hero.warrior.berserker": {
    "introduction": "A relentless warrior who thrives on aggressive momentum.",
    "battleStyle": "Front line Dpser who master the art of relentless attacks and self-buffing to overwhelm enemies.",
    "skills": {
      "skill.warrior.moon_slash": {
        "introduction": "Move swiftly approaching to enemy and execute a sweeping attack against multiple enemies."
      },
      "skill.warrior.warlust": {
        "introduction": "A self-buff that increases Berserker's damage by 1/3 and enable berserker to immune to control effects for 2 rounds."
      },
      "skill.warrior.strike_of_meteorite": {
        "introduction": "A heavy single-enemy strike that weakens targets' armour. Attack attaches an Armor Breaker debuff to target which stacks up to 2 times, each stack reduces target's armour by 15% for 2 rounds."
      },
      "skill.warrior.blood_frenzy": {
        "introduction": "Passive. After surviving incoming damage, Blood Frenzy can activate based on remaining HP: 50% chance above 25% through 50% HP; 75% chance above 10% through 25% HP; guaranteed at 10% HP or less. It cannot activate above 50% HP or while already active.\nFor 2 rounds, gain 20 Agility and lose round(current Defence ÷ 2) Defence. While active, Moon Slash and Strike of Meteorite restore whole HP equal to 30% of their calculated direct damage; Moon Slash heals separately for each target."
      }
    }
  },
  "hero.warrior.defence": {
    "introduction": "A shield-bearing warrior built to hold ground under pressure.",
    "battleStyle": "Breaks armour, disrupts enemies, and reinforces personal defence.",
    "skills": {
      "skill.warrior.devastate": {
        "introduction": "A forceful attack against one enemy."
      },
      "skill.warrior.shield_bash": {
        "introduction": "A shield attack that can stun."
      },
      "skill.warrior.thunder_pot": {
        "introduction": "A defensive technique with enemy-facing pressure."
      }
    }
  },
  "hero.warrior.weapon_master": {
    "introduction": "A seasoned warrior who masters weapon techniques and pursues decisive physical strikes.",
    "battleStyle": "Front line Tank-Dpser who reduces enemy's healing and armour to secure victory.",
    "skills": {
      "skill.warrior.fatal_strike": {
        "introduction": "A decisive strike with weapon that attaches a debuff which reduces target's healing by 70% for 2 rounds."
      },
      "skill.warrior.armor_crush": {
        "introduction": "A crushing strike that can weaken targets' armour. Attack attaches an Armor Breaker debuff to target which stacks up to 3 times, each stack reduces target's armour by 15% for 2 rounds.\n >> Special Effect:\n   - Debuff stacks two times: activate an extra debuff \"Wound Armor Crush\" which reduces target's agility by 20% for 2 rounds.\n   - Debuff stacks three times: activate an extra debuff \"Bleeding Armor Crush\" which causes 8-12 continuous damage over 3 rounds."
      },
      "skill.warrior.antivenom_potion": {
        "introduction": "Drink an antivenom potion to remove poison effects and recover health. Warrior Weapon Master gains a buff that increases their poison resistance by 45 for 2 rounds."
      }
    }
  }
} as const satisfies HeroGalleryContentRegistry;
