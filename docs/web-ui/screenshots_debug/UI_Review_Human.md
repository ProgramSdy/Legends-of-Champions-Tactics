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

### Date

2026-08-09

### Screenshot name

team_builder_09_08_2026_01

### Task List

On Team builder page:
1 Mark 1_ In Your Team box: the bottom line of your team rectangle is higher than the bottom line of Player hero rectangle which make player hero box going out of the your team rectangle. There should be a minimal clearance control.

2 Mark 2_ Make Your Team box alwasy show three player hero boxes. Current 1v1 shows one player hero box, 2v2 shows 2. I want alwasy shows three player hero boxes. when 1v1, grey out two hero box and keep the first one. 2v2 grey out the last hero box at right side. 3v3 keep current setup.

3 Mark 3 and 4_ Remove all hero names (from both Your Team box and Hero Selection Matrix) in this page, there shall not be any name mentioned here, only facutly and major information is displayed.

4 Mark 5_ In Your Team box, change PLAYER 1, PLAYER 2, PLAYER 3 to HERO 1, HERO 2, HERO 3

5 Mark 6_ Add hero faculty tab here including "All, Warrior, Mage, Paladin, etc.." If warrior tab is clicked, then only warriors are list in the hero selection matrix, apply this to all other faculty.

6 Mark 7 and 8_ Add left-right arrow here for exploring more heroes.

7 Mark 9 and 10_ Remove the stentance in the red boxes.

8 Make all above changes that are applied to Your Team area apply to Enemy Team box as wel.

9 Add Warrior_Berserker and Paladin_Holy to the roster. 


### Date

2026-08-14

### Screenshot name

Task_14_08_2026_01

### Task List
This task invovles both UI and Python Engine change. We will involve battle formation into our battle, we will start with 2v2 first, not start 3v3 yet.
Check picture Task_14_08_2026_01.png, it hight the rough location where hero shall appear in the 2v2 battle. Red circle is the location for player heroes and green circle is the location for enemy heroes.
There are two battle formation to choose,
Formation 1: hero stay in circle 1 and 2, hero stay in circle 1, position mark as "front", hero stay in circle 2, position mark as "rear". This represent the hero in circle 1 is standing front, and hero in circle two is standing behand.
Formation 2: hero stay in circle 3 and 4, both hero position mark as "front". This represennt the two heroes are standing side by side, both are standing front.
This setup applies to both player and enemy heroes.

UI:
1_ In Team Builder Page, add an option button where player can select battle formation. make option button for enemy team as well. Make good UI design in appearance. enemy team will random select a formation when enemy control is computer.

2_ In Battle page, heroes. will be located in those circles as described above after besing decided from Team Builder Page.

Python Engine:
1_ When hero position is decided in Team Builder Page, those values (either "front" or "rear") will be passed to hero instance. in Hero Class in hero.py, there is a argument "position" being defined in __init__() function (see below), the value of hero position shall be passed to this argument and kept in hero instance.
def __init__(self, sys_init, name, group, is_player_controlled, major, faculty, position):

2_ Hero damage type Skills now have an extra argument called attack_type, for example, see below code piece from warrior berserker. pay attention, this extra argument only apply to those skills where their skill_type="damage", other type of skills are not impact.
self.add_skill(Skill(self, "Strike of Meteorite", self.strike_of_meteorite, target_type="single", skill_type="damage", attack_type = "melee", capable_interrupt_magic_casting=True))

This new argument has now just been applied to warrior, and later when we test, we shall only use warrior weapon master, defence and berserker to make test, other heroes have not been updated with this argument yet. Definition of values of attack_type for each skill from all heroes shall only be authorized by project owner, core team from Codex shall not do it.

attack_type has three value "melee", "ranged_instant", and "ranged_projectile". final damage calculation will be run differently depending on the Hero position we defined before and the attack_type of the damaging skill being used. 
Rule_melee:
 1_ If attacking hero is in a positioin marked as "front", his melee attack can only apply on the defending hero also with a position "front". defending hero with a position "rear" can not be attacked. This shall be applied in both UI (hero in rear position not selectable) and selectable hero list for the skill in python engine (This make sure the Computer controled hero also not able to select rear hero when using melee attack).
 2_ when all defending heroes are defeated, a melee attack from attacking hero can appoach to the defending heroes which has a "rear" position.
 3_ If attacking hero is in a positioin marked as "rear", target selection will follow rule 1_ and 2_
 4_ If attacking hero is in a positioin marked as "rear", his attack will receive a Damage Punishment. final damage will be reduced by 30%. damage calculation management in code will be discussed seperatedly from following up content.

Rule_ranged_projectile:
 1_ attacking hero can attack defending hero from any position.
 2_ Damage Punishment:
     Attack Hero in "front", Defending Hero in "front", no punishment.
     Attack Hero in "front", Defending Hero in "rear", final damage will be reduced by 12.5%.
     Attack Hero in "rear", Defending Hero in "front", final damage will be reduced by 12.5%.
     Attack Hero in "rear", Defending Hero in "rear", final damage will be reduced by 25%.
     damage calculation management in code will be discussed seperatedly from following up content.

Rule_ranged_instant:
 1_ attacking hero can attack defending hero from any position.
 2_ No Damage Punishment for this attack_type skills.

3_ Methodology of passing attack_type through the skill execution pipeline into Hero.take_damage().
Implement a backward-compatible way to pass each Skill.attack_type through the skill execution pipeline into Hero.take_damage().

Objective:

attack_type is already defined on each Skill, for example:

Skill(
    self,
    "Strike of Meteorite",
    self.strike_of_meteorite,
    target_type="single",
    skill_type="damage",
    attack_type="melee",
)

and:

Skill(
    self,
    "Moon Slash",
    self.moon_slash,
    target_type="multi",
    skill_type="damage",
    attack_type="ranged_instant",
)

The goal is for that value to flow automatically like this:

Skill.attack_type
    ↓
Skill.execute()
    ↓
hero skill method
    ↓
target.take_damage(..., attack_type=...)

Do not duplicate "melee", "ranged_instant", etc. inside hero skill methods.

Important compatibility requirement:

There are many existing hero skill methods with different function signatures. Do not make a global breaking change that forces every skill method to immediately accept an attack_type parameter.

Implement a compatibility layer in Skill so existing skill methods continue to work unchanged.

Recommended implementation:

1. In skill.py, import inspect.
2. Add a helper method inside Skill, for example:

def run_skill_action(self, *args):
    signature = inspect.signature(self.skill_action)
    if "attack_type" in signature.parameters:
        return self.skill_action(
            *args,
            attack_type=self.attack_type,
        )
    return self.skill_action(*args)

This helper should:

* inspect the bound hero skill method;
* pass attack_type=self.attack_type only when that skill method explicitly accepts an attack_type parameter;
* otherwise call the existing method exactly as before.

