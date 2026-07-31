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

### Date

2026-07-31

### Screenshot name

N/A

### Task List

1: Issue found regarding to action restriction skills. Such as Shield Bash Shield Lash, Heroric Charge, etc..
 - Shield Bash shall stun target for one round, but not working, target still can action.
 - Shield Lash, Heroric Charge will apply a scoff debuff to target, force this target to attack scoff initiator on next round (Play cannot control which skill to pick, AI will choose a random single target skill), for a player control hero, it feels like skip the control for that round and hero just action a random sigle target skill to that scoff initiator. 
 - Those logic works well on backend python logic where UI has not been applied. So I think the issue might be from how UI is matching with logic engine.
 - Check game.py, you will see for example when a hero got scoff, how it will perform and how the flow is passed to hero.ai_action() method. Have a deep investigation and understand on this original logic.
 - Check hero.py, you will find how status such as stunned is managed in hero.ai_action(), Have a deep investigation and understand on this original logic.

 2: Have a good investigation on above issue and plan out the best solution for current architecture. Provide a study report. Do not start fix work.

 ### Date

2026-07-31

### Screenshot name

battle_31_07_2026-01

### Task List

1_ Mark_1 and Mark_2, heroes are feeling floating in the air compare to the backgrond. Move them downward a bit to a reasonable place.
2_ Mark_3, Battle log font is still too small, make it bigger.
3_ Mark_3, Battle log content is not ideal, it shall come from python engine output. Investigate game.py file and check display_battle_info() and display_status_updates(). display_status_updates() works at the begining of each round to indicate buff and debuff updates, display_battle_info() works at each hero action and provide damage and status information. Study this logic and update current log display.
4_ Mark_4, Hero profession shall include both faculty + Major, now only major is shown. Eg, Warrior Defence now only shows Defence.
5_ Mark_4, Hero name is not correct, you are now giving random name to heroes which is not good. Hero names are defined in the hero_generator.py there are name groups defined for each hero in same faculty. Different major hero in same faculty share a same name group. Apply a random name selection from the hero name group on his faculty. Try provide different names to the same type of hero (same faculty) in one battle unless number of same hero is more than the pickable name from group, then repetitive name shall be allowed. 
6_ Mark_5, remove this empty area by extend the bottom line of each skill button. Keep skill icon squre shape for a resonable size, fill the empty area with some decoration with good design.
7_ In Team Builder page Player slot, when selecting heros, No name is needed to be displayed, Only display falcuty and major, such as Paladin - Protection, etc.