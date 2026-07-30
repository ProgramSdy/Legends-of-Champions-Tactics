# UI Review Human

## Purpose

Track UI issues found by Human (Daoyu-Project owner)

## Review Entry Template

### Date

2026-07-27

### Screenshot name

battle_27_07_2026-01

### Issue List

Mark_1: Battle Log shall come from actual game engine output.
Mark_2: RED_RECT area, There is a bug in skill buttons, when battle log increses, those button will become vertically larger, I think the bottom is accidentally hooked with battle log bottom line.
Mark_3: Instead of only shows hero status in this bar, I think it can show the hero HP as well. status icon below hp bar.
Mark_4 GREEN_RECT area, this area needs a new layout, give more space for battle logs, battle logs window need to be wider. Skill card/button need to be make reasonable smaller, it is just for click but need consider appearance attractive.
Mark_5: when I move my mouse to the status icon, it shows unknow status, I think data didn't come through correctly.

### Date

2026-07-29

### Screenshot name

N/A

### Task List

1: Currently, only Warrior_Weapon_Master and Rogue_Comprehensiveness is activated. Please activate more heroes. Listed below:
  - Priest_Comprehensiveness
  - Priest_Discipline
  - Paladin_Retribution
  - Paladin_Protection
  - Mage_Comprehensiveness
  - Warrior_Defence
  - Warrior_Weapon_Master
  - Rogue_Comprehensiveness
2: Now there is only battle scene available, add a Team build scene before start battle scene. In team build scene, 
  - Choose 1V1 or 2V2 or 3V3, 
  - Choose available heroes for player team.
  - For enemy team, make two options, 1 random choose, 2 player specify.
  - Player team, all heroes are controled by player.
  - Enemy team, make two options, 1 Computer control (Use the logic from python engine) 2 player control
3: In batle scene, make live 2v2 ad live 3v3 available.
4: In battle scene, show up a popup button when game finishes, click the button will bring you back to Team build scene.