3. In Skill.execute(), route normal skill execution through this helper instead of directly calling self.skill_action(...) where appropriate.

At minimum, update the normal damage execution paths:

Single-target damage:

return self.run_skill_action(hits[0])

Multi-target damage:

return self.run_skill_action(hits)

Review the other self.skill_action(...) calls carefully and only migrate them where doing so is safe and semantically correct.

Do not break special-case skills or functions that intentionally use additional positional parameters such as ally/opponent mode.

4. Update Hero.take_damage() from something like:

def take_damage(self, damage):

to:

def take_damage(self, damage, attack_type="NA"):

Preserve all existing behaviour when attack_type is not provided.

5. Migrate Warrior_Berserker as the first concrete example.

Change:

def moon_slash(self, other_heroes):

to:

def moon_slash(self, other_heroes, attack_type="NA"):

and pass the received value into:

opponent.take_damage(
    damage_dealt,
    attack_type=attack_type,
)

Change:

def strike_of_meteorite(self, other_hero):

to:

def strike_of_meteorite(self, other_hero, attack_type="NA"):

and pass the received value into every take_damage() call:

other_hero.take_damage(
    damage_dealt,
    attack_type=attack_type,
)

Ensure both Blood Frenzy and non-Blood-Frenzy return paths are updated.

6. Preserve the existing Skill definitions as the authoritative source of attack type.

For example:

attack_type="melee"

and:

attack_type="ranged_instant"

must remain defined on the Skill object rather than being repeated inside hero skill functions.

Expected result:

Strike of Meteorite
Skill.attack_type = "melee"
    ↓
Skill.execute()
    ↓
run_skill_action(target)
    ↓
strike_of_meteorite(target, attack_type="melee")
    ↓
target.take_damage(damage, attack_type="melee")

and:

Moon Slash
Skill.attack_type = "ranged_instant"
    ↓
Skill.execute()
    ↓
run_skill_action(targets)
    ↓
moon_slash(targets, attack_type="ranged_instant")
    ↓
target.take_damage(damage, attack_type="ranged_instant")

Constraints:

* Keep existing combat calculations unchanged.
* Do not duplicate damage formulas.
* Do not refactor unrelated hero skills.
* Maintain backward compatibility for skills that do not yet accept attack_type.
* Preserve existing API/adapter behaviour unless required by this change.
* Add or update tests to verify:
    * existing skills still execute;
    * migrated skills receive the correct attack type;
    * take_damage() receives "melee" for Strike of Meteorite;
    * take_damage() receives "ranged_instant" for Moon Slash;
    * skills without an attack_type parameter remain unaffected.

3_ update Hero.take_damage_action(), make it can recieve attack_type argument from Hero.take_damage() 
def take_damage_action(self, damage_dealt, attack_type):

4_ add a new function in Hero class called take_damage_calculation,
def take_damage_calculation(self, damage_dealt, attack_type):
This function will receive damage_dealt and attack_type from Hero.take_damage_action()
This function is where the final damamge calculation take place. use this function to replace below code from Hero.take_damage_action()
{
  self.hp = self.hp - damage_dealt
}
This function shall also recieve the arguments of the position of both the attack hero and the defending hero. (Find a proper way to realize this)
Final damage will be based on the Damage Punishment rule we defined previously for differnt hero position for both attack and defending hero. Therefore in this function, damage_dealt, attack_type, attack hero position and defending hero position are necessary. 

### Date

2026-08-15

### Screenshot name

Task_15_08_2026_01.png
Task_15_08_2026_02.png
Task_15_08_2026_03.png

### Task List
This task is a continuous task from UI-018. Major job is to add battle formation for 3v3 battle. Check attached pictures where they have lighlighted the rough location where hero shall appear in the 3v3 battle. Red circle is the location for player heroes and green circle is the location for enemy heroes.
There are three battle formation to choose:

Task_15_08_2026_01.png demonstrates Formation 1: hero stay in circle 1, 2 and 3, hero stay in circle 1, position mark as "front", hero stay in circle 2 and 3, position mark as "rear". This represent the hero in circle 1 is standing front, and hero in circle 2 and 3 are standing behand.

Task_15_08_2026_02.png demonstrates Formation 2: hero stay in circle 1, 2 and 3, hero stay in circle 1 and 2 position mark as "front", hero stay in circle 3, position mark as "rear". This represent the hero in circle 1 and 2 are standing front, and hero in circle 3 is standing behand.

Task_15_08_2026_03.png deonstrates Formation 3: hero stay in circle 1, 2 and 3, all heroes position mark as "front". This represennt the all three heroes are standing side by side, they are all standing front.

This setup applies to both player and enemy heroes.

UI:
1_ In Team Builder Page, add an option button where player can select battle formation in 3v3. make option button for enemy team as well. Make good UI design in appearance. enemy team will random select a formation when enemy control is computer.

2_ In Battle page, heroes. will be located in those circles as described above after besing decided from Team Builder Page.

Python Engine:
Core project team from Codex can decide if python engine need to be modified to reflect this change.

## Date

2026-08-19

### Screenshot name

N/A

### Task List

1_ Activate a new stage in Stage Map. Stage Name: Paladin's Altar. Location is at the right middle side of the map, where there is a Altar. All design follow the same style as Warrior's Barrack. 
There will be totally 9 battles in this stage.
Battle 1: 2v2, Formation: Front and Rear, Heroes: Paladin_Protection (front), Mage_Comprehensiveness(Rear). 
Battle 2: 1v1, Formation: NA, Hero: Paladin_Protection.
Battle 3: 3v3, Formation: Front 2 and Rear 1, Heroes: Paladin_Protection (front), Warrior_Defence (front), Mage_Comprehensiveness(Rear). 

After finish battle 3, Paladin_Protection is unlocked and can be chosen by player. Pop up a windlow tell player that "Paladin_Protection is unlocked"

Battle 4: 2v2, Formation: Side by Side, Heroes: Paladin_Retribution, Warrior_Weapon_Master. 
Battle 5: 1v1, Formation: NA, Hero: Paladin_Retribution.
Battle 6: 3v3, Formation: Front 2 and Rear 1, Heroes: Paladin_Protection (front), Paladin_Retribution (front), Priest_Descipline (Rear). 

After finish battle 6, Paladin_Retribution is unlocked and can be chosen by player. Pop up a windlow tell player that "Paladin_Retribution is unlocked"

Battle 7: 2v2, Formation: Side by Side, Heroes: Paladin_Holy , Rogue_Comprehensiveness.
Battle 8: 1v1, Formation: NA, Hero: Paladin_Holy.
Battle 9: 3v3, Formation: Side by Side, Heroes: Paladin_Retribution, Paladin_Protection, Paladin_Holy.

After finish battle 9, Paladin_Holy is unlocked and can be chosen by player. Pop up a windlow tell player that "Paladin_Holy is unlocked"

2_ Update battles in Warrior's Barrack.
There will be totally 9 battles in this stage.
Battle 1: 2v2, Formation: Front and Rear, Heroes: Warrior_Baserker (front), Priest_Comprehensiveness(Rear). 
Battle 2: 1v1, Formation: NA, Hero: Warrior_Baserker.
Battle 3: 3v3, Formation: Front 2 and Rear 1, Heroes: Warrior_Baserker (front), Rogue_Comprehensiveness (front), Mage_Comprehensiveness (Rear). 

After finish battle 3, Warrior_Baserker is unlocked and can be chosen by player. Pop up a windlow tell player that "Warrior_Baserker is unlocked"

Battle 4: 2v2, Formation: Side by Side, Heroes: Warrior_Baserker, Warrior_Weapon_Master. 
Battle 5: 1v1, Formation: NA, Hero: Warrior_Weapon_Master.
Battle 6: 3v3, Formation: Front 2 and Rear 1, Heroes: Warrior_Weapon_Master (front), Paladin_Retribution (front), Priest_Descipline (Rear). 

After finish battle 6, Player is granted with a item card. Pop up a windlow tell player that "You have granted an item card".

Battle 7: 2v2, Formation: Front and Rear, Heroes: Warrior_Defence (Front), Priest_Descipline (Rear). 
Battle 8: 1v1, Formation: NA, Hero: Warrior_Defence.
Battle 9: 3v3, Formation: Side by Side, Heroes: Warrior_Weapon_Master, Warrior_Defence, Warrior_Baserker.

After finish battle 9, Warrior_Defence is unlocked and can be chosen by player. Pop up a windlow tell player that "Warrior_Defence is unlocked"


# Date

2026-08-20

### Screenshot name

N/A

### Task List

1_ Game Start Page: after player click START GAME button, it pops up two button, onw is "NEW GAME" and another one is "LOAD GAME". If Player click "NEW GAME", it will popup a window ask player to select a available SLOT, there are totally five SLOT available in saving system. If all five slots are occupied, then player need to select a slot to over-ryde the existing data, shall pop up warning message similar to most of the game design. If Player click "LOAD GAME", then the same popup window shows up and player can select an existing saving data from one of the 5 slot. If there is no exsiting save data, the "LOAD GAME" button shall be greyed out.

2_ For any new game initilized, player's available hero roster is restricted to:

- Warrior Weapon Master
- Mage Comprehensiveness
- Priest Comprehensiveness
- Rogue Comprehensiveness

3_ Current stage picutre at the right top of team builder page for both Warrior's Barrack and Paladin's Altar are wrong, They shall show the exact building of Warrior's Barrack and Paladin's Altar. Find the correct building from stage map and present them properly.

# Date

2026-08-31

### Screenshot name

N/A

### Task List

1_ Add a half transparent Spanner icon on the upper right coner of Stage Map Page. Click it will take us to the Engineering Test and Debugging Page.

2_ Add a proper icon on the upper left coner of Stage Map Page. Click it will take us to Game Start page.

3_ Add a Engineering Test and Debugging Page. This page can be drafted by directly copy Arena Page and with below modifications.
 3_1_ Both Player team and enemy team shall have the full access to all registerd hero roster.
 3_2_ No data saving requested in this page, so this page shall be seperated from any connection or relation towards a player's data. 

 4_ Redesign Arena
 # Arena Mode Redesign (MVP)

Redesign the Arena mode to make it feel more like a roguelike progression (inspired by Slay the Spire), while preserving the core turn-based tactical gameplay of Legends of Champions.

## Overall Structure

- One Arena Run consists of 12 battles.
- Each battle is an independent node.
- Battle type is randomly selected:
  - 1v1
  - 2v2
  - 3v3
- The player should know the upcoming battle type before entering the battle.

## Hero Squad Build

Add a extra page for Hero Squad Build at the beginning of an Arena Run:

- The player selects a fixed Hero Squad from all available heroes.
- Available heroes depend on the unlocked heroes from game progress. 
- Current MVP:
  - Arena not activated until player has 6 heroes.
  - Player selects 6 heroes to build a squad.
- This Hero Squad remains locked for the entire Arena Run.
- The player cannot switch heroes outside this squad during the run.

## Team Selection

Can draft by using the current Team Builder Page with necessary modifications.

Before every battle:

- The player chooses the required heroes from the Hero Squad.
- Examples:
  - 1v1 → choose 1 hero
  - 2v2 → choose 2 heroes
  - 3v3 → choose 3 heroes

This creates meaningful strategic decisions based on the enemy composition and battle size.

## Save/Load data system

Arena shall be intergrated into current game save/load data system. 

## Battle Design and enemy team
- 12 Battle type is randomly selected with respected to below distribution.
  - 1v1 (20% posibility)
  - 2v2 (50% posibility)
  - 3v3 (30% posibility)
- Enemy Team rules:
  - Enemy team randomly build, repeated heroes is allowed. 
  - Team formation is randomly picked.
  - For 2v2 formation:
    - Side by Side, all random hero
    - Front and rear, Front hero randomly pick from Warrior and Paladin. Rear hero randomly pick from Mage, Rogue and Priest.
  - For 3v3 formation:
    - Side by Side, all random hero
    - Front 2 Rear 1 and Front 1 Rear 2, Front hero randomly pick from Warrior and Paladin. Rear hero randomly pick from Mage, Rogue and Priest.


## Design Goals

Arena is NOT a tutorial.

The purpose of Arena is to:

- Test the player's understanding of all hero classes.
- Encourage team-building and strategic planning.
- Increase replayability through different Hero Pool combinations.
- Create different runs without changing the core combat system.

Keep the implementation simple (MVP), but design the architecture so future features (battle rewards, relics, branching paths, etc.) can be added easily.

Future Expansion (Not required for MVP)

Design the Arena system so the following features can be added later without major refactoring:

- Battle rewards
- Branching paths
- Elite battles
- Boss battles
- Hero injuries / persistence
- Healing nodes
- Shops
- Arena achievements
- Difficulty modifiers

# Date

2026-09-05

### Screenshot name

N/A

### Task List

We are now improving ONLY the responsive architecture of the BATTLE SCENE.

IMPORTANT BOUNDARY:
Before making any code changes, first inspect the current battle-scene implementation and clearly define:
1. Which files/components/styles are in scope.
2. Which existing systems are NOT in scope.
3. Which current parameters/logic must be preserved exactly.
4. What you plan to change.
5. What you will deliberately not change.

Do not change unrelated UI, gameplay logic, hero data, formation logic, skill logic, backend/Python combat logic, Team Builder, Squad Builder, Arena Hub, startup/save screen, assets, art, text, battle rules, or other screens.

The current battle presentation has been fine-tuned and works well at a 1920×1080 reference setup. Treat the current 1920×1080 presentation as the visual baseline/reference. Do not redesign or retune that baseline unless strictly necessary to implement the responsive framework.

GOAL

