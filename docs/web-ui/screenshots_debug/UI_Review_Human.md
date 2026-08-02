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

### Date

2026-08-02

### Screenshot name

battle_02_08_2026-01

### Task List

1_ Mark_1 and Mark_2, In 1v1 Hero with image and hero with fallback image size are significantly different? They need to be identical. Use the size of fall back hero (in Red Rectable), this size is ok for 1v1 battle, current hero with image size is too small. Then fix 2v2 and v3 as well.
2_ Mark_3, In 1v1 hero image feet position (up and down) from play team and enemy team shall be aligned to this Red Line. Their feet postion shall alwasy align with each other.
3_ Mark_4, There is a hero-aura at the bottom of hero image, player is blue and enemy is red, this is a good design, but the ring position is not correctly align with hero position, they are a bit drift to the left. Make sure the middle point align with hero image middle point. (in left and right position)
4_ Make sure the Hp bar still have enough gap with hero image after above modification.
5_ Battle effect:
  5_1: Healing effect now I can see is a gree bar, but this bar is always in a fixed position, this is wrong. This bar shall appears in the location where the hero who receives healing is located.
  5_2: Debuff effect now is like a double purple ring flashing, but this ring is also always in a fixed position, this is wrong. This ring shall appears in the location where the hero who receives debuff is located. Change the ring colour from purple to red.
  5_3: Add a Buff effect similar to debuff effect. Make it similar to debuff effect but change colour to blue. The ring shall appears in the location where the hero who receives buff is located. 
  5_4: Hero attack effect currently design is attack hero make a quick dash forward and defending hero make a quick dash backward. This is correct when player hero attacks, player hero dash to the right and enemy hero also dash to the right. But it is wrong when enemy hero attacks, now I see both hero also dash to the right side. This shall be correct to both hero dash to the left. Because player hero is at the left side and enemy hero stays at right side. If enemy hero attacks, dashing to the left make it feels like enemy hero is dasing forward and player hero is dashing backward.

### Screenshot name

battle_02_08_2026-02

### Task List

1_ Mark_1, When select Choose team for Enemy Composition, enemy slot still shows fake name and major. Please fix it as you fix for Player slot before, where it is suppose to show Faculty-Major.
2_ Add a scrolling bar at the right side in team builder page.
3_ Add a scrolling bar at the right side in battle asset registry page.