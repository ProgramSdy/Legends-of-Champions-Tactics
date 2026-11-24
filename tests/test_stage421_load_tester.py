from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
import uuid

import pytest

from tests.tools import public_battle_load as load
from battle_api.progression import ProgressionStore, STAGE_BATTLES, INITIAL_UNLOCKED_HERO_IDS
from battle_api.public_identity import PublicIdentityService


def _args(**overrides):
    values = dict(
        base_url="http://127.0.0.1:8000",
        allow_production=False,
        owner_authorization="",
        allow_insecure_local_tls=False,
        execute=True,
        players=2,
        timeout_seconds=1,
        duration_seconds=5,
        max_rps=2,
        max_requests=10,
        max_error_rate=.2,
        max_commands_per_battle=10,
        max_stage_attempts=1,
    )
    values.update(overrides)
    return argparse.Namespace(**values)


def test_validate_target_rejects_credentials_paths_and_non_https_production():
    with pytest.raises(ValueError, match="bare HTTP"):
        load.validate_target(_args(base_url="http://user:pass@127.0.0.1:8000"))
    with pytest.raises(ValueError, match="bare HTTP"):
        load.validate_target(_args(base_url="http://127.0.0.1:8000/api"))
    with pytest.raises(ValueError, match="HTTPS"):
        load.validate_target(_args(base_url="http://example.invalid"))


def test_validate_target_requires_both_production_opt_ins():
    target = _args(base_url="https://example.invalid", allow_production=True)
    with pytest.raises(ValueError, match="Owner authorization"):
        load.validate_target(target)
    target.owner_authorization = load.PRODUCTION_CONFIRMATION
    origin, local = load.validate_target(target)
    assert origin == "https://example.invalid"
    assert local is False


def test_dry_run_is_zero_request_and_reports_limits(capsys):
    assert load.main(["--base-url", "http://127.0.0.1:8000", "--players", "2"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "DRY_RUN_ZERO_REQUESTS"
    assert report["players"] == 2
    assert report["max_requests"] == 500
    assert report["scenario"] == {
        "stageId": "warriors-barrack", "battleIndex": 1, "battleSize": 2,
        "playerTeam": list(load.TEAM), "playerFormation": "front-rear",
    }


def test_authoritative_stage_and_roster_allow_repeating_stage_one(tmp_path: Path):
    definition = STAGE_BATTLES["warriors-barrack"][0]
    assert (definition.battle_index, definition.battle_size, definition.formation) == (1, 2, "front-rear")
    assert set(load.TEAM).issubset(INITIAL_UNLOCKED_HERO_IDS)
    store = ProgressionStore(tmp_path / "disposable-stage.sqlite3")
    store.create_save_slot(1)
    assert store.assert_stage_battle_access(load.STAGE_ID, load.STAGE_INDEX).battle_size == 2
    store.commit_victory(battle_id="local-first-stage-one", stage_id=load.STAGE_ID,
                         battle_index=load.STAGE_INDEX)
    assert store.assert_stage_battle_access(load.STAGE_ID, load.STAGE_INDEX).battle_size == 2


def test_main_refuses_overwriting_existing_csv(tmp_path: Path):
    csv_path = tmp_path / "existing.csv"
    csv_path.write_text("sentinel\n")
    with pytest.raises(SystemExit, match="already exists"):
        load.main(["--base-url", "http://127.0.0.1:8000", "--csv", str(csv_path)])
    assert csv_path.read_text() == "sentinel\n"


def test_parser_exposes_ca_file_and_not_custom_player_names():
    args = load.parser().parse_args(["--ca-file", "/tmp/ca.pem"])
    assert args.ca_file == Path("/tmp/ca.pem")
    with pytest.raises(SystemExit):
        load.parser().parse_args(["--identity-prefix", "Iso"])


def test_parser_supports_concurrency_alias():
    args = load.parser().parse_args(["--concurrency", "3"])
    assert args.players == 3
    assert args.init_max_rps == 0.1
    assert (args.init_general_rps, args.init_duration_seconds, args.init_max_requests) == (2, 600, 200)
    assert args.max_active_battles == 20


def test_classification_separates_rate_capacity_rule_and_api_errors():
    assert load.classify(200, {}) == "ok"
    assert load.classify(429, {}) == "rate_limit"
    assert load.classify(409, {"detail": {"code": "battleCapacityReached"}}) == "capacity"
    assert load.classify(409, {"detail": {"code": "illegalTargets"}}) == "battle_rule"
    assert load.classify(500, {"detail": {"code": "unexpected"}}) == "api_error"
    assert load.classify(302, {"location": "https://other.example"}) == "redirect"


@pytest.mark.parametrize("code", ["illegalTargets", "illegalSkill", "invalidCommand", "battleEnded"])
def test_published_battle_rule_codes_are_not_counted_as_generic_api_errors(code):
    assert load.classify(409, {"detail": {"code": code}}) == "battle_rule"


def test_redirect_is_a_terminal_budget_category():
    budget = load.RunBudget(_args(max_requests=5))
    budget.before_request()
    budget.record(load.RequestResult(0, "probe", 1, 302, "redirect"))
    assert budget.stop.is_set()


def test_accepted_false_command_is_a_battle_rule_without_network(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, _limit):
            return b'{"accepted": false, "reason": "invalidTarget"}'

    class Opener:
        def open(self, *_args, **_kwargs):
            return Response()

    args = _args(ca_file=None)
    budget = load.RunBudget(args)
    client = load.PlayerClient(0, "https://127.0.0.1:8443", args, budget)
    client.opener = Opener()
    with pytest.raises(load.ApiFailure) as failure:
        client.request("POST", "/api/v1/battles/b/commands", {}, label="battle_command")
    assert failure.value.category == "battle_rule"
    assert budget.rows[-1].category == "battle_rule"


def test_only_expected_prior_battle_409_counts_as_operation_ok():
    class Response:
        status = 409

        def __init__(self, code):
            self.code = code

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, _limit):
            return json.dumps({"detail": {"code": self.code}}).encode()

    class Opener:
        code = "battleNoLongerActive"

        def open(self, *_args, **_kwargs):
            return Response(self.code)

    args = _args(ca_file=None, max_requests=5)
    budget = load.RunBudget(args)
    client = load.PlayerClient(0, "https://127.0.0.1:8443", args, budget)
    client.opener = opener = Opener()
    client.request("GET", "/api/v1/battles/old", label="prior_battle_state",
                   expected_statuses=frozenset({409}))
    opener.code = "unexpectedConflict"
    with pytest.raises(load.ApiFailure) as failure:
        client.request("GET", "/api/v1/battles/old", label="prior_battle_state",
                       expected_statuses=frozenset({409}))
    assert failure.value.category == "api_error"
    report = load.summary(budget.rows, [], 1)
    assert report["requests"] == 2
    assert report["successful_requests"] == 0
    assert report["operation_ok_requests"] == report["expected_non_2xx_ok"] == 1
    assert report["error_rate"] == .5


@pytest.mark.parametrize("body", [b"<html>rate limit</html>", b"Too Many Requests", b""])
def test_non_json_429_is_rate_limit_and_stops_immediately(body: bytes):
    class Response:
        status = 429

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self, _limit):
            return body

    class Opener:
        def open(self, *_args, **_kwargs):
            return Response()

    args = _args(ca_file=None, max_requests=10)
    budget = load.RunBudget(args)
    client = load.PlayerClient(0, "https://127.0.0.1:8443", args, budget)
    client.opener = Opener()
    with pytest.raises(load.ApiFailure) as failure:
        client.request("POST", "/api/v1/sessions/recover", {"recoveryCode": "LOCAL-ONLY"},
                       label="player_recover")
    assert failure.value.category == "rate_limit"
    assert budget.stop.is_set()
    assert len(budget.rows) == 1
    report = load.summary(budget.rows, [], 1, budget)
    assert report["requests"] == report["http_429"] == report["counts"]["rate_limit"] == 1
    assert report["counts"]["tool_error"] == 0
    assert report["non_json_responses"] == (0 if not body else 1)
    with pytest.raises(load.StopRun):
        client.request("POST", "/api/v1/sessions/recover", {}, label="player_recover")
    assert len(budget.rows) == 1