Refactor the battle scene into a clear responsive presentation architecture that can later support these six viewport configurations:

1. Monitor
2. Laptop Large
3. Laptop Medium
4. Pad
5. Pad Mini
6. Phone Landscape only

Do NOT try to redesign all six layouts in this task unless required. The immediate priority is establishing the correct architecture and preserving the current 1920×1080 result.

--------------------------------------------------
A. BATTLE PRESENTATION LAYERS
--------------------------------------------------

Please structure/reason about the battle scene as five conceptual presentation layers:

Layer 1 — Arena / World Background
- Arena/background/environment only.
- Responsible for battlefield background scaling/cropping.

Layer 2 — Combat Actors
- Heroes.
- Future summons/pets/temporary combat actors.
- Actor placement belongs to the battlefield coordinate system.

Layer 3 — Combat VFX
- Projectiles.
- Spell effects.
- Hit effects.
- Ground effects.
- Other world-space combat effects.
- Do not mix VFX positioning logic into HUD layout logic.

Layer 4 — World-Anchored UI
- Hero-related UI that follows a battlefield actor.
- Examples: target indicators, HP/status indicators if/when displayed above heroes, casting indicators, floating damage/healing numbers, selection markers.
- This layer follows world/battlefield positions but may later use minimum readable screen sizes.

Layer 5 — Screen UI / HUD
This includes the existing battle HUD such as:
- top battle header;
- round/turn UI;
- left player hero/team bars;
- right enemy hero/team bars;
- active hero panel;
- bottom skill slots/cards;
- battle log;
- speed controls;
- auto battle;
- select skill;
- resign;
- other battle-screen HUD controls.

The HUD is screen-space responsive UI and should remain conceptually separate from the battlefield/world coordinate system.

Do not create unnecessary complexity if the current DOM does not require five physical root elements. The important requirement is a clear responsibility boundary between these systems.

--------------------------------------------------
B. PRESERVE EXISTING HERO SCALE LOGIC
--------------------------------------------------

This is very important.

Each hero already has a unique hero scaling rate.

There is also existing formation scaling logic. Formation scale differs depending on things such as:
- front/rear positioning;
- side-by-side positioning;
- 2v2 formation;
- 3v3 formation;
- other currently implemented formation-specific presentation cases.

These values have already been manually fine-tuned and work correctly in the current 1920×1080 battle presentation.

DO NOT replace, normalize, recompute, retune, simplify, or remove these existing values.

Current conceptual calculation:

    ExistingHeroScale
    =
    HeroScaleRate
    × FormationScaleRate

Keep that behaviour unchanged.

We now want to add ONE new presentation factor:

    FinalHeroScale
    =
    HeroScaleRate
    × FormationScaleRate
    × BrowserSizeRate

BrowserSizeRate represents viewport/battle-display configuration scaling only.

Important requirements:

- BrowserSizeRate is NOT hero-specific.
- BrowserSizeRate is NOT formation-specific.
- All heroes in the same current browser configuration use the same BrowserSizeRate.
- Existing relative visual size relationships between heroes must therefore remain intact.
- Existing formation-specific size relationships must remain intact.
- At the 1920×1080 reference setup, BrowserSizeRate must be 1.0 so that the current presentation remains visually unchanged.

Example:

    HeroScaleRate = existing value
    FormationScaleRate = existing value
    BrowserSizeRate = 1.0 at reference desktop

Therefore:

    FinalHeroScale = current existing scale

Do not hardcode arbitrary different responsive rates into individual hero definitions.

--------------------------------------------------
C. HERO POSITIONING IS SEPARATE FROM HERO SCALE
--------------------------------------------------

Do NOT use BrowserSizeRate as a general multiplier for hero X/Y positioning.

Size and position are separate concerns.

Hero size:

    HeroScaleRate
    × FormationScaleRate
    × BrowserSizeRate

Hero position:

    Existing formation/reference position
    ->
    projected/mapped into the current Battlefield Viewport

Preserve the existing formation-position logic unless a wrapper/projection step is required.

Do not change the tactical meaning of formation.

Do not move authoritative combat-position logic into CSS or frontend responsive logic.

--------------------------------------------------
D. REFERENCE BATTLEFIELD
--------------------------------------------------

Treat the current 1920×1080 setup as the reference presentation.

The goal is resolution-independent presentation, NOT redesigning the reference layout.

The battle scene should conceptually contain:

    Battle Screen
    |
    +-- Screen HUD
    |
    +-- Battlefield Viewport
        |
        +-- Arena
        +-- Actors
        +-- VFX
        +-- World-Anchored UI

The Battlefield Viewport should provide a stable coordinate/projection context for world elements.

Do not simply scale the entire page as one 1920×1080 canvas because HUD readability/responsive behaviour will later be different from battlefield scaling.

--------------------------------------------------
E. RESPONSIVE CONFIGURATION FOUNDATION
--------------------------------------------------

Prepare the battle architecture for these six configurations:

1. Monitor
2. Laptop Large
3. Laptop Medium
4. Pad
5. Pad Mini
6. Phone Landscape

Current initial viewport threshold direction:

Monitor:
    width >= 1600
    height >= 900

Laptop Large:
    approximately width 1440–1599
    and adequate height around 800+

Laptop Medium:
    approximately width 1180–1439
    and adequate height around 700+

Pad:
    approximately width 900–1179
    landscape

Pad Mini:
    approximately width 700–899
    landscape

Phone:
    landscape only
    generally identified strongly by short viewport height
    approximately max-height around 550px

These thresholds are starting design categories, not permission to blindly redesign the UI.

Please inspect the current battle CSS before deciding the exact implementation.

Height must be considered, not only width.

A viewport that is wide but very short must be able to use a denser battle presentation mode later.

Do not create dozens of width × height combinations.

Prefer a small understandable configuration system.

--------------------------------------------------
F. BATTLE HEIGHT BEHAVIOUR
--------------------------------------------------

Current battle behaviour keeps the page non-scrolling and allows the central battlefield to absorb most vertical compression.

We want to improve this architecture.

Keep the battle scene as a non-scrolling game screen.

Do NOT solve battle responsiveness by introducing normal page scrolling.

Instead, prepare for:
- height-aware HUD density;
- compact/dense HUD modes;
- controlled reduction of padding/gaps;
- a minimum usable battlefield area;
- future structural simplification of HUD at small sizes.

The battlefield should not be the only region sacrificed when viewport height becomes short.

However, do not redesign skill cards/HUD details beyond what is necessary for the architectural foundation in this task.

--------------------------------------------------
G. CSS / IMPLEMENTATION PRINCIPLES
--------------------------------------------------

Where appropriate:

- Prefer CSS variables for battle responsive configuration values.
- Prefer clamp() or continuous responsive sizing for values that should smoothly scale.
- Use breakpoints only when the presentation genuinely changes.
- Keep world/battlefield scaling separate from HUD responsive layout.
- Avoid device-model detection.
- Respond to viewport dimensions/orientation.
- Avoid unnecessary JavaScript if CSS can cleanly handle presentation.
- If JavaScript is required to determine a battle display mode, centralize it rather than scattering independent viewport checks throughout components.

Do not introduce a new framework/library unless clearly necessary.

--------------------------------------------------
H. PHONE ORIENTATION
--------------------------------------------------

Phone support is LANDSCAPE ONLY.

Do not build a portrait battle layout.

Eventually a portrait phone should display a rotate-device message rather than attempting to render the full battle.

For this task, only establish the architecture required for that behaviour if appropriate.

--------------------------------------------------
I. REGRESSION REQUIREMENT
--------------------------------------------------

The most important acceptance test:

At the current 1920×1080 reference viewport, the battle scene should look and behave the same as before this change.

Specifically preserve:
- hero visual sizes;
- relative hero visual sizes;
- formation-dependent hero scaling;
- hero positions;
- arena composition;
- current HUD arrangement;
- battle functionality;
- current controls;
- existing animations/effects;
- all gameplay behaviour.

Do not make visual “improvements” unrelated to responsiveness.

Do not rename or reorganize unrelated code simply for cleanliness.

--------------------------------------------------
J. FIRST RESPONSE BEFORE CODING
--------------------------------------------------

Before editing files, report back with:

1. Current battle-scene files/components/styles involved.
2. Current hero scaling calculation and where it is implemented.
3. Current formation scaling calculation and where it is implemented.
4. Current hero-position calculation and where it is implemented.
5. Current battle layout/viewport structure.
6. Current width/height responsive rules affecting the battle scene.
7. Proposed exact scope boundary.
8. Proposed minimal implementation plan.
9. Any risks of changing the existing 1920×1080 appearance.
10. How you will verify that 1920×1080 remains unchanged.

Then implement only after you have established that boundary.

After implementation, provide:
- files changed;
- exact behaviour changed;
- behaviour intentionally left unchanged;
- test/build/lint results;
- comparison of 1920×1080 before vs after;
- any remaining work needed for the six final responsive layouts.

Again: preserve the current working 1920×1080 hero and formation tuning. This task is to ADD a clean browser-responsive presentation layer, not to replace the existing battle design.


# Date

2026-09-11

### Screenshot name

N/A

### Task List

## 1. Battle-End Conditions Update

# Current Battle-End Conditions

The current battle design has two primary termination conditions:

1. **Elimination victory** — if all heroes on one team become unable to continue fighting, the opposing team wins.
2. **Maximum-round termination** — if neither team has been eliminated when the maximum number of rounds is reached, the battle ends.

The current general maximum is 15 rounds.

# New Battle-End Conditions:

Keep rule 1 as no change.
1. **Elimination victory** — if all heroes on one team become unable to continue fighting, the opposing team wins.

Rule 2 need to be changed. Detail list below:

Maximum-Round Result Hierarchy

Two possible timeout criteria were considered: surviving hero count and remaining HP percentage.

The agreed direction is to use them hierarchically.

- First tiebreaker — surviving heroes

When the maximum round is reached:

> **The team with more surviving heroes wins.**

Example:

 Team A: 3 surviving heroes
 Team B: 2 surviving heroes

Team A wins regardless of remaining HP percentages.

The reasoning is that surviving hero count represents battlefield control and action economy. If combat continued, the team with more active heroes generally has additional actions, skills, targeting options, and combination potential.

- Second tiebreaker — remaining HP percentage average.

Only when both teams have the **same number of surviving heroes** should remaining HP percentage average be compared. Average is calculated via adding all remaining hero hp percentage and then devided by the number of remaining heroses.

```text
Maximum round reached
        ↓
Compare surviving hero count
        ↓
Different? → More surviving heroes wins
        ↓
Equal
        ↓
Compare remaining HP percentage average
```


Exact Tie → Draw

An edge case was discussed where both teams have:

- the same surviving hero count; and
- the same remaining HP percentage average.

Example:

- Team A: 1 survivor at 50% HP
- Team B: 1 survivor at 50% HP

Decision

> **The battle result should be Draw.**



PvP Draw Behaviour

For PvP, Draw is a natural and acceptable result.

If both players finish with equal surviving hero count and equal remaining HP percentage, neither has demonstrated superiority according to the defined objectives. The match should therefore be recorded as a Draw rather than arbitrarily awarding victory.

PvE Draw Behaviour — Battle Result vs Stage Result

PvE requires a distinction between **battle outcome** and **stage progression**.

Decision

A PvE Draw does **not** clear the stage.

```text
Battle Result: DRAW
Stage Result:  NOT CLEARED
```

The player must replay the encounter to progress.

This does not require the battle itself to be labelled a Loss. The player genuinely achieved a Draw, but did not satisfy the requirement to defeat the stage encounter.

This distinction may also provide useful feedback: a Draw can communicate that the player is close to clearing the encounter.

Future reward design could potentially distinguish Draw from Loss, but no consolation reward was finalized.



## 2. Different Maximum Rounds for 1v1, 2v2, and 3v3

The current system uses approximately 15 rounds as a general maximum, but 1v1, 2v2, and 3v3 have substantially different:

- combatant counts;
- action density;
- interaction complexity;
- healing capacity;
- combination opportunities;
- expected battle duration.

The discussion therefore supports making maximum rounds configurable by battle size.

Initial illustrative values were:

```text
1v1 → approximately 9 rounds
2v2 → approximately 13 rounds
3v3 → approximately 15 rounds
```

Conceptually:

- **1v1** should feel shorter and more duel-like.
- **2v2** introduces stronger hero-combination and Interlock play.
- **3v3** is the fullest tactical expression and may require more time for formation, combinations, and evolving battle states.

# Date

2026-09-12

### Screenshot name

N/A

### Task List

Implement the first pre-alpha sound-effect system for Legends of Champions Tactics using the already-installed jsfxr 1.4.1.

Goal

Create a centralized frontend audio system using jsfxr for procedural game sound effects.

Initial sound categories:

* UI click
* UI hover
* Menu/game events
* Skill attack
* Damage/hit
* Evade
* Buff
* Debuff
* Defeated

Architecture

Create a centralized AudioManager or equivalent audio service.

Game/UI components should NOT call jsfxr directly.

They should use a simple interface such as:

audio.play("ui.click");
audio.play("ui.hover");
audio.play("battle.skill");
audio.play("battle.damage");
audio.play("battle.evade");
audio.play("battle.buff");
audio.play("battle.debuff");
audio.play("battle.defeated");

Keep all jsfxr presets/parameters in a separate sound-definition/config file so sounds can be tuned without modifying gameplay components.

Design the architecture so individual sounds can later be changed from:

type: "jsfxr"

to:

type: "file"

for WAV/OGG production assets without changing the components that trigger them.

Initial sound design

Create clearly distinguishable temporary pre-alpha sounds:

