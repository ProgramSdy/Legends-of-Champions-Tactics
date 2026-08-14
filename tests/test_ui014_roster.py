from __future__ import annotations

from battle_api.adapter import BattleAdapter, HERO_ROSTER
from battle_api.app import app
from battle_api.models import CreateBattleRequest
from fastapi.testclient import TestClient


client = TestClient(app)
NEW_HEROES = ("hero.warrior.berserker", "hero.paladin.holy")


def test_roster_endpoint_publishes_ten_typed_definitions_and_new_metadata():
    response = client.get("/api/v1/heroes")
    assert response.status_code == 200
    heroes = response.json()["heroes"]
    assert len(heroes) == 10
    by_id = {hero["definitionId"]: hero for hero in heroes}
    for definition_id in NEW_HEROES:
        assert by_id[definition_id]["displayName"]
        assert by_id[definition_id]["faculty"]
        assert by_id[definition_id]["specialization"]


def test_new_definition_ids_are_accepted_by_the_v1_create_model():
    request = CreateBattleRequest(
        battleSize=2,
        playerTeam=[NEW_HEROES[0], NEW_HEROES[1]],
        enemyCompositionMode="specified",
        enemyTeam=[NEW_HEROES[1], NEW_HEROES[0]],
        enemyControlMode="player",
        playerFormation="front-rear",
        enemyFormation="side-by-side",
        seed=19,
    )
    assert request.player_team == list(NEW_HEROES)
    assert request.enemy_team == [NEW_HEROES[1], NEW_HEROES[0]]


def test_each_new_hero_constructs_with_stable_ids_skills_and_a_live_action():
    adapter = BattleAdapter()
    for index, definition_id in enumerate(NEW_HEROES):
        session, envelope = adapter.create_battle(
            seed=100 + index,
            battle_id=f"battle.ui014.{index}",
            player_team=[definition_id],
            enemy_team=["hero.rogue.comprehensiveness"],
        )
        snapshot = envelope["data"]["snapshot"]
        friendly_id = snapshot["sides"][0]["combatantIds"][0]
        combatant = snapshot["combatants"][friendly_id]
        assert combatant["definitionId"] == definition_id
        assert len(combatant["skills"]) == 3
        action = snapshot["legalActions"][0]
        result = adapter.submit(
            session,
            {
                "type": "useSkill",
                "commandId": f"cmd.ui014.{index}",
                "expectedRevision": session.revision,
                "actorId": action["actorId"],
                "skillId": action["skillId"],
                "targetIds": action["validTargetIds"][: action["minimumTargets"]],
            },
        )
        assert result["accepted"] is True


def test_equal_seeded_random_configuration_is_deterministic_with_expanded_roster():
    kwargs = {
        "seed": 77,
        "battle_size": 3,
        "player_team": ["hero.warrior.berserker", "hero.paladin.holy", "hero.mage.comprehensiveness"],
        "enemy_composition_mode": "random",
        "enemy_control_mode": "player",
    }
    first = BattleAdapter().create_battle(battle_id="battle.ui014.random.a", **kwargs)[1]
    second = BattleAdapter().create_battle(battle_id="battle.ui014.random.b", **kwargs)[1]

    def definitions(envelope):
        snapshot = envelope["data"]["snapshot"]
        return [snapshot["combatants"][combatant_id]["definitionId"] for combatant_id in snapshot["sides"][1]["combatantIds"]]

    assert definitions(first) == definitions(second)
    assert len(definitions(first)) == 3
    assert set(HERO_ROSTER) >= set(definitions(first))
