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
    "introduction": "A holy paladin devoted to resilient protection and restoration.",
    "battleStyle": "Combines healing, cleansing, protection, and ranged holy pressure.",
    "skills": {
      "skill.paladin.purify_healing": {
        "introduction": "Restores one ally and can cleanse an eligible harmful effect."
      },
      "skill.paladin.holy_blast": {
        "introduction": "A ranged holy attack that can affect multiple enemies."
      },
      "skill.paladin.shield_of_protection": {
        "introduction": "Protects the caster from incoming damage for a limited time."
      }
    }
  },
  "hero.paladin.protection": {
    "introduction": "A resilient paladin who withstands harm and protects the line.",
    "battleStyle": "Absorbs pressure, disrupts enemies, and supports the team over time.",
    "skills": {
      "skill.paladin.hammer_of_revenge": {
        "introduction": "A ranged holy retaliation that responds to the caster's debuffs."
      },
      "skill.paladin.shield_of_righteous": {
        "introduction": "A melee shield strike that strengthens the caster's defence."
      },
      "skill.paladin.heroric_charge": {
        "introduction": "A ranged charge that can disrupt and draw hostility."
      },
      "skill.paladin.holy_aura": {
        "introduction": "Passive: while alive, restores each living teammate at round start."
      }
    }
  },
  "hero.paladin.retribution": {
    "introduction": "A battle-ready paladin who builds crusading momentum.",
    "battleStyle": "Alternates steady melee pressure with empowered holy attacks and support.",
    "skills": {
      "skill.paladin.hammer_of_anger": {
        "introduction": "A ranged holy attack that benefits from crusader momentum."
      },
      "skill.paladin.crusader_strike": {
        "introduction": "A melee strike that builds Wrath of Crusader."
      },
      "skill.paladin.flash_of_light": {
        "introduction": "Restores an ally, strengthened by Wrath of Crusader."
      }
    }
  },
  "hero.priest.comprehensiveness": {
    "introduction": "A versatile priest who balances holy restoration with shadow pressure.",
    "battleStyle": "Supports wounded allies while maintaining ranged pressure.",
    "skills": {
      "skill.priest.holy_smite": {
        "introduction": "A direct holy attack against one enemy."
      },
      "skill.priest.shadow_word_pain": {
        "introduction": "Marks one enemy with a continuing shadow affliction."
      },
      "skill.priest.binding_heal": {
        "introduction": "Restores an ally and also helps the caster."
      }
    }
  },
  "hero.priest.discipline": {
    "introduction": "A disciplined priest who turns holy conviction toward allies or enemies.",
    "battleStyle": "Adapts between healing, protection, and multi-target pressure.",
    "skills": {
      "skill.priest.penance": {
        "introduction": "Heals an ally or damages an enemy according to the chosen target."
      },
      "skill.priest.holy_word_redemption": {
        "introduction": "Places a restorative holy effect on one ally."
      },
      "skill.priest.holy_word_punishment": {
        "introduction": "Pressures multiple enemies with a holy punishment effect."
      }
    }
  },
  "hero.rogue.comprehensiveness": {
    "introduction": "A quick rogue who uses precision, poison, and evasive movement.",
    "battleStyle": "Prioritises vulnerable enemies while avoiding retaliation.",
    "skills": {
      "skill.rogue.sharp_blade": {
        "introduction": "A swift melee strike that can cause bleeding."
      },
      "skill.rogue.poisoned_dagger": {
        "introduction": "A ranged dagger attack that can apply poison."
      },
      "skill.rogue.shadow_evasion": {
        "introduction": "A self-buff that improves evasion."
      }
    }
  },
  "hero.warrior.berserker": {
    "introduction": "A relentless warrior who thrives on aggressive momentum.",
    "battleStyle": "Pressures several enemies and turns fury into force.",
    "skills": {
      "skill.warrior.moon_slash": {
        "introduction": "A sweeping attack against multiple enemies."
      },
      "skill.warrior.warlust": {
        "introduction": "A self-buff that increases battle aggression."
      },
      "skill.warrior.strike_of_meteorite": {
        "introduction": "A heavy single-enemy attack."
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
    "introduction": "A seasoned weapon master who pursues decisive physical strikes.",
    "battleStyle": "Finishes vulnerable enemies and weakens durable defenders.",
    "skills": {
      "skill.warrior.fatal_strike": {
        "introduction": "A decisive strike that can reduce healing received."
      },
      "skill.warrior.armor_crush": {
        "introduction": "A crushing strike that can weaken armour."
      },
      "skill.warrior.antivenom_potion": {
        "introduction": "A self-directed recovery and poison-resistance action."
      }
    }
  }
} as const satisfies HeroGalleryContentRegistry;