UI Click
Short, clean, subtle mechanical click.

UI Hover
Very short and quiet high-frequency tick. Less prominent than click.

Menu/Game Event
Clear notification/chime suitable for events such as turn changes or confirmations.

Skill Attack
Stronger, energetic attack sound. Use layering or multiple jsfxr sounds if useful.

Damage
Short, punchy impact/hit sound.

Evade
Fast upward/air-like movement sound suggesting an attack narrowly missing.

Buff
Positive rising magical tone.

Debuff
Darker descending/distorted tone.

Defeated
Heavier descending impact/failure sound with a slightly longer decay.

These are pre-alpha placeholders. Prioritize clear gameplay feedback over realistic/cinematic quality.

Integration

Connect the sounds only where matching events already clearly exist in the current frontend/game flow.

Do not change battle mechanics or backend logic just to support audio.

Avoid excessive hover audio: prevent overlapping/retrigger spam where necessary.

Browser autoplay restrictions must be handled safely. Audio should begin only after normal user interaction.

Extensibility

Prepare the system so we can later add IDs such as:

audio.play("warrior.fatalStrike");
audio.play("mage.fireball");
audio.play("rogue.backstab");

and potentially layer multiple procedural sounds for one skill.

Also leave the architecture ready for background music using normal OGG/WAV audio files later. Do NOT implement background music in this task.

Verification

After implementation:

1. Run existing frontend tests.
2. Run lint/typecheck.
3. Run production build.
4. Confirm no existing functionality is broken.
5. Report:
    * files created/modified
    * sound IDs implemented
    * where each sound is currently triggered
    * any jsfxr/TypeScript/browser issues encountered

Do not redesign unrelated code or UI.


# Date

2026-09-21

### Screenshot name

N/A

### Task List

Update the Hero Gallery implementation plan for Legends of Champions Tactics. The existing Manual button on the Stage Map is the entry point. Clicking it should open a compact Game Manual window with exactly three options, in this order:

1. Hero Gallery
2. Battle Instruction
3. Sound On/Off

Before implementation, read the relevant project rules, current task, Hero System, Skill System, combat documentation, web UI architecture, battle data contract, and style guide. Inspect the existing Manual button, navigation, roster, progression, assets, and audio system. Follow the project’s agent and documentation rules.

1_ Hero Gallery: Design and implement a Hero Gallery page for Legends of Champions Tactics.

Purpose: let players explore the 10 approved web hero specializations across Warrior, Mage, Paladin, Rogue, and Priest. This is an introduction and reference page, separate from Team Builder.

Build a responsive, accessible dark-fantasy gallery with:
- Faculty filters and illustrated cards for all 10 approved specializations.
- A selected-hero profile with large artwork, faculty and specialization, a brief introduction, a plain-language battle-style summary, basic properties (range of Hp, Damage, Defence, Agility, all different types of magic resistance), and expandable active-skill descriptions.
- A clearly separated passive skill section. For heroes so far not design passive skills, keep this section and maked N/A.
- Owned/Locked state from the active save slot’s authoritative backend data. Locked heroes must remain viewable. Show an unlock route only when one actually exists; do not imply that Priest Discipline currently has one.
- Navigation into and out of the Gallery that fits the existing startup, stage-map, and game flows.

Use stable definition IDs for identity and the existing asset fallback system. Keep introductions and skill copy in a maintainable presentation-content registry, with each claim checked against current hero and skill behavior. Hero starting stats are randomized: this is a special feature in the game, apply proper explanation on this feature. (Randomization represent a slightly fluctuating in hero situations similar to real life).

The Gallery explains general hero abilities. Do not reuse battle-specific preview numbers as permanent skill values or calculate damage, healing, hit chance, target legality, or status outcomes in React. Python remains the gameplay authority. Preserve existing battle, progression, save-slot, audio, keyboard, touch, and responsive behavior.

Start by proposing the route, page structure, content source, and any data gaps in a short implementation plan. Then implement the page, add focused tests for roster coverage, ownership states, navigation, and accessibility, update relevant documentation, and report the changes and validation results.

2_ Battle Instruction: Open a dedicated, readable guide covering battle basics, skill and target selection, turns, victory conditions, 2v2 and 3v3 formations, front/rear targeting, status effects, and a few clearly labelled practical strategy tips. Check every rules statement against the current engine and documentation. Explain mechanics in player-friendly language without exposing implementation details or claiming that a suggested strategy is an engine rule.

3_ Sound On/Off: This is a toggle inside the Manual window, not a separate page. Display its current state clearly. Connect it to the existing central audio system so it controls both UI and battle sound effects without bypassing browser audio restrictions. Persist the preference locally if the existing audio architecture supports it; do not treat it as save-slot or gameplay state.

The Manual window must match the Stage Map’s dark-fantasy style, support keyboard and touch input, manage focus correctly, close with Escape or its close button, and return focus to Manual. Provide clear navigation back to the Stage Map from both pages. Preserve existing map hotspots, battle behavior, progression, and audio event ordering.

Implement the changes, add focused tests for menu behavior, navigation, hero coverage and ownership, instruction accuracy where practical, sound toggle behavior, and accessibility. Update relevant documentation and report validation results and any remaining limitations.

### Date

2026-09-22

### Screenshot name

Hero_Gallery_Concept.png

### Task List

Current Hero Gallery UI is too dull and simple. An improvment work is essential. Design and implement the Hero Gallery page for Legends of Champions Tactics based as closely as practical on the approved concept UI/reference image Hero_Gallery_Concept.png.

IMPORTANT:
The attached/approved Hero Gallery concept is now the visual design target. Do not redesign the page from scratch. Reproduce its layout, hierarchy, proportions, dark-fantasy visual language, gold ornamentation, typography treatment, card structure, spacing, and overall presentation while integrating it correctly with the existing project architecture and authoritative game data.

Before making changes, read and follow:

- docs/Codex/Current_Task.md
- docs/Codex/Project_Rules.md
- docs/Technical/Architecture.md
- docs/GDD/Hero_System.md
- docs/GDD/Skill_System.md
- docs/web-ui/WEB_UI_ARCHITECTURE.md
- docs/web-ui/Style_Guide.md
- docs/web-ui/BATTLE_DATA_CONTRACT_V1.md
- any relevant image/asset creation rules

Also inspect:
- existing routes
- startup and stage-map navigation
- Manual/menu flow
- hero definitions
- approved hero artwork and avatar assets
- roster API
- active save-slot ownership flow
- existing asset fallback system
- responsive/layout conventions
- audio and input handling

Follow all existing agent, architecture, documentation, and testing rules.

==================================================
1. PURPOSE
==================================================

Hero Gallery is an introduction/reference page for the game's heroes.

It is NOT Team Builder.

Players should be able to browse the 10 approved web hero specializations across:

- Warrior
- Mage
- Paladin
- Rogue
- Priest

