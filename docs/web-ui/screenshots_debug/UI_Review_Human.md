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