def test_initialization_has_separate_shared_rate_cap():
    args = _args(mode="reuse", max_rps=100, init_max_rps=10, max_requests=10,
                 duration_seconds=10, drain_seconds=1)
    budget = load.RunBudget(args)
    times = []
    for worker in range(3):
        assert budget.before_request("initialization") == "initialization"
        times.append(time.monotonic())
        budget.record(load.RequestResult(worker, "player_recover", 1, 200, "ok", "initialization"))
    assert times[1] - times[0] >= .08
    assert times[2] - times[1] >= .08
    assert len(budget.rows) == 3


def test_separate_initialization_clock_starts_battle_window_at_barrier():
    args = _args(mode="reuse", duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=600, init_max_requests=10,
                 init_max_rps=100, init_general_rps=100, max_rps=100,
                 max_requests=10)
    budget = load.RunBudget(args)
    budget.started = time.monotonic() - 400
    assert budget.before_request("initialization", "/api/v1/sessions/recover") == "initialization"
    budget.record(load.RequestResult(0, "player_recover", 1, 200, "ok", "initialization"))
    assert not budget.begin_battle(0)
    budget.initialization_complete()
    assert budget.begin_battle(0)
    assert budget.before_request("normal", "/api/v1/stages") == "normal"
    budget.record(load.RequestResult(0, "stage_state", 2, 200, "ok", "normal"))
    report = load.summary(budget.rows, [], time.monotonic() - budget.started, budget)
    assert report["initialization_seconds"] >= 400
    assert report["battle_phase_seconds"] < 1
    assert report["initialization_requests"] == report["battle_phase_requests"] == 1
    assert report["battle_average_ms"] == report["battle_p95_ms"] == 2
    budget.leave_battle(0, interrupted=False)


def test_initialization_and_battle_request_caps_are_independent():
    args = _args(mode="reuse", duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=600, init_max_requests=2,
                 init_max_rps=100, init_general_rps=100, max_rps=100,
                 max_requests=1)
    budget = load.RunBudget(args)
    for index in range(2):
        phase = budget.before_request("initialization", "/api/v1/save-slots")
        budget.record(load.RequestResult(0, "slot_state", 1, 200, "ok", phase))
    budget.initialization_complete()
    phase = budget.before_request("normal", "/api/v1/stages")
    budget.record(load.RequestResult(0, "stage_state", 1, 200, "ok", phase))
    with pytest.raises(load.StopRun, match="request budget"):
        budget.before_request("normal", "/api/v1/stages")
    assert len(budget.rows) == 3 and budget.battle_started_at is not None


def test_sensitive_and_general_initialization_have_distinct_shared_pacing():
    args = _args(mode="reuse", duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=600, init_max_requests=10,
                 init_max_rps=20, init_general_rps=100, max_rps=100,
                 max_requests=10)
    budget = load.RunBudget(args)
    sensitive_times = []
    for path, label in (("/api/v1/sessions/recover", "player_recover"),
                        ("/api/v1/save-slots", "slot_state"),
                        ("/api/v1/sessions/recover", "player_recover")):
        phase = budget.before_request("initialization", path)
        if label == "player_recover":
            sensitive_times.append(time.monotonic())
        budget.record(load.RequestResult(0, label, 1, 200, "ok", phase))
    assert sensitive_times[1] - sensitive_times[0] >= .04
    assert budget.next_general_initialization_request < budget.next_initialization_request


def test_production_sensitive_cap_does_not_delay_general_preflight_ten_seconds():
    args = _args(mode="reuse", duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=600, init_max_requests=10,
                 init_max_rps=.1, init_general_rps=2, max_rps=3,
                 max_requests=10)
    budget = load.RunBudget(args)
    phase = budget.before_request("initialization", "/api/v1/sessions/recover")
    budget.record(load.RequestResult(0, "player_recover", 1, 200, "ok", phase))
    phase = budget.before_request("initialization", "/api/v1/save-slots")
    budget.record(load.RequestResult(0, "slot_state", 1, 200, "ok", phase))
    assert budget.next_initialization_request - budget.started >= 9.9
    assert budget.next_general_initialization_request - budget.started < 2
    assert len(budget.rows) == 2 and not budget.stop.is_set()


def test_preinitialization_timeout_never_starts_battle_clock():
    args = _args(mode="reuse", duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=1, init_max_requests=10,
                 init_max_rps=100, init_general_rps=100, max_rps=100)
    budget = load.RunBudget(args)
    budget.started = time.monotonic() - 2
    with pytest.raises(load.StopRun, match="Phase duration"):
        budget.before_request("initialization", "/api/v1/sessions/recover")
    assert budget.stop.is_set() and budget.battle_started_at is None
    assert budget.rows == [] and budget.battle_attempts == 0


def test_reuse_stops_immediately_on_one_unexpected_api_error():
    args = _args(mode="reuse", duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=600, init_max_requests=10,
                 init_max_rps=100, init_general_rps=100, max_rps=100,
                 max_requests=10, max_error_rate=.9)
    budget = load.RunBudget(args)
    phase = budget.before_request("initialization", "/api/v1/progression")
    budget.record(load.RequestResult(0, "roster_state", 1, 500, "api_error", phase))
    assert budget.stop.is_set()
    with pytest.raises(load.StopRun):
        budget.before_request("initialization", "/api/v1/progression")


def test_preinitialization_timeout_before_request_preserves_ready_account(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    args = _args(mode="reuse", duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=1, init_max_requests=10,
                 init_max_rps=100, init_general_rps=100, max_rps=100)
    budget = load.RunBudget(args)
    budget.started = time.monotonic() - 2
    account = _stored_account()

    class Client:
        sent_requests = 0

        def __init__(self, *_):
            pass

        def request(self, *_args, **_kwargs):
            budget.before_request("initialization", "/api/v1/sessions/recover")
            pytest.fail("Expired initialization must not send a request")

    monkeypatch.setattr(load, "PlayerClient", Client)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(account)
        outcome = load.run_player(0, "https://127.0.0.1:8443", args, budget, pool, account)
        assert outcome["reason"] == "StopRun"
        assert account["state"] == "ready"
        assert account["recoveryCode"] == "ABCD-EFGH-IJKL-MNOP"
    assert budget.rows == [] and budget.battle_attempts == 0


def test_thirty_player_workers_never_exceed_twenty_active_battle_slots():
    args = _args(mode="reuse", players=30, max_active_battles=20,
                 duration_seconds=300, drain_seconds=60,
                 init_duration_seconds=600, init_max_requests=200)
    budget = load.RunBudget(args)
    budget.initialization_complete()
    active = 0
    peak = 0
    guard = load.threading.Lock()

    def worker(_number):
        nonlocal active, peak
        assert budget.acquire_battle_slot()
        try:
            with guard:
                active += 1
                peak = max(peak, active)
            time.sleep(.01)
            with guard:
                active -= 1
        finally:
            budget.battle_slots.release()

    with ThreadPoolExecutor(max_workers=30) as executor:
        list(executor.map(worker, range(30)))
    assert peak <= 20 and active == 0


def test_thirty_active_battle_slots_are_allowed_and_peak_is_recorded():
    args = _args(mode="reuse", players=30, max_active_battles=30,
                 max_requests=600, duration_seconds=300, drain_seconds=60,
                 drain_requests_per_battle=12, init_duration_seconds=600,
                 init_max_requests=200)
    budget = load.RunBudget(args)
    budget.initialization_complete()
    for worker in range(30):
        assert budget.acquire_battle_slot()
        assert budget.begin_battle(worker)
    assert budget.peak_active_battles == 30
    for worker in range(30):
        budget.leave_battle(worker, interrupted=False)
        budget.battle_slots.release()


def test_client_active_battle_limit_above_thirty_is_rejected():
    with pytest.raises(SystemExit, match="Invalid limits"):
        load.main(["--max-active-battles", "31"])


def test_waiting_battle_worker_does_not_launch_after_drain_cutoff():
    args = _args(mode="reuse", players=2, max_active_battles=1,
                 duration_seconds=10, drain_seconds=2,
                 init_duration_seconds=30, init_max_requests=10)
    budget = load.RunBudget(args)
    budget.initialization_complete()
    assert budget.acquire_battle_slot()
    budget.battle_started_at = time.monotonic() - 9
    try:
        assert not budget.acquire_battle_slot()
        assert budget.battle_attempts == 0
    finally:
        budget.battle_slots.release()


def test_action_for_uses_legal_distinct_minimum_targets():
    snapshot = {
        "phase": "active",
        "combatants": {"e1": {"sideId": "enemy"}, "e2": {"sideId": "enemy"}},
        "legalActions": [
            {
                "actorId": "p1", "skillId": "skill.arcane_missiles",
                "minimumTargets": 2, "validTargetIds": ["e1", "e1", "e2"],
            }
        ],
    }
    assert load.action_for(snapshot)["targetIds"] == ["e1", "e2"]


def test_summary_metrics_and_csv_are_credential_free(tmp_path: Path):
    rows = [
        load.RequestResult(0, "player_create", 10, 200, "ok"),
        load.RequestResult(0, "battle_command", 20, 429, "rate_limit"),
        load.RequestResult(1, "battle_state", 30, 409, "battle_rule"),
    ]
    outcomes = [{"worker": 0, "battles_settled": 0}]
    report = load.summary(rows, outcomes, 1.0)
    assert report["requests"] == 3
    assert report["successful_requests"] == 1
    assert report["http_429"] == 1
    assert report["completed_battles"] == 0
    assert report["average_ms"] == 20
    assert report["p95_ms"] == 30
    assert report["counts"]["rate_limit"] == 1
    csv_path = tmp_path / "metrics.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("worker", "endpoint", "latency_ms", "http_status", "category"))
        writer.writerows((row.worker, row.endpoint, row.latency_ms, row.status, row.category) for row in rows)
    content = csv_path.read_text()
    assert "recovery" not in content.lower()
    assert "cookie" not in content.lower()
    assert "csrf" not in content.lower()


def test_run_budget_stops_at_global_request_bound():
    args = _args(max_requests=1)
    budget = load.RunBudget(args)
    budget.before_request()
    budget.record(load.RequestResult(0, "probe", 1, 200, "ok"))
    with pytest.raises(load.StopRun):
        budget.before_request()


def test_normal_cutoff_prevents_new_battle_but_allows_draining_requests():
    args = _args(duration_seconds=100, max_requests=36, drain_seconds=20,
                 drain_requests_per_battle=12)
    budget = load.RunBudget(args)
    assert budget.begin_battle(0)
    assert budget.begin_battle(1)
    assert budget.begin_battle(2)
    assert not budget.begin_battle(3)
    assert budget.drain_reason == "request_reserve"
    assert not budget.stop.is_set()
    assert budget.before_request() == "drain"
    budget.record(load.RequestResult(0, "battle_command", 1, 200, "ok", "drain"))
    for worker in range(3):
        budget.leave_battle(worker, interrupted=False)
    assert not budget.active_battles


def test_multiple_workers_respect_one_normal_launch_cutoff():
    args = _args(duration_seconds=100, max_requests=24, drain_seconds=20,
                 drain_requests_per_battle=12)
    budget = load.RunBudget(args)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(budget.begin_battle, range(10)))
    assert sum(results) == 2
    assert budget.drain_reason == "request_reserve"
    assert len(budget.active_battles) == 2
    assert not budget.stop.is_set()
    for worker, started in enumerate(results):
        if started:
            budget.leave_battle(worker, interrupted=False)


def test_time_reserve_starts_drain_without_exceeding_total_duration():
    args = _args(mode="reuse", duration_seconds=100, max_requests=100, drain_seconds=20,
                 drain_requests_per_battle=12)
    budget = load.RunBudget(args)
    assert budget.begin_battle(0)
    budget.started = time.monotonic() - 85
    assert budget.before_request() == "drain"
    budget.record(load.RequestResult(0, "battle_command", 1, 200, "ok", "drain"))
    assert not budget.begin_battle(1)
    budget.started = time.monotonic() - 101
    with pytest.raises(load.StopRun):
        budget.before_request()
    assert budget.stop.is_set()


def test_metrics_separate_http_success_from_accepted_operations_and_drain():
    rows = [
        load.RequestResult(0, "battle_state", 1, 409, "ok"),
        load.RequestResult(0, "battle_command", 1, 200, "battle_rule"),
        load.RequestResult(0, "battle_state", 1, 200, "ok", "drain"),
        load.RequestResult(0, "battle_state", 1, 500, "api_error", "drain"),
        load.RequestResult(0, "battle_state", 1, 0, "timeout", "drain"),
    ]
    report = load.summary(rows, [], 1.0)
    assert report["requests"] == sum(report["counts"].values()) == 5
    assert report["operation_ok_requests"] == report["counts"]["ok"] == 2
    assert report["successful_requests"] == report["http_successful_requests"] == 2
    assert report["expected_non_2xx_ok"] == 1
    assert report["http_2xx_operation_failures"] == 1
    assert report["http_responses"] == 4
    assert report["http_non_2xx_responses"] == 2
    assert report["no_http_response_requests"] == 1
    assert (report["successful_requests"] + report["http_non_2xx_responses"]
            + report["no_http_response_requests"]) == report["requests"]
    assert (report["normal_requests"], report["drain_requests"]) == (2, 3)
    assert report["error_rate"] == .6


def test_cutoff_after_stage_preflight_does_not_mark_or_launch_battle(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    args = _args(mode="reuse", duration_seconds=100, max_requests=100,
                 drain_seconds=20, drain_requests_per_battle=12)
    budget = load.RunBudget(args)
    account = _stored_account()

    class Client:
        worker = 0

        def __init__(self, *_):
            self.budget = budget

        def request(self, *_args, **_kwargs):
            pytest.fail("Battle launch must not be sent")

    monkeypatch.setattr(load, "stage_one_available", lambda _client:
                        setattr(budget, "started", time.monotonic() - 85) or True)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(account)
        assert load.fight(Client(), pool, account) is None
        assert account["state"] == "ready" and account["battleId"] is None
        assert account["recoveryCode"] == "ABCD-EFGH-IJKL-MNOP"
    assert budget.battle_attempts == 0
    assert budget.drain_reason == "time_reserve"


def test_thirty_worker_initialization_rate_limit_does_not_create_thirty_unfinished_battles(
    monkeypatch, tmp_path: Path, capsys,
):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        for number in range(1, 31):
            pool.append({"state": "ready", "playerName": f"Test_Player_{number:03d}",
                         "playerId": f"local-player-{number}", "profileId": f"local-profile-{number}",
                         "recoveryCode": f"PRIVATE-LOCAL-{number}", "battleId": None})

    class Client:
        def __init__(self, worker, _origin, _args, budget):
            self.worker = worker
            self.budget = budget
            self.sent_requests = 0

        def request(self, _method, endpoint, *_args, **_kwargs):
            assert endpoint == "/api/v1/sessions/recover"
            phase = self.budget.before_request("initialization")
            self.sent_requests += 1
            self.budget.record(load.RequestResult(self.worker, "player_recover", 1,
                                                  429, "rate_limit", phase, "non_json"))
            raise load.ApiFailure("rate_limit", 429)

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "fight", lambda *_args: pytest.fail("No battle may launch"))
    assert load.main(["--mode", "reuse", "--execute", "--base-url", "https://127.0.0.1:8443",
                      "--pool-file", str(path), "--concurrency", "30", "--init-concurrency", "1",
                      "--init-max-rps", "100", "--max-rps", "100", "--max-requests", "100",
                      "--duration-seconds", "10", "--drain-seconds", "1"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["accounts_attempted"] == 30
    assert report["workers_initialized"] == 0
    assert report["initialization_requests"] == report["requests"] == 1
    assert report["counts"]["rate_limit"] == report["http_429"] == 1
    assert report["battle_attempts"] == report["unfinished_battles"] == 0
    assert report["accounts_requiring_verification"] == 1
    assert report["actual_server_active_battles"] is None
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        assert [item["state"] for item in pool.data["accounts"]].count("requires_reconciliation") == 1
        assert [item["state"] for item in pool.data["accounts"]].count("ready") == 29
        assert all(item["recoveryCode"] == f"PRIVATE-LOCAL-{number}"
                   for number, item in enumerate(pool.data["accounts"], 1))


def test_reuse_battle_phase_waits_for_every_worker_to_initialize(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    args = _args(mode="reuse", players=3, duration_seconds=10, max_requests=50,
                 drain_seconds=1, init_concurrency=2, init_duration_seconds=30,
                 init_max_requests=20, init_max_rps=100, init_general_rps=100,
                 max_stage_attempts=1)
    budget = load.RunBudget(args)
    launched = []

    class Client:
        def __init__(self, worker, _origin, supplied_args, supplied_budget):
            self.worker = worker
            self.args = supplied_args
            self.budget = supplied_budget

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fixed_roster_available", lambda *_args: True)
    monkeypatch.setattr(load, "stage_one_available", lambda *_args: True)

    def finish(client, _pool, account):
        assert budget.initialized_workers == 3
        assert budget.initialization_completed_at is not None
        assert budget.battle_started_at == budget.initialization_completed_at
        assert client.traffic_phase == "normal"
        launched.append(account["playerId"])
        return "victory"

    monkeypatch.setattr(load, "fight", finish)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        accounts = []
        for number in range(3):
            account = {"state": "ready", "playerId": f"player-{number}",
                       "profileId": f"profile-{number}", "recoveryCode": f"LOCAL-{number}",
                       "battleId": None}
            pool.append(account)
            accounts.append(account)
        barrier = load.threading.Barrier(3, action=budget.initialization_complete)
        with ThreadPoolExecutor(max_workers=3) as executor:
            outcomes = list(executor.map(
                lambda pair: load.run_player(pair[0], "https://127.0.0.1:8443", args,
                                             budget, pool, pair[1], barrier),
                enumerate(accounts),
            ))
        assert all(item["battles_settled"] == 1 for item in outcomes)
        assert all(item["state"] == "ready" for item in accounts)
    assert len(launched) == 3


def test_lost_launch_response_keeps_prior_battle_id_and_attempt(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    args = _args(mode="reuse", duration_seconds=100, max_requests=20,
                 drain_seconds=20, drain_requests_per_battle=2)
    budget = load.RunBudget(args)
    account = {**_stored_account(), "battleId": "prior-settled-battle"}

    class Client:
        worker = 0

        def __init__(self):
            self.budget = budget
            self.args = args

        def request(self, _method, _endpoint, payload=None, **_kwargs):
            assert account["state"] == "uncertain_launch"
            assert account["battleId"] == "prior-settled-battle"
            assert payload["attemptId"] == account["pendingAttemptId"]
            raise load.ApiFailure("timeout")

    monkeypatch.setattr(load, "stage_one_available", lambda *_args: True)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(account)
        with pytest.raises(load.ApiFailure):
            load.fight(Client(), pool, account)
        assert account["state"] == "uncertain_launch"
        assert account["battleId"] == "prior-settled-battle"
        assert account["pendingAttemptId"].startswith("load-")
    assert budget.battle_attempts == 0
    assert budget.drain_reason == "interrupted_battle"


def test_explicit_uncertain_launch_reconciliation_retains_battle_audit(
    monkeypatch, tmp_path: Path,
):
    path = _private_pool(tmp_path)
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: object())
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fixed_roster_available", lambda *_args: True)
    monkeypatch.setattr(load, "stage_one_available", lambda *_args: True)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        account = {**_stored_account(), "state": "uncertain_launch",
                   "battleId": "prior-battle", "pendingAttemptId": "load-uncertain"}
        pool.append(account)
        assert load.reconcile_player(0, "https://127.0.0.1:8443", _args(mode="reconcile"),
                                     load.RunBudget(_args()), pool, account)
        assert account["state"] == "ready"
        assert account["battleId"] == "prior-battle"
        assert account["resolvedAttemptId"] == "load-uncertain"
        assert account["pendingAttemptId"] is None


def test_active_battle_settles_in_drain_and_account_returns_ready(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    args = _args(mode="reuse", duration_seconds=100, max_requests=20,
                 drain_seconds=20, drain_requests_per_battle=2, max_stage_attempts=3)
    budget = load.RunBudget(args)
    account = _stored_account()

    class Client:
        def __init__(self, worker, _origin, supplied_args, supplied_budget):
            self.worker = worker
            self.args = supplied_args
            self.budget = supplied_budget

        def request(self, _method, _endpoint, _payload=None, *, label, **_):
            phase = budget.before_request()
            budget.record(load.RequestResult(self.worker, label, 1, 200, "ok", phase))
            if label == "stage_launch":
                budget.started = time.monotonic() - 85
                return {"battleId": "battle-1", "revision": 1, "lifecycleStatus": "active",
                        "data": {"snapshot": {"phase": "active", "turnControl": {"acceptsCommands": True},
                                              "combatants": {"e": {"sideId": "enemy"}},
                                              "legalActions": [{"actorId": "a", "skillId": "s",
                                                                "minimumTargets": 1, "validTargetIds": ["e"]}]}}}
            assert label == "battle_command"
            return {"lifecycleStatus": "settled", "settlement": {"outcome": {
                "kind": "victory", "winningSideId": "friendly"}}}

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fixed_roster_available", lambda *_args: True)
    monkeypatch.setattr(load, "stage_one_available", lambda *_args: True)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(account)
        outcome = load.run_player(0, "https://127.0.0.1:8443", args, budget, pool, account)
        assert outcome["battles_settled"] == 1
        assert outcome["reason"] == "graceful_stop"
        assert account["state"] == "ready"
        assert account["recoveryCode"] == "ABCD-EFGH-IJKL-MNOP"
    report = load.summary(budget.rows, [outcome], 100, budget)
    assert (report["two_v_two_started"], report["two_v_two_settled"],
            report["unfinished_battles"]) == (1, 1, 0)
    assert (report["normal_requests"], report["drain_requests"]) == (1, 1)
    assert report["workers_gracefully_stopped"] == 1


def test_hard_request_budget_during_battle_keeps_account_in_flight(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    args = _args(mode="reuse", duration_seconds=100, max_requests=2,
                 drain_seconds=20, drain_requests_per_battle=1,
                 max_stage_attempts=1, max_commands_per_battle=3)
    budget = load.RunBudget(args)
    account = _stored_account()
    active = {"phase": "active", "turnControl": {"acceptsCommands": True},
              "combatants": {"e": {"sideId": "enemy"}},
              "legalActions": [{"actorId": "a", "skillId": "s", "minimumTargets": 1,
                                "validTargetIds": ["e"]}]}

    class Client:
        def __init__(self, worker, _origin, supplied_args, supplied_budget):
            self.worker = worker
            self.args = supplied_args
            self.budget = supplied_budget

        def request(self, _method, _endpoint, _payload=None, *, label, **_):
            phase = budget.before_request()
            budget.record(load.RequestResult(self.worker, label, 1, 200, "ok", phase))
            return {"battleId": "battle-1", "revision": 1, "lifecycleStatus": "active",
                    "data": {"snapshot": active}}

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fixed_roster_available", lambda *_args: True)
    monkeypatch.setattr(load, "stage_one_available", lambda *_args: True)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(account)
        outcome = load.run_player(0, "https://127.0.0.1:8443", args, budget, pool, account)
        assert outcome["reason"] == "StopRun"
        assert account["state"] == "active_battle"
        assert account["battleId"] == "battle-1"
        assert account["recoveryCode"] == "ABCD-EFGH-IJKL-MNOP"
    assert len(budget.rows) == 2
    assert budget.battle_attempts == 1 and budget.battle_settlements == 0
    assert not budget.active_battles


def _private_pool(tmp_path: Path) -> Path:
    directory = tmp_path / "private"
    directory.mkdir(mode=0o700)
    return directory / "players.json"


def _stored_account() -> dict:
    return {"playerId": "dedicated-player", "recoveryCode": "ABCD-EFGH-IJKL-MNOP",
            "profileId": "owned-profile", "state": "ready", "battleId": None}


def test_pool_is_private_outside_repository_and_exclusive(tmp_path: Path):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as first:
        first.append(_stored_account())
        assert os.stat(path).st_mode & 0o777 == 0o600
        with pytest.raises(ValueError, match="already in use"):
            with load.PlayerPool(path, "https://127.0.0.1:8443", create=False):
                pass
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as reopened:
        assert reopened.data["accounts"][0]["playerId"] == "dedicated-player"
    with pytest.raises(ValueError, match="outside the Git repository"):
        load.PlayerPool(load.REPOSITORY_ROOT / "pool.json", "https://127.0.0.1:8443", create=True)


def test_pool_rejects_duplicate_identity_and_wrong_origin(tmp_path: Path):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(_stored_account())
        with pytest.raises(ValueError, match="Duplicate player"):
            pool.append(_stored_account())
    with pytest.raises(ValueError, match="origin"):
        with load.PlayerPool(path, "https://localhost:8443", create=False):
            pass


def test_reuse_recovers_and_loads_owned_slot_without_creating(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    calls = []

    class Client:
        def __init__(self, *_):
            pass

        def request(self, method, endpoint, payload=None, **_):
            calls.append((method, endpoint))
            if endpoint == "/api/v1/sessions/recover":
                assert payload == {"recoveryCode": "ABCD-EFGH-IJKL-MNOP"}
                return {"playerId": "dedicated-player", "recoveryConfirmed": True}
            if endpoint == "/api/v1/save-slots":
                return {"slots": [{"slotId": 1, "occupied": True, "profileId": "owned-profile"}]}
            if endpoint == "/api/v1/save-slots/1/load":
                return {"slot": {"profileId": "owned-profile"}}
            if endpoint == "/api/v1/progression":
                return {"profileId": "owned-profile", "unlockedHeroDefinitionIds": list(load.TEAM)}
            if endpoint == "/api/v1/stages":
                return {"stages": [{"stageId": load.STAGE_ID, "battles": [
                    {"displayOrder": 1, "battleSize": 2, "unlocked": True}]}]}
            raise AssertionError(endpoint)

    monkeypatch.setattr(load, "PlayerClient", Client)

    def settled(_client, pool, account):
        pool.update(account, state="ready")
        return "victory"

    monkeypatch.setattr(load, "fight", settled)
    args = _args(mode="reuse", max_stage_attempts=1)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        account = {**_stored_account(), "playerName": "Legacy_Load_xyz"}
        pool.append(account)
        result = load.run_player(0, "https://127.0.0.1:8443", args,
                                 load.RunBudget(args), pool, account)
        assert result["battles_settled"] == 1
        assert account["state"] == "ready"
        assert account["playerName"] == "Legacy_Load_xyz"
    assert ("POST", "/api/v1/players") not in calls
    assert ("POST", "/api/v1/save-slots/1/create") not in calls
    assert ("POST", "/api/v1/sessions/recover") in calls
    assert ("POST", "/api/v1/save-slots/1/load") in calls
    assert not any("/battles/2" in path or "/battles/3" in path for _, path in calls)


def test_reused_player_repeats_only_fixed_stage_one_2v2(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    launches, commands, paths = [], [], []
    account = _stored_account()
    args = _args(mode="reuse", max_stage_attempts=2)
    budget = load.RunBudget(args)

    class Client:
        def __init__(self, _worker, _origin, _args, supplied_budget):
            self.budget = supplied_budget
            self.args = _args

        def request(self, method, endpoint, payload=None, **_):
            paths.append(endpoint)
            if endpoint == "/api/v1/progression":
                return {"profileId": account["profileId"], "unlockedHeroDefinitionIds": list(load.TEAM)}
            if endpoint == "/api/v1/stages":
                return {"stages": [{"stageId": load.STAGE_ID, "battles": [
                    {"displayOrder": 1, "battleSize": 2, "unlocked": True}]}]}
            if endpoint == f"/api/v1/stages/{load.STAGE_ID}/battles/1":
                assert account["state"] == "uncertain_launch"
                assert payload["playerTeam"] == list(load.TEAM)
                assert payload["playerFormation"] == "front-rear"
                assert payload["mode"] == "learner"
                launches.append(payload["attemptId"])
                return {"battleId": f"battle-{len(launches)}", "revision": 1,
                        "lifecycleStatus": "active", "data": {"snapshot": {
                            "phase": "active", "turnControl": {"acceptsCommands": True},
                            "combatants": {"enemy-1": {"sideId": "enemy"}},
                            "legalActions": [{"actorId": "friendly-1", "skillId": "skill.valid",
                                              "minimumTargets": 1, "validTargetIds": ["enemy-1"]}],
                        }}}
            if endpoint.endswith("/commands"):
                commands.append(payload)
                return {"lifecycleStatus": "settled", "settlement": {"outcome": {
                    "kind": "victory", "winningSideId": "friendly" if len(commands) == 1 else "enemy"
                }}}
            raise AssertionError(endpoint)

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(account)
        result = load.run_player(0, "https://127.0.0.1:8443", args, budget, pool, account)
        assert result["battles_settled"] == 2
        assert account["state"] == "ready"
        assert account["playerId"] == "dedicated-player"
    assert len(set(launches)) == 2
    assert len({command["commandId"] for command in commands}) == 2
    assert all(command["targetIds"] == ["enemy-1"] for command in commands)
    assert not any("/battles/2" in endpoint or "/battles/3" in endpoint for endpoint in paths)
    report = load.summary([], [result], 60, budget)
    assert (report["two_v_two_started"], report["two_v_two_settled"],
            report["two_v_two_victories"], report["two_v_two_defeats"],
            report["battles_per_minute"]) == (2, 2, 1, 1, 2)


def test_missing_fixed_hero_blocks_reuse_before_launch(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    calls = []

    class Client:
        def __init__(self, *_):
            self.sent_requests = 0

        def request(self, method, endpoint, payload=None, **_):
            self.sent_requests += 1
            calls.append(endpoint)
            if endpoint == "/api/v1/progression":
                return {"profileId": "owned-profile", "unlockedHeroDefinitionIds": [load.TEAM[0]]}
            raise AssertionError(endpoint)

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    args = _args(mode="reuse")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        account = _stored_account()
        pool.append(account)
        result = load.run_player(0, "https://127.0.0.1:8443", args,
                                 load.RunBudget(args), pool, account)
        assert result["reason"] == "required_hero_missing_or_profile_mismatch"
        assert account["state"] == "requires_reconciliation"
    assert calls == ["/api/v1/progression"]


def test_recovery_failure_keeps_account_pending_and_never_creates(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    calls = []

    class Client:
        def __init__(self, *_):
            self.sent_requests = 0

        def request(self, method, endpoint, *_args, **_kwargs):
            self.sent_requests += 1
            calls.append((method, endpoint))
            raise load.ApiFailure("api_error", 401)

    monkeypatch.setattr(load, "PlayerClient", Client)
    args = _args(mode="reuse")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        account = _stored_account()
        pool.append(account)
        result = load.run_player(0, "https://127.0.0.1:8443", args,
                                 load.RunBudget(args), pool, account)
        assert result["reason"] == "api_error"
        assert account["state"] == "requires_reconciliation"
    assert calls == [("POST", "/api/v1/sessions/recover")]


def test_interrupted_run_requires_explicit_reconciliation(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        account = _stored_account()
        pool.append(account)
        pool.update(account, state="in_flight", battleId="battle.old")
    with pytest.raises(SystemExit, match="confirmation"):
        load.main(["--mode", "reconcile", "--pool-file", str(path), "--execute"])
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fixed_roster_available", lambda _client, _account: True)
    monkeypatch.setattr(load, "stage_one_available", lambda _client: True)
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: object())
    args = _args(mode="reconcile")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        account = pool.data["accounts"][0]
        assert load.reconcile_player(0, "https://127.0.0.1:8443", args,
                                     load.RunBudget(args), pool, account)
        assert account["state"] == "ready" and account["battleId"] == "battle.old"


def test_reuse_refuses_interrupted_pool_before_any_network(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append({**_stored_account(), "state": "in_flight", "battleId": "unfinished-battle"})
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: pytest.fail("Network client must not start"))
    with pytest.raises(SystemExit, match="reconcile first"):
        load.main(["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
                   "--mode", "reuse", "--concurrency", "1", "--execute"])


def test_incremental_creation_and_pending_pool_fail_closed(monkeypatch, tmp_path: Path, capsys):
    path = _private_pool(tmp_path)

    def provision(worker, _origin, _args, _budget, pool, account):
        assert account is None
        reservation = pool.reserve_next_player()
        number = uuid.uuid4().hex
        pool.update(reservation, playerId=f"player-{number}", recoveryCode=f"code-{number}",
                    profileId=f"profile-{number}", state="ready", battleId=None)
        return {"worker": worker, "provisioned": True, "reason": "",
                "player_id": f"player-{number}", "profile_id": f"profile-{number}"}

    monkeypatch.setattr(load, "provision_player", provision)
    common = ["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
              "--mode", "provision", "--execute", "--concurrency", "2"]
    assert load.main(common + ["--pool-size", "2"]) == 0
    assert json.loads(capsys.readouterr().out)["pool_total"] == 2
    previous = 2
    for target in (10, 30, 50, 100):
        assert load.main(common + ["--pool-size", str(target)]) == 0
        report = json.loads(capsys.readouterr().out)
        assert report["pool_total"] == target
        assert report["accounts_attempted"] == target - previous
        assert report["concurrency_limit"] == 2
        previous = target
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        assert [account["playerName"] for account in pool.data["accounts"]] == [
            f"Test_Player_{number:03d}" for number in range(1, 101)
        ]
        pool.update(pool.data["accounts"][0], state="in_flight")
    with pytest.raises(SystemExit, match="reconcile"):
        load.main(common + ["--pool-size", "100"])
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        assert len(pool.data["accounts"]) == 100


def test_enrollment_uses_reserved_fixed_name_without_uuid_suffix(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    posted_names = []

    class Client:
        def __init__(self, *_):
            pass

        def request(self, method, endpoint, payload=None, **_):
            assert (method, endpoint) == ("POST", "/api/v1/players")
            posted_names.append(payload["playerName"])
            raise load.ApiFailure("api_error", 503)

    monkeypatch.setattr(load, "PlayerClient", Client)
    args = _args(mode="provision")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        for worker in range(2):
            result = load.provision_player(worker, "https://127.0.0.1:8443", args,
                                     load.RunBudget(args), pool, None)
            assert result["reason"] == "api_error"
        assert posted_names == ["Test_Player_001", "Test_Player_002"]
        assert [item["playerName"] for item in pool.data["accounts"]] == posted_names
        assert all(item["state"] == "enrollment_pending" for item in pool.data["accounts"])


def test_provisioning_account_resumes_without_replacement(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: object())
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fixed_roster_available", lambda _client, _account: True)
    monkeypatch.setattr(load, "stage_one_available", lambda _client: True)
    launched = []

    def finish(_client, pool, account):
        launched.append(load.STAGE_INDEX)
        pool.update(account, state="ready")
        return "victory"

    monkeypatch.setattr(load, "fight", finish)
    args = _args(mode="provision")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        account = {**_stored_account(), "state": "provisioning"}
        pool.append(account)
        args.max_stage_attempts = 1
        result = load.provision_player(0, "https://127.0.0.1:8443", args,
                                 load.RunBudget(args), pool, account)
        assert result["provisioned"] is True
        assert account["state"] == "ready"
    assert launched == []


def test_uncertain_enrollment_blocks_replacement_and_reconciliation(tmp_path: Path):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append({"state": "enrollment_pending", "reservationId": "reservation-one"})
    common = ["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
              "--execute"]
    with pytest.raises(SystemExit, match="uncertain"):
        load.main(common + ["--mode", "create", "--pool-size", "2"])
    with pytest.raises(SystemExit, match="Only credentialed interrupted"):
        load.main(common + ["--mode", "reconcile", "--reconcile-rows", "1",
                            "--concurrency", "1", "--confirm-reconcile",
                            load.RECONCILE_CONFIRMATION])


@pytest.mark.parametrize("failure", [load.StopRun("budget stopped before send"),
                                      load.ApiFailure("timeout")])
def test_interrupted_enrollment_preserves_credentialless_reservation(
    monkeypatch, tmp_path: Path, failure: Exception,
):
    path = _private_pool(tmp_path)
    requests = []

    class Client:
        def __init__(self, *_):
            pass

        def request(self, method, endpoint, payload=None, **_):
            requests.append((method, endpoint, payload["playerName"]))
            raise failure

    monkeypatch.setattr(load, "PlayerClient", Client)
    args = _args(mode="provision")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        result = load.provision_player(0, "https://127.0.0.1:8443", args,
                                 load.RunBudget(args), pool, None)
        assert result["provisioned"] is False
        assert len(pool.data["accounts"]) == 1
        reservation = pool.data["accounts"][0]
        assert reservation["state"] == "enrollment_pending"
        assert reservation["playerName"] == "Test_Player_001"
        assert reservation["reservationId"]
        assert "playerId" not in reservation and "recoveryCode" not in reservation
    assert requests == [("POST", "/api/v1/players", "Test_Player_001")]
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as reopened:
        assert reopened.data["accounts"][0]["state"] == "enrollment_pending"


def test_enrollment_code_is_saved_before_later_request_failure(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    calls = []

    class Client:
        def __init__(self, *_):
            pass

        def request(self, method, endpoint, payload=None, **_):
            calls.append(endpoint)
            if endpoint == "/api/v1/players":
                return {"playerId": "new-player", "recoveryCode": "LOCAL-TEST-CODE"}
            raise load.StopRun("budget stopped after code persisted")

    monkeypatch.setattr(load, "PlayerClient", Client)
    args = _args(mode="provision")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        result = load.provision_player(0, "https://127.0.0.1:8443", args,
                                 load.RunBudget(args), pool, None)
        assert result["reason"] == "StopRun"
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as reopened:
        account = reopened.data["accounts"][0]
        assert account["state"] == "provisioning"
        assert account["playerId"] == "new-player"
        assert account["recoveryCode"] == "LOCAL-TEST-CODE"
    assert calls == ["/api/v1/players", "/api/v1/recovery-code/acknowledge"]


def test_mixed_pool_reconcile_requires_explicit_rows_without_network(
    monkeypatch, tmp_path: Path,
):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append({**_stored_account(), "state": "in_flight", "battleId": "unfinished-battle"})
        pool.reserve_next_player()
    before = path.read_bytes()
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: pytest.fail("No network allowed"))
    with pytest.raises(SystemExit, match="requires explicit 1-based row numbers"):
        load.main(["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
                   "--mode", "reconcile", "--concurrency", "2", "--execute",
                   "--confirm-reconcile", load.RECONCILE_CONFIRMATION])
    assert path.read_bytes() == before


def test_failed_reconciliation_keeps_valid_battle_account_blocked(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        account = {**_stored_account(), "state": "in_flight", "battleId": "unfinished-battle"}
        pool.append(account)
        monkeypatch.setattr(load, "PlayerClient", lambda *_args: object())
        monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs:
                            (_ for _ in ()).throw(load.ApiFailure("api_error", 401)))
        assert not load.reconcile_player(0, "https://127.0.0.1:8443", _args(mode="reconcile"),
                                         load.RunBudget(_args()), pool, account)
        assert account["state"] == "in_flight"
        assert account["battleId"] == "unfinished-battle"


def _mixed_recovery_pool(tmp_path: Path) -> Path:
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        for number in range(1, 9):
            pool.append({"playerId": f"player-{number}", "recoveryCode": f"private-code-{number}",
                         "profileId": f"profile-{number}", "playerName": f"Test_Player_{number:03d}",
                         "state": "in_flight" if number in (7, 8) else "ready",
                         "battleId": f"battle-{number}" if number in (7, 8) else None})
        pool.reserve_next_player()
        pool.reserve_next_player()
    return path


def test_inspect_is_read_only_and_reports_only_presence_flags(monkeypatch, tmp_path: Path, capsys):
    path = _mixed_recovery_pool(tmp_path)
    before_manifest = path.read_bytes()
    before_lock = Path(f"{path}.lock").read_bytes()
    before_files = set(path.parent.iterdir())
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: pytest.fail("Inspection must not use network"))
    assert load.main(["--mode", "inspect", "--pool-file", str(path),
                      "--base-url", "https://127.0.0.1:8443"]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["manifestReadyWithCredentials"] == 6
    assert report["serverVerifiedReadyAccounts"] is None
    assert [row["state"] for row in report["accounts"]] == [
        *(["ready"] * 6), "in_flight", "in_flight", "enrollment_pending", "enrollment_pending"
    ]
    assert report["accounts"][6] == {"row": 7, "state": "in_flight", "hasPlayerId": True,
                                      "hasRecoveryCode": True, "hasBattleId": True}
    assert report["accounts"][8] == {"row": 9, "state": "enrollment_pending",
                                      "hasPlayerId": False, "hasRecoveryCode": False,
                                      "hasBattleId": False}
    assert "private-code" not in output and "player-7" not in output
    assert path.read_bytes() == before_manifest
    assert Path(f"{path}.lock").read_bytes() == before_lock
    assert set(path.parent.iterdir()) == before_files
    with pytest.raises(SystemExit, match="read-only"):
        load.main(["--mode", "inspect", "--pool-file", str(path), "--execute"])
    with pytest.raises(SystemExit, match="origin"):
        load.main(["--mode", "inspect", "--pool-file", str(path),
                   "--base-url", "https://localhost:8443"])
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False):
        with pytest.raises(SystemExit, match="already in use"):
            load.main(["--mode", "inspect", "--pool-file", str(path),
                       "--base-url", "https://127.0.0.1:8443"])


def test_inspect_nonlocal_origin_remains_offline_without_write_opt_ins(
    monkeypatch, tmp_path: Path, capsys,
):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://loc-tactics.duckdns.org", create=True) as pool:
        pool.append({**_stored_account(), "playerName": "Test_Player_001"})
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: pytest.fail("No network allowed"))
    assert load.main(["--mode", "inspect", "--pool-file", str(path),
                      "--base-url", "https://loc-tactics.duckdns.org"]) == 0
    assert json.loads(capsys.readouterr().out)["manifestReadyWithCredentials"] == 1


def test_targeted_reconciliation_skips_pending_and_verifies_id_and_code(
    monkeypatch, tmp_path: Path, capsys,
):
    path = _mixed_recovery_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        untouched = [dict(pool.data["accounts"][index]) for index in (*range(6), 8, 9)]
    calls = []

    class Client:
        def __init__(self, worker, *_):
            self.number = worker + 7

        def request(self, method, endpoint, payload=None, **_):
            calls.append((self.number, method, endpoint))
            if endpoint == "/api/v1/sessions/recover":
                assert payload == {"recoveryCode": f"private-code-{self.number}"}
                return {"playerId": f"player-{self.number}", "recoveryConfirmed": True}
            if endpoint == "/api/v1/save-slots":
                return {"slots": [{"slotId": 1, "occupied": True,
                                   "profileId": f"profile-{self.number}"}]}
            if endpoint == "/api/v1/save-slots/1/load":
                return {"slot": {"profileId": f"profile-{self.number}"}}
            if endpoint == f"/api/v1/battles/battle-{self.number}":
                return {"detail": {"code": "battleNoLongerActive"}}
            if endpoint == "/api/v1/progression":
                return {"profileId": f"profile-{self.number}",
                        "unlockedHeroDefinitionIds": list(load.TEAM)}
            if endpoint == "/api/v1/stages":
                return {"stages": [{"stageId": load.STAGE_ID, "battles": [
                    {"displayOrder": 1, "battleSize": 2, "unlocked": True}]}]}
            raise AssertionError(endpoint)

    monkeypatch.setattr(load, "PlayerClient", Client)
    assert load.main(["--mode", "reconcile", "--reconcile-rows", "7,8",
                      "--concurrency", "2", "--pool-file", str(path),
                      "--base-url", "https://127.0.0.1:8443", "--execute",
                      "--confirm-reconcile", load.RECONCILE_CONFIRMATION]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["rowResults"] == [{"row": 7, "status": "ready"}, {"row": 8, "status": "ready"}]
    assert report["pendingEnrollmentsUntouched"] == 2
    assert "private-code" not in output and "player-7" not in output
    assert all(endpoint != "/api/v1/players" for _, _, endpoint in calls)
    assert {number for number, _, _ in calls} == {7, 8}
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        assert [pool.data["accounts"][index] for index in (*range(6), 8, 9)] == untouched
        assert all(pool.data["accounts"][index]["state"] == "ready" for index in (6, 7))
        assert [pool.data["accounts"][index]["battleId"] for index in (6, 7)] == ["battle-7", "battle-8"]


def test_targeted_reconciliation_wrong_player_id_keeps_interrupted_state(
    monkeypatch, tmp_path: Path, capsys,
):
    path = _mixed_recovery_pool(tmp_path)

    class Client:
        def __init__(self, *_):
            pass

        def request(self, method, endpoint, payload=None, **_):
            assert endpoint == "/api/v1/sessions/recover"
            assert payload == {"recoveryCode": "private-code-7"}
            return {"playerId": "wrong-player", "recoveryConfirmed": True}

    monkeypatch.setattr(load, "PlayerClient", Client)
    assert load.main(["--mode", "reconcile", "--reconcile-rows", "7",
                      "--concurrency", "1", "--pool-file", str(path),
                      "--base-url", "https://127.0.0.1:8443", "--execute",
                      "--confirm-reconcile", load.RECONCILE_CONFIRMATION]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["rowResults"] == [{"row": 7, "status": "failed_kept_interrupted"}]
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        assert pool.data["accounts"][6]["state"] == "in_flight"
        assert pool.data["accounts"][6]["battleId"] == "battle-7"
        assert all(pool.data["accounts"][index]["state"] == "enrollment_pending"
                   for index in (8, 9))


def test_reconciliation_failed_authoritative_roster_check_keeps_interrupted_state(
    monkeypatch, tmp_path: Path,
):
    path = _mixed_recovery_pool(tmp_path)
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: object())
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fixed_roster_available", lambda *_args: False)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=False) as pool:
        account = pool.data["accounts"][6]
        before = dict(account)
        assert not load.reconcile_player(0, "https://127.0.0.1:8443", _args(mode="reconcile"),
                                         load.RunBudget(_args()), pool, account)
        assert account == before


def test_targeted_reconciliation_rejects_pending_rows_before_network(monkeypatch, tmp_path: Path):
    path = _mixed_recovery_pool(tmp_path)
    before = path.read_bytes()
    monkeypatch.setattr(load, "PlayerClient", lambda *_args: pytest.fail("No network allowed"))
    with pytest.raises(SystemExit, match="Only credentialed interrupted"):
        load.main(["--mode", "reconcile", "--reconcile-rows", "9,10",
                   "--concurrency", "2", "--pool-file", str(path),
                   "--base-url", "https://127.0.0.1:8443", "--execute",
                   "--confirm-reconcile", load.RECONCILE_CONFIRMATION])
    assert path.read_bytes() == before


def test_disposable_public_backend_does_not_make_player_names_unique(tmp_path: Path):
    """A fresh name lookup alone cannot make a retry idempotent."""
    store = ProgressionStore(tmp_path / "disposable-public.sqlite3",
                             public_mode=True, allow_public_initialize=True)
    service = PublicIdentityService(store, key=b"local-test-key-material-32-bytes!!")
    first = service.enroll("Test_Player_009")
    second = service.enroll("Test_Player_009")
    assert first.player_id != second.player_id
    assert first.recovery_code != second.recovery_code


def test_partial_enrollment_and_ambiguous_second_response_never_retry_pending(
    monkeypatch, tmp_path: Path,
):
    path = _private_pool(tmp_path)
    calls = []

    class Client:
        def __init__(self, *_):
            pass

        def request(self, method, endpoint, payload=None, **_):
            calls.append(endpoint)
            if endpoint == "/api/v1/players":
                if payload["playerName"] == "Test_Player_001":
                    return {"playerId": "first-player", "recoveryCode": "FIRST-LOCAL-CODE"}
                assert payload["playerName"] == "Test_Player_002"
                raise load.ApiFailure("timeout")
            if endpoint == "/api/v1/recovery-code/acknowledge":
                return {}
            if endpoint == "/api/v1/save-slots/1/create":
                return {"slot": {"profileId": "first-profile"}}
            if endpoint == "/api/v1/progression":
                return {"profileId": "first-profile", "unlockedHeroDefinitionIds": list(load.TEAM)}
            if endpoint == "/api/v1/stages":
                return {"stages": [{"stageId": load.STAGE_ID, "battles": [
                    {"displayOrder": 1, "battleSize": 2, "unlocked": True}]}]}
            raise AssertionError(endpoint)

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(load, "fight", lambda *_args: pytest.fail("Provisioning must not battle"))
    args = _args(mode="provision", max_stage_attempts=1)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        first = load.provision_player(0, "https://127.0.0.1:8443", args,
                                load.RunBudget(args), pool, None)
        second = load.provision_player(1, "https://127.0.0.1:8443", args,
                                 load.RunBudget(args), pool, None)
        assert first["provisioned"] is True
        assert second["reason"] == "timeout"
        assert pool.data["accounts"][0]["state"] == "ready"
        assert pool.data["accounts"][0]["playerId"] == "first-player"
        assert pool.data["accounts"][1]["state"] == "enrollment_pending"
        assert "playerId" not in pool.data["accounts"][1]
        assert "recoveryCode" not in pool.data["accounts"][1]
    before = path.read_bytes()
    call_count = len(calls)
    with pytest.raises(SystemExit, match="uncertain"):
        load.main(["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
                   "--mode", "create", "--pool-size", "2", "--execute"])
    assert path.read_bytes() == before
    assert len(calls) == call_count


def test_provision_and_legacy_create_never_dispatch_battle_workers(monkeypatch, tmp_path: Path, capsys):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append({**_stored_account(), "state": "ready"})
    monkeypatch.setattr(load, "run_player", lambda *_: pytest.fail("Battle worker dispatched"))
    monkeypatch.setattr(load, "fight", lambda *_: pytest.fail("Battle launched"))
    for mode in ("provision", "create"):
        assert load.main(["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
                          "--mode", mode, "--pool-size", "1", "--concurrency", "1",
                          "--execute"]) == 0
        report = json.loads(capsys.readouterr().out)
        assert report["accounts_attempted"] == 0
        assert report["battles_started"] == 0


def test_inspect_reports_duplicates_but_mutating_mode_rejects_them(tmp_path: Path, capsys):
    path = _private_pool(tmp_path)
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        pool.append(_stored_account())
        duplicate = {**_stored_account(), "playerName": "Test_Player_002",
                     "profileId": "different-profile"}
        pool.data["accounts"].append(duplicate)
        pool.save()
    assert load.main(["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
                      "--mode", "inspect", "--concurrency", "2"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["totalManifestRecords"] == 2
    assert report["manifestReadyWithCredentials"] == 2
    assert report["duplicatePlayerIds"] == 1
    assert report["duplicateRecoveryCodes"] == 1
    assert report["manifestEligibleAccounts"] == 0
    assert report["enoughEligibleForRequestedTest"] is False
    assert report["serverVerifiedReadyAccounts"] is None
    assert "recoveryCode" not in json.dumps(report)
    with pytest.raises(SystemExit, match="duplicate"):
        load.main(["--base-url", "https://127.0.0.1:8443", "--pool-file", str(path),
                   "--mode", "reuse", "--concurrency", "1", "--execute"])


def test_failed_new_account_recovery_keeps_saved_code_and_never_battles(monkeypatch, tmp_path: Path):
    path = _private_pool(tmp_path)
    calls = []

    class Client:
        def __init__(self, *_):
            pass

        def request(self, method, endpoint, payload=None, **_):
            calls.append(endpoint)
            if endpoint == "/api/v1/players":
                return {"playerId": "created-player", "recoveryCode": "SECRET-LOCAL-CODE"}
            if endpoint == "/api/v1/recovery-code/acknowledge":
                return {}
            if endpoint == "/api/v1/save-slots/1/create":
                return {"slot": {"profileId": "created-profile"}}
            raise AssertionError(endpoint)

    monkeypatch.setattr(load, "PlayerClient", Client)
    monkeypatch.setattr(load, "recover_account", lambda *_args, **_kwargs:
                        (_ for _ in ()).throw(load.ApiFailure("api_error")))
    monkeypatch.setattr(load, "fight", lambda *_args: pytest.fail("Battle launched"))
    args = _args(mode="provision")
    with load.PlayerPool(path, "https://127.0.0.1:8443", create=True) as pool:
        result = load.provision_player(0, "https://127.0.0.1:8443", args,
                                       load.RunBudget(args), pool, None)
        assert result["provisioned"] is False
        assert result["reason"] == "api_error"
        assert pool.data["accounts"][0]["state"] == "provisioning"
        assert pool.data["accounts"][0]["recoveryCode"] == "SECRET-LOCAL-CODE"
    assert calls == ["/api/v1/players", "/api/v1/recovery-code/acknowledge",
                     "/api/v1/save-slots/1/create"]