The Gallery should explain:
- who each hero is
- their faculty
- their specialization
- their general battle style
- their general properties
- their active skills
- their passive ability/abilities where applicable
- whether the hero is currently Owned or Locked

Locked heroes MUST remain fully viewable in the Gallery.

Do not imply an unlock method unless a real unlock route currently exists in authoritative project data.

In particular, do not invent an unlock route for Priest Discipline.

==================================================
2. APPROVED VISUAL DESIGN
==================================================

Reproduce the approved concept UI as closely as practical.

The page should use a cinematic dark-fantasy presentation with:
- deep navy/black panels
- restrained gold borders
- fine ornamental corner details
- warm gold headings
- ivory/off-white body text
- faculty-specific accent colours
- subtle glow for selected elements
- atmospheric fantasy landscape visible behind/around the interface
- high-quality hero artwork as the major visual focus

Do not make the UI look like a generic modern SaaS dashboard.

Avoid:
- bright flat cards
- excessive rounded corners
- oversized pills
- modern mobile-app styling
- excessive gradients
- unnecessary animation
- clutter

The design should feel like a polished fantasy strategy/RPG compendium.

==================================================
3. SITE HEADER
==================================================

The approved design intentionally removes the normal header CONTENT.

Item displayed in header:
- Back to Manual


Preserve the atmospheric/background treatment associated with the header/top region so the page still blends naturally with the existing game presentation.

Navigation into/out of Hero Gallery should fit the existing game flow.

Hero Gallery should be accessible through the Manual/menu flow already established for the Stage Map.

==================================================
4. DESKTOP PAGE STRUCTURE
==================================================

Follow the approved composition.

The main desktop layout is essentially two major regions:

LEFT:
Hero browsing/gallery.

RIGHT:
Selected hero profile.

The selected hero artwork should visually bridge the composition and remain a major focal point.

Do not convert this into a simple list/detail admin layout.

==================================================
5. LEFT — HERO GALLERY
==================================================

At the upper-left:

HERO GALLERY

Subtitle similar in purpose to:
"Meet the champions. Explore their abilities, playstyles, and find your favourites."

Below this place the faculty filters.

Filters:

- All
- Warrior
- Mage
- Paladin
- Rogue
- Priest

Use existing faculty iconography/assets where available.

Each faculty should retain its established visual identity/accent colour.

The selected filter should use a restrained gold highlighted state consistent with the concept.

==================================================
6. HERO CARD GRID
==================================================

Below the filters display cards for all 10 approved hero specializations.

Use stable hero definition IDs for identity.

Each card should contain:
- hero avatar/artwork
- faculty identity/icon
- specialization name
- Owned or Locked state

Use actual approved assets and the project's existing fallback system.

Do not create duplicate hero identity logic based on display names.

The selected hero card should have a clearly visible gold illuminated border/glow similar to the approved concept.

OWNED:
Use the restrained green treatment shown in the concept.

LOCKED:
Use subdued neutral styling and a lock indicator.

Locked cards remain clickable/selectable.

Selecting a locked hero must still display the complete Gallery profile.

Do not visually disable locked heroes as if they cannot be inspected.

==================================================
7. LEFT LOWER DECORATIVE AREA
==================================================

Preserve the concept's atmospheric lower-left area rather than filling every available space with controls.

A restrained fantasy quotation/decorative line may be used, similar in spirit to:

"Different paths. A greater purpose."

Treat this as presentation content, not gameplay data.

The landscape/background should remain visible around this area.

==================================================
8. SELECTED HERO ARTWORK
==================================================

Use the selected hero's approved large artwork as a major visual feature between the gallery and information panel.

Artwork should:
- remain high resolution
- preserve aspect ratio
- avoid unintended cropping of important head/helmet/weapon features where practical
- blend naturally into the dark profile panel
- use subtle lower-edge fading/gradient where needed
- not sit inside an obvious generic rectangular image box

Use existing hero assets/fallback logic.

Do not modify original image files unnecessarily.

==================================================
9. RIGHT — HERO PROFILE HEADER
==================================================

The selected hero profile should begin with:

FACULTY
SPECIALIZATION NAME

For example:

PALADIN
HOLY KNIGHT

Use faculty iconography beside the heading where appropriate.

Below it display a short thematic tagline if one exists in the presentation-content registry.

Then display:
- brief hero introduction
- Owned/Locked state

Keep these descriptions concise and readable.

Do not invent lore that contradicts project documentation.

==================================================
10. BATTLE STYLE
==================================================

Below the introduction create a dedicated BATTLE STYLE panel.

This is plain-language presentation content describing how the hero generally behaves in battle.

Example style:

"Durable and supportive frontline fighter. Holy Knights protect allies, disrupt enemies, and bring divine power to the battlefield through a blend of defence, healing, and righteous strikes."

IMPORTANT:
Do NOT introduce a formal gameplay "role" system unless such a system already exists authoritatively.

"Battle Style" is explanatory UI copy, not a new gameplay classification.

==================================================
11. PROPERTIES — USE AUTHORITATIVE HERO RANGES
==================================================

Replace the previous generic Properties section with the approved property presentation shown in the latest concept.

Section title:

PROPERTIES (Base Range)

Display the actual verified hero property ranges available from authoritative project data.

The approved visual structure is:

HP                  [range]
Damage              [range]

Defence             [range]
Agility             [range]

Then:

Magic Resistance Schools

Fire                [range]
Frost               [range]

Arcane              [range]
Shadow              [range]

Death               [range]
Poison              [range]

Nature              [range]

For the currently approved Holy Knight concept, the visual reference showed:

HP                  85–95
Damage              55–65
Defence             34–40
Agility             15–25

Magic Resistance Schools

Fire                34–40
Frost               34–40
Arcane              34–40
Shadow              40–50
Death               40–50
Poison              20–30
Nature              25–35

IMPORTANT:
These values must NOT simply be hardcoded because they appeared in the concept.

First verify the authoritative hero/property definitions.

Use authoritative values/ranges if they exist.

If the concept and authoritative data disagree, authoritative game data wins and document the discrepancy.

Hero starting stats are randomized, so present RANGE information rather than pretending every hero starts with one fixed stat value.

React must not reproduce Python gameplay calculations.

Prefer consuming authoritative definition/API data where appropriate.

If an exact property range cannot actually be verified, do not invent one.

==================================================
12. PROPERTY VISUAL DESIGN
==================================================

Integrate Properties professionally into the existing profile rather than creating a large spreadsheet.

Use:
- compact two-column layout where space permits
- thin separators
- ivory labels
- warm gold numeric ranges
- slightly stronger label treatment for "Magic Resistance Schools"
- consistent spacing
- no unnecessary icons for every property

The property section should be information-dense but elegant.

On narrower layouts it may collapse into one column.

==================================================
13. SKILLS AREA
==================================================

Below the hero information/profile area implement the skill section shown in the approved design.

Use tabs:

Active Skills (N)
Passive (N)

Counts must come from actual hero/skill definitions rather than being hardcoded globally.

Each active skill should appear as an expandable accordion row.

Each row should contain:
- skill icon if an approved asset exists
- skill name
- concise plain-language description
- expand/collapse indicator

Expanded content may provide a somewhat fuller explanation of what the skill generally does.

Do NOT show battle-preview numbers as permanent skill values.

Do NOT calculate in React:
- damage
- healing
- hit chance
- target legality
- status outcomes
- resistance resolution
- cooldown behavior
- combat formulas

Python remains gameplay authority.

The Gallery explains abilities; it does not simulate them.

==================================================
14. PASSIVES
==================================================

Passive abilities must be visually and structurally separated from active skills.

Use the Passive tab/panel from the approved design.

Where a hero has no passive, handle this cleanly rather than inventing one.

Do not convert passives into active skills for presentation convenience.

==================================================
15. PRESENTATION CONTENT REGISTRY
==================================================

Create/extend a maintainable presentation-content registry for Gallery-specific explanatory text.

Appropriate content includes:
- short introduction
- tagline
- Battle Style summary
- concise skill explanation where authoritative raw definitions are not presentation-friendly

Keep this separate from gameplay logic.

Every gameplay-related claim in presentation copy must be checked against current hero/skill behavior.

Do not duplicate authoritative mechanical values into presentation copy unnecessarily.

==================================================
16. DATA AUTHORITY
==================================================

Respect current ownership boundaries.

Use authoritative backend/save-slot data for:
- Owned
- Locked

Do not infer ownership from frontend state when authoritative save-slot data exists.

Do not invent:
- mana
- rarity
- hero levels
- equipment
- formal role classifications
- cooldown rules
- unlock requirements
- progression rules

Do not create parallel hero definitions in React.

Stable definition IDs remain the identity source.

==================================================
17. NAVIGATION
==================================================

Integrate Hero Gallery with the existing navigation flow.

The Stage Map Manual button/menu should include:

1. Hero Gallery
2. Battle Instruction
3. Sound On/Off

Hero Gallery opens this page.

Provide an appropriate way to return to the previous game context without restoring the removed full site header.

Reuse existing navigation conventions where possible.

Do not break:
- startup flow
- stage-map flow
- Team Builder
- battle navigation
- save-slot flow

==================================================
18. RESPONSIVE DESIGN
==================================================

The approved image represents the desktop composition.

Preserve its visual hierarchy at smaller sizes rather than simply shrinking everything.

Desktop:
- gallery on left
- major hero artwork/profile composition on right
- skills below profile content

Tablet:
- filters remain easy to use
- hero grid adapts
- profile/artwork may reorganize vertically
- Properties can collapse intelligently

Mobile:
Suggested flow:

Hero Gallery title
→ faculty filters
→ hero cards
→ selected hero artwork
→ hero identity/introduction
→ Battle Style
→ Properties
→ Active/Passive tabs
→ skill accordions

Do not allow horizontal page overflow.

Touch targets must remain usable.

==================================================
19. ACCESSIBILITY
==================================================

Implement proper accessibility rather than relying on visuals alone.

Include:
- semantic buttons
- keyboard-accessible faculty filters
- keyboard-accessible hero selection
- visible focus states
- appropriate aria state for selected filters/cards
- accessible accordion controls
- aria-expanded
- usable Active/Passive tab semantics
- meaningful image alt text
- ownership state represented in text, not colour alone
- sufficient contrast

Preserve existing keyboard behavior.

==================================================
20. AUDIO
==================================================

Use existing UI audio infrastructure if applicable.

Do not create another audio system.

Gallery interactions such as:
- faculty selection
- hero selection
- accordion expansion
- tab switching

may use the existing UI click behavior where consistent with the rest of the game.

Respect Sound On/Off.

==================================================
21. TESTS
==================================================

Add focused tests covering at minimum:

- all 10 approved hero specializations appear
- faculty filtering
- stable definition IDs
- selected hero changes correctly
- Owned state
- Locked state
- locked hero remains viewable/selectable
- authoritative ownership data is used
- no fake Priest Discipline unlock route appears
- property ranges render correctly from authoritative data
- Magic Resistance Schools render correctly
- Active/Passive tab behavior
- skill accordion behavior
- navigation into Gallery
- navigation out of Gallery
- keyboard interaction
- important accessibility semantics
- responsive behavior where existing test infrastructure supports it
- asset fallback behavior if appropriate

Do not rewrite unrelated tests.

==================================================
22. DOCUMENTATION
==================================================

Update relevant documentation according to Project_Rules.md.

Document:
- Hero Gallery route
- navigation entry point
- page responsibility
- presentation-content registry
- ownership source
- property range source
- asset usage/fallback
- any new components
- tests/validation
- known limitations/data gaps

Update Current_Task/Completed or other project tracking documents only according to the project's established documentation workflow.

==================================================
23. IMPLEMENTATION PROCESS
==================================================

Do not immediately start coding.

First inspect the required documentation and current implementation.

Then provide a SHORT implementation plan containing:

1. proposed route
2. component/page structure
3. authoritative data sources
4. presentation-content source
5. ownership source
6. property-range source
7. asset source/fallback
8. navigation integration
9. identified data gaps or conflicts with the approved concept

Then implement.

Do not stop after producing the plan unless a genuine blocker requires clarification.

==================================================
24. VALIDATION
==================================================

After implementation run the relevant:

- frontend tests
- targeted Hero Gallery tests
- type checking
- linting
- build
- backend tests if backend/API behavior was touched

Also manually verify the page at representative desktop/tablet/mobile viewport sizes if the project's tooling supports this.

Check specifically for:
- clipping
- overlapping text
- hero artwork cropping
- property layout
- long specialization names
- skill descriptions
- locked state readability
- keyboard navigation
- horizontal overflow

==================================================
25. FINAL REPORT
==================================================

At completion report concisely:

- files changed
- route implemented
- major components added/changed
- data sources used
- how ownership works
- how property ranges are sourced
- presentation registry location
- navigation changes
- tests added
- validation commands/results
- documentation updated
- remaining limitations/data gaps

Do not claim validation that was not actually run.

==================================================
DESIGN PRIORITY
==================================================

The approved Hero Gallery concept is the visual target.

Preserve its major composition:

LEFT
- HERO GALLERY heading
- faculty filters
- 10 hero cards
- selected gold-highlighted card
- Owned/Locked indicators
- atmospheric lower area

CENTER/RIGHT
- large selected hero artwork
- faculty + specialization
- Owned/Locked indicator
- introduction
- BATTLE STYLE
- PROPERTIES (Base Range)
- Magic Resistance Schools
- Active Skills / Passive tabs
- expandable skill rows

The implementation should look recognizably like the approved concept rather than merely containing the same information.

At the same time, project architecture and authoritative gameplay data take precedence over visual mockup assumptions.