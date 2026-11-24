#!/usr/bin/env python3
"""Bounded, opt-in Public Stage-1 2v2 tester. Never point at real players.

The default invocation is a zero-request plan. Provision (and legacy create)
enrolls dedicated accounts without battles. Reuse recovers ready accounts and
repeatedly plays Warrior's Barrack battle 1. There is no player-data cleanup API.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import fcntl
import http.cookiejar
import ipaddress
import json
import math
import os
from pathlib import Path
import socket
import ssl
import stat
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPSHandler, HTTPCookieProcessor, HTTPRedirectHandler, ProxyHandler, Request, build_opener
import uuid


PRODUCTION_CONFIRMATION = "OWNER_APPROVED_STAGE_4_2_1_WRITE"
RECONCILE_CONFIRMATION = "ABANDON_INTERRUPTED_TEST_BATTLES"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STAGE_ID = "warriors-barrack"
STAGE_INDEX = 1
TEAM = ("hero.warrior.weapon_master", "hero.mage.comprehensiveness")
FORMATION = "front-rear"  # Team slot 1 is front; slot 2 is rear.
SENSITIVE_INITIALIZATION_PATHS = frozenset({
    "/api/v1/players", "/api/v1/sessions/recover", "/api/v1/recovery-code/forgot",
})


def is_loopback(host: str) -> bool:
    """Only literal loopback addresses and the exact localhost name are local."""
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        if host.lower() != "localhost":
            return False
        try:
            answers = socket.getaddrinfo(host, None)
            return bool(answers) and all(
                ipaddress.ip_address(answer[4][0]).is_loopback for answer in answers
            )
        except (OSError, ValueError):
            return False


def validate_target(args: argparse.Namespace) -> tuple[str, bool]:
    parsed = urlsplit(args.base_url)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username or parsed.password or parsed.path not in {"", "/"}
            or parsed.query or parsed.fragment):
        raise ValueError("--base-url must be a bare HTTP(S) origin without credentials or path")
    local = is_loopback(parsed.hostname)
    if args.execute and parsed.scheme != "https":
        raise ValueError("Public API execution requires HTTPS, including local tests")
    if not local:
        if parsed.scheme != "https":
            raise ValueError("Non-loopback targets require HTTPS")
        if (getattr(args, "mode", None) != "inspect"
                and (not args.allow_production or args.owner_authorization != PRODUCTION_CONFIRMATION)):
            raise ValueError("Non-loopback execution requires both production opt-ins and separate Owner authorization")
    if args.allow_insecure_local_tls and not local:
        raise ValueError("TLS verification can only be disabled for a loopback target")
    return f"{parsed.scheme}://{parsed.netloc}", local


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class RequestResult:
    worker: int
    endpoint: str
    latency_ms: float
    status: int
    category: str
    phase: str = "normal"
    body_format: str = "json"


class StopRun(RuntimeError):
    pass


class ApiFailure(RuntimeError):
    def __init__(self, category: str, status: int = 0):
        self.category = category
        self.status = status
        super().__init__(f"{category} ({status})")


class PlayerPool:
    """Exclusive, crash-durable manifest for dedicated test identities only."""

    def __init__(self, path: Path, origin: str, *, create: bool):
        if not path.is_absolute():
            raise ValueError("--pool-file must be an absolute path outside the repository")
        if path.is_symlink():
            raise ValueError("Pool file must not be a symlink")
        self.path = path.resolve(strict=False)
        if self.path == REPOSITORY_ROOT or REPOSITORY_ROOT in self.path.parents:
            raise ValueError("--pool-file must be outside the Git repository")
        parent = self.path.parent
        if (not parent.is_dir() or parent.stat().st_uid != os.getuid()
                or parent.stat().st_mode & 0o077):
            raise ValueError("Pool parent directory must be owner-owned and mode 0700")
        self.origin = origin
        self.create = create
        self.lock_fd: int | None = None
        self.thread_lock = threading.RLock()
        self.data: dict = {}

    def __enter__(self) -> PlayerPool:
        lock_path = Path(f"{self.path}.lock")
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        self.lock_fd = os.open(lock_path, flags, 0o600)
        try:
            if os.fstat(self.lock_fd).st_uid != os.getuid() or os.fstat(self.lock_fd).st_mode & 0o077:
                raise ValueError("Pool lock must be owner-owned and mode 0600")
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(self.lock_fd)
            self.lock_fd = None
            raise ValueError("Account pool is already in use") from exc
        except Exception:
            os.close(self.lock_fd)
            self.lock_fd = None
            raise
        try:
            if self.path.exists():
                info = self.path.stat()
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise ValueError("Pool file must be owner-owned and mode 0600")
                self.data = json.loads(self.path.read_text())
                self._validate_data(self.data)
            elif self.create:
                self.data = {"schemaVersion": 1, "origin": self.origin, "accounts": []}
                self.save()
            else:
                raise ValueError("Pool file does not exist; create it explicitly")
        except Exception:
            self.__exit__()
            raise
        return self

    def _validate_data(self, data: object, *, allow_duplicate_identities: bool = False) -> None:
        if (not isinstance(data, dict) or data.get("schemaVersion") != 1
                or data.get("origin") != self.origin
                or not isinstance(data.get("accounts"), list)
                or any(not isinstance(item, dict) for item in data["accounts"])):
            raise ValueError("Pool schema or origin does not match")
        accounts = data["accounts"]
        enrolled = [item for item in accounts if item.get("state") != "enrollment_pending"]
        ids = [item.get("playerId") for item in enrolled]
        codes = [item.get("recoveryCode") for item in enrolled]
        profiles = [item.get("profileId") for item in accounts if item.get("profileId")]
        names = [item["playerName"] for item in accounts if item.get("playerName")]
        reservations = [item.get("reservationId") for item in accounts
                        if item.get("state") == "enrollment_pending"]
        if (any(not isinstance(item, str) or not item
                for item in ids + codes + profiles + names + reservations)
                or (not allow_duplicate_identities and
                    (len(ids) != len(set(ids)) or len(codes) != len(set(codes))))
                or len(profiles) != len(set(profiles)) or len(names) != len(set(names))
                or len(reservations) != len(set(reservations))):
            raise ValueError("Pool contains duplicate or missing player identities")
        if any(not isinstance(item.get("state"), str)
               or item["state"] not in {"ready", "provisioning", "in_flight", "enrollment_pending",
                                     "initializing", "requires_reconciliation", "uncertain_launch",
                                     "active_battle"}
               for item in accounts):
            raise ValueError("Pool contains an unknown account state")
        if any((item["state"] == "uncertain_launch" and
                not isinstance(item.get("pendingAttemptId"), str)) or
               (item["state"] == "active_battle" and
                not isinstance(item.get("battleId"), str))
               for item in accounts):
            raise ValueError("Pool contains an incomplete battle-state record")

    def inspect(self, requested_concurrency: int = 2) -> dict:
        """Read a locked manifest snapshot without creating files or making requests."""
        lock_fd = os.open(f"{self.path}.lock", os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            info = os.fstat(lock_fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ValueError("Pool lock must be owner-owned and mode 0600")
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ValueError("Account pool is already in use") from exc
            descriptor = os.open(self.path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            with os.fdopen(descriptor) as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise ValueError("Pool file must be owner-owned and mode 0600")
                data = json.load(stream)
            self._validate_data(data, allow_duplicate_identities=True)
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
        rows = [{"row": number, "state": item["state"],
                 "hasPlayerId": bool(item.get("playerId")),
                 "hasRecoveryCode": bool(item.get("recoveryCode")),
                 "hasBattleId": bool(item.get("battleId"))}
                for number, item in enumerate(data["accounts"], 1)]
        accounts = data["accounts"]
        ids = [item.get("playerId") for item in accounts if item.get("playerId")]
        codes = [item.get("recoveryCode") for item in accounts if item.get("recoveryCode")]
        duplicate_ids = len(ids) - len(set(ids))
        duplicate_codes = len(codes) - len(set(codes))
        ready = sum(item.get("state") == "ready" and bool(item.get("playerId"))
                    and bool(item.get("recoveryCode")) and bool(item.get("profileId"))
                    for item in accounts)
        eligible = ready if not (duplicate_ids or duplicate_codes) else 0
        return {"mode": "READ_ONLY_INSPECT", "originMatches": True,
                "accounts": rows,
                "totalManifestRecords": len(accounts),
                "manifestReadyWithCredentials": ready,
                "pendingEnrollments": sum(item["state"] == "enrollment_pending" for item in accounts),
                "provisioningAccounts": sum(item["state"] == "provisioning" for item in accounts),
                "inFlightAccounts": sum(item["state"] == "in_flight" for item in accounts),
                "initializingAccounts": sum(item["state"] == "initializing" for item in accounts),
                "requiresReconciliationAccounts": sum(item["state"] == "requires_reconciliation"
                                                      for item in accounts),
                "uncertainLaunches": sum(item["state"] == "uncertain_launch" for item in accounts),
                "lastConfirmedActiveBattles": sum(item["state"] == "active_battle"
                                                   for item in accounts),
                "duplicatePlayerIds": duplicate_ids,
                "duplicateRecoveryCodes": duplicate_codes,
                "manifestEligibleAccounts": eligible,
                "requestedConcurrency": requested_concurrency,
                "enoughEligibleForRequestedTest": eligible >= requested_concurrency,
                "serverVerifiedReadyAccounts": None,
                "pendingEnrollmentNotice": (
                    "Enrollment without a saved Recovery Code cannot be recovered automatically; "
                    "no enrollment was retried."
                ) if any(item["state"] == "enrollment_pending" for item in rows) else None}

    def __exit__(self, *_: object) -> None:
        if self.lock_fd is not None:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            os.close(self.lock_fd)
            self.lock_fd = None

    def save(self) -> None:
        with self.thread_lock:
            temporary = self.path.with_name(f".{self.path.name}.{uuid.uuid4().hex}.tmp")
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(temporary, flags, 0o600)
            try:
                with os.fdopen(descriptor, "w") as stream:
                    json.dump(self.data, stream, separators=(",", ":"))
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
                directory = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            finally:
                if temporary.exists():
                    temporary.unlink()

    def update(self, account: dict, **fields: object) -> None:
        with self.thread_lock:
            account.update(fields)
            self.save()

    def append(self, account: dict) -> None:
        with self.thread_lock:
            if account.get("playerId") and any(item.get("playerId") == account["playerId"]
                                               for item in self.data["accounts"]):
                raise ValueError("Duplicate player identity in account pool")
            if account.get("playerName") and any(item.get("playerName") == account["playerName"]
                                                 for item in self.data["accounts"]):
                raise ValueError("Duplicate player name in account pool")
            self.data["accounts"].append(account)
            self.save()

    def reserve_next_player(self) -> dict:
        """Persist the next numbered identity before sending its enrollment request."""
        with self.thread_lock:
            number = len(self.data["accounts"]) + 1
            if number > 100:
                raise ValueError("Account pool is limited to 100 players")
            reservation = {"state": "enrollment_pending", "reservationId": uuid.uuid4().hex,
                           "playerName": f"Test_Player_{number:03d}"}
            self.append(reservation)
            return reservation


class RunBudget:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.started = time.monotonic()
        self.next_request = self.started
        self.next_initialization_request = self.started
        self.next_general_initialization_request = self.started
        # The CLI supplies this flag for reuse runs. Older direct-call test
        # namespaces retain their original single-window behavior.
        self.separate_initialization = (getattr(args, "mode", None) == "reuse"
                                        and hasattr(args, "init_duration_seconds"))
        self.battle_started_at: float | None = None if self.separate_initialization else self.started
        self.lock = threading.Lock()
        self.stop = threading.Event()
        self.draining = threading.Event()
        self.drain_reason: str | None = None
        self.initialization_slots = threading.BoundedSemaphore(
            getattr(args, "init_concurrency", args.players)
        )
        self.battle_slots = threading.BoundedSemaphore(
            getattr(args, "max_active_battles", args.players)
        )
        self.initialized_workers = 0
        self.initialization_completed_at: float | None = None
        self.rows: list[RequestResult] = []
        self.in_flight = 0
        self.active_battles: set[int] = set()
        self.peak_active_battles = 0
        self.battle_attempts = 0
        self.battle_settlements = 0
        self.battle_victories = 0
        self.battle_defeats = 0
        self.battle_draws = 0

    def acquire_battle_slot(self) -> bool:
        """Queue extra player workers without exceeding the server battle cap."""
        while not self.stop.is_set() and not self.draining.is_set():
            with self.lock:
                battle_start = self.battle_started_at
            if battle_start is None:
                return False
            remaining = (self.args.duration_seconds
                         - getattr(self.args, "drain_seconds", 0)
                         - (time.monotonic() - battle_start))
            if remaining <= 0:
                return False
            if self.battle_slots.acquire(timeout=min(1.0, remaining)):
                return True
        return False

    def begin_battle(self, worker: int) -> bool:
        """Reserve time/requests *inside* the hard limits for active battles."""
        with self.lock:
            if self.battle_started_at is None:
                return False
            battle_start = self.battle_started_at if self.separate_initialization else self.started
            elapsed = time.monotonic() - battle_start
            used = (sum(row.phase != "initialization" for row in self.rows)
                    if self.separate_initialization else len(self.rows))
            remaining = self.args.max_requests - used - self.in_flight
            reserve = getattr(self.args, "drain_requests_per_battle", 0) * (len(self.active_battles) + 1)
            drain_seconds = getattr(self.args, "drain_seconds", 0)
            if (self.stop.is_set() or self.draining.is_set()
                    or elapsed >= self.args.duration_seconds - drain_seconds
                    or remaining < reserve):
                if not self.stop.is_set() and not self.draining.is_set():
                    self.drain_reason = ("time_reserve" if elapsed >= self.args.duration_seconds - drain_seconds
                                         else "request_reserve")
                    self.draining.set()
                return False
            self.active_battles.add(worker)
            self.peak_active_battles = max(self.peak_active_battles, len(self.active_battles))
            return True

    def can_launch_reserved(self, worker: int) -> bool:
        """Recheck after stage preflight, before writing an uncertain battle marker."""
        with self.lock:
            if worker not in self.active_battles:
                return False
            if self.battle_started_at is None:
                return False
            battle_start = self.battle_started_at if self.separate_initialization else self.started
            elapsed = time.monotonic() - battle_start
            drain_seconds = getattr(self.args, "drain_seconds", 0)
            used = (sum(row.phase != "initialization" for row in self.rows)
                    if self.separate_initialization else len(self.rows))
            remaining = self.args.max_requests - used - self.in_flight
            reserve = getattr(self.args, "drain_requests_per_battle", 0) * len(self.active_battles)
            if (self.stop.is_set() or self.draining.is_set()
                    or elapsed >= self.args.duration_seconds - drain_seconds
                    or remaining < reserve or remaining < 1):
                if not self.stop.is_set() and not self.draining.is_set():
                    self.drain_reason = ("time_reserve" if elapsed >= self.args.duration_seconds - drain_seconds
                                         else "request_reserve")
                    self.draining.set()
                return False
            return True

    def leave_battle(self, worker: int, *, interrupted: bool) -> None:
        with self.lock:
            self.active_battles.discard(worker)
            if interrupted and not self.draining.is_set():
                self.drain_reason = "interrupted_battle"
                self.draining.set()

    def initialization_complete(self) -> None:
        with self.lock:
            self.initialization_completed_at = time.monotonic()
            if self.separate_initialization:
                self.battle_started_at = self.initialization_completed_at

    def before_request(self, traffic_phase: str = "normal", path: str = "") -> str:
        with self.lock:
            initialization = self.separate_initialization and traffic_phase == "initialization"
            phase_start = (self.started if initialization or not self.separate_initialization
                           else self.battle_started_at or self.started)
            phase_duration = (self.args.init_duration_seconds if initialization
                              else self.args.duration_seconds)
            phase_limit = (self.args.init_max_requests if initialization else self.args.max_requests)
            phase_rows = (sum(row.phase == "initialization" for row in self.rows)
                          if initialization else
                          sum(row.phase != "initialization" for row in self.rows)
                          if self.separate_initialization else len(self.rows))
            elapsed = time.monotonic() - phase_start
            if self.stop.is_set() or elapsed >= phase_duration:
                self.stop.set()
                raise StopRun("Phase duration or error stop reached")
            if phase_rows + self.in_flight >= phase_limit:
                self.stop.set()
                raise StopRun("Phase request budget reached")
            drain_seconds = getattr(self.args, "drain_seconds", 0)
            if (not self.separate_initialization and traffic_phase == "initialization"
                    and getattr(self.args, "mode", None) == "reuse"
                    and elapsed >= self.args.duration_seconds - drain_seconds):
                self.drain_reason = "initialization_overran_normal_window"
                self.draining.set()
                raise StopRun("Initialization exceeded the normal traffic window")
            if (not initialization and getattr(self.args, "mode", None) == "reuse"
                    and not self.draining.is_set() and drain_seconds > 0
                    and elapsed >= self.args.duration_seconds - drain_seconds):
                self.drain_reason = "time_reserve"
                self.draining.set()
            self.in_flight += 1
            phase = ("initialization" if traffic_phase == "initialization"
                     else "drain" if self.draining.is_set() else "normal")
            scheduled = max(self.next_request, time.monotonic())
            if traffic_phase == "initialization":
                if not path or path.rstrip("/") in SENSITIVE_INITIALIZATION_PATHS:
                    scheduled = max(scheduled, self.next_initialization_request)
                    self.next_initialization_request = scheduled + 1 / getattr(self.args, "init_max_rps", 1)
                else:
                    scheduled = max(scheduled, self.next_general_initialization_request)
                    self.next_general_initialization_request = scheduled + 1 / getattr(self.args, "init_general_rps", self.args.max_rps)
            delay = max(0.0, scheduled - time.monotonic())
            self.next_request = scheduled + 1 / self.args.max_rps
        if self.stop.wait(delay):
            with self.lock:
                self.in_flight -= 1
            raise StopRun("Stopped before scheduled request")
        if time.monotonic() - phase_start >= phase_duration:
            with self.lock:
                self.in_flight -= 1
            self.stop.set()
            raise StopRun("Phase duration reached before scheduled request")
        if (not self.separate_initialization and traffic_phase == "initialization"
                and getattr(self.args, "mode", None) == "reuse"
                and time.monotonic() - self.started >= self.args.duration_seconds - drain_seconds):
            with self.lock:
                self.in_flight -= 1
                self.drain_reason = "initialization_overran_normal_window"
                self.draining.set()
            raise StopRun("Initialization exceeded the normal traffic window")
        return phase

    def record(self, result: RequestResult) -> None:
        with self.lock:
            self.in_flight -= 1
            self.rows.append(result)
            errors = sum(row.category != "ok" for row in self.rows)
            if (getattr(self.args, "mode", None) == "reuse" and result.category != "ok"):
                # An unexpected battle or initialization failure must stop
                # every worker before the next stage can be considered.
                self.stop.set()
            elif result.category in {"timeout", "rate_limit", "capacity", "redirect"}:
                self.stop.set()
            elif len(self.rows) >= 10 and errors / len(self.rows) > self.args.max_error_rate:
                self.stop.set()

    def battle_launched(self) -> None:
        with self.lock:
            self.battle_attempts += 1

    def battle_settled(self, *, result: str) -> None:
        with self.lock:
            self.battle_settlements += 1
            self.battle_victories += int(result == "victory")
            self.battle_defeats += int(result == "defeat")
            self.battle_draws += int(result == "draw")


def classify(status: int, body: object) -> str:
    detail = body.get("detail", {}) if isinstance(body, dict) else {}
    code = detail.get("code", "") if isinstance(detail, dict) else ""
    if 200 <= status < 300:
        return "ok"
    if 300 <= status < 400:
        return "redirect"
    if status == 429:
        return "rate_limit"
    if code == "battleCapacityReached":
        return "capacity"
    if code in {"illegalTargets", "illegalSkill", "invalidCommand", "battleEnded",
                "staleRevision", "notYourTurn", "invalidStageBattleConfiguration"}:
        return "battle_rule"
    return "api_error"


class PlayerClient:
    def __init__(self, worker: int, origin: str, args: argparse.Namespace, budget: RunBudget):
        self.worker = worker
        self.origin = origin
        self.args = args
        self.budget = budget
        self.traffic_phase = "initialization"
        self.sent_requests = 0
        self.cookies = http.cookiejar.CookieJar()
        context = (
            ssl._create_unverified_context() if args.allow_insecure_local_tls
            else ssl.create_default_context(cafile=str(args.ca_file) if args.ca_file else None)
        )
        # Ignore HTTPS_PROXY and friends: a loopback-only run must remain local.
        self.opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(self.cookies), HTTPSHandler(context=context), NoRedirect())
        self.csrf: str | None = None

    def request(self, method: str, path: str, payload: dict | None = None, *, label: str,
                expected_statuses: frozenset[int] = frozenset()) -> dict:
        phase = self.budget.before_request(self.traffic_phase, path)
        data = json.dumps(payload if payload is not None else {}).encode() if method == "POST" else None
        headers = {"Accept": "application/json"}
        if method == "POST":
            headers.update({"Content-Type": "application/json", "Origin": self.origin})
            if self.csrf:
                headers["X-CSRF-Token"] = self.csrf
        request = Request(self.origin + path, data=data, headers=headers, method=method)
        started = time.monotonic()
        status = 0
        body: object = {}
        category = "tool_error"
        body_format = "empty"
        try:
            try:
                self.sent_requests += 1
                response = self.opener.open(request, timeout=self.args.timeout_seconds)
            except HTTPError as exc:
                response = exc
            with response:
                status = response.status
                category = classify(status, {})
                raw = response.read(2_000_000)
                if raw:
                    try:
                        body = json.loads(raw)
                        body_format = "json"
                    except (ValueError, UnicodeDecodeError):
                        body = {}
                        body_format = "non_json"
                        if 200 <= status < 300:
                            category = "tool_error"
                else:
                    body = {}
            if body_format == "json":
                category = classify(status, body)
            if (status in expected_statuses and label == "prior_battle_state"
                    and isinstance(body, dict)
                    and isinstance(body.get("detail"), dict)
                    and body["detail"].get("code") == "battleNoLongerActive"):
                category = "ok"
            if category == "ok" and not isinstance(body, dict):
                category = "tool_error"
            if label == "battle_command" and category == "ok":
                data = body.get("data") if isinstance(body, dict) else None
                if (isinstance(body, dict) and body.get("accepted") is False) or (isinstance(data, dict) and data.get("accepted") is False):
                    category = "battle_rule"
        except (TimeoutError, socket.timeout):
            category = "timeout"
        except URLError as exc:
            category = "timeout" if isinstance(exc.reason, TimeoutError) else "tool_error"
        except (ValueError, OSError):
            category = "tool_error"
        finally:
            self.budget.record(RequestResult(self.worker, label, (time.monotonic() - started) * 1000,
                                             status, category, phase, body_format))
        if category != "ok":
            raise ApiFailure(category, status)
        # Protected writes rotate CSRF along with the HttpOnly session cookie.
        if isinstance(body.get("csrfToken"), str):
            self.csrf = body["csrfToken"]
        else:
            for cookie in self.cookies:
                if cookie.name == "__Host-loct_csrf":
                    self.csrf = cookie.value
        return body


def action_for(snapshot: dict) -> dict:
    if snapshot.get("phase") == "ended":
        raise StopRun("Battle already ended")
    actors = snapshot.get("combatants", {})
    choices = snapshot.get("legalActions", [])
    if not isinstance(actors, dict) or not isinstance(choices, list):
        raise ApiFailure("tool_error")
    def rank(action: dict) -> tuple[int, int]:
        targets = action.get("validTargetIds", [])
        enemies = sum(actors.get(target, {}).get("sideId") == "enemy" for target in targets)
        return (enemies > 0, enemies)
    for action in sorted(choices, key=rank, reverse=True):
        minimum = action.get("minimumTargets")
        targets = action.get("validTargetIds")
        if not isinstance(minimum, int) or not isinstance(targets, list):
            continue
        distinct = list(dict.fromkeys(targets))
        if minimum <= len(distinct):
            return {"actorId": action["actorId"], "skillId": action["skillId"], "targetIds": distinct[:minimum]}
    raise ApiFailure("battle_rule")


def stage_one_available(client: PlayerClient) -> bool:
    stages = client.request("GET", "/api/v1/stages", label="stage_state")
    warrior = next((stage for stage in stages.get("stages", [])
                    if stage.get("stageId") == STAGE_ID), None)
    definition = next((battle for battle in warrior.get("battles", [])
                       if battle.get("displayOrder") == STAGE_INDEX), None) if warrior else None
    return bool(definition and definition.get("unlocked") and definition.get("battleSize") == 2)


def fixed_roster_available(client: PlayerClient, account: dict) -> bool:
    progression = client.request("GET", "/api/v1/progression", label="roster_state")
    return (progression.get("profileId") == account.get("profileId")
            and isinstance(progression.get("unlockedHeroDefinitionIds"), list)
            and set(TEAM).issubset(progression["unlockedHeroDefinitionIds"]))


def fight(client: PlayerClient, pool: PlayerPool, account: dict) -> str | None:
    """Return None when the normal phase closes before a new launch."""
    worker = getattr(client, "worker", threading.get_ident())
    if not client.budget.acquire_battle_slot():
        return None
    try:
        if not client.budget.begin_battle(worker):
            return None
        try:
            return _fight_after_reservation(client, pool, account)
        finally:
            client.budget.leave_battle(
                worker, interrupted=account.get("state") in {"in_flight", "uncertain_launch", "active_battle"}
            )
    finally:
        client.budget.battle_slots.release()


def _fight_after_reservation(client: PlayerClient, pool: PlayerPool, account: dict) -> str | None:
    # This read both rechecks authoritative access and lets the global budget
    # stop cleanly before an account is marked as a possibly launched battle.
    if not stage_one_available(client):
        raise ApiFailure("battle_rule")
    worker = getattr(client, "worker", threading.get_ident())
    if not client.budget.can_launch_reserved(worker):
        return None
    # Keep the previous Battle ID until the new launch is confirmed. A lost
    # response must remain visibly uncertain and cannot trigger a retry.
    attempt_id = f"load-{uuid.uuid4().hex}"
    pool.update(account, state="uncertain_launch", pendingAttemptId=attempt_id)
    launched = client.request("POST", f"/api/v1/stages/{STAGE_ID}/battles/{STAGE_INDEX}", {
        "playerTeam": list(TEAM), "playerFormation": FORMATION, "mode": "learner",
        "attemptId": attempt_id,
    }, label="stage_launch")
    battle_id = launched["battleId"]
    pool.update(account, state="active_battle", previousBattleId=account.get("battleId"),
                battleId=battle_id, pendingAttemptId=None)
    client.budget.battle_launched()
    envelope = launched
    for _ in range(client.args.max_commands_per_battle):
        if envelope.get("lifecycleStatus") == "settled":
            receipt = envelope.get("settlement")
            if not isinstance(receipt, dict):
                raise ApiFailure("tool_error")
            outcome = receipt.get("outcome")
            if not isinstance(outcome, dict):
                raise ApiFailure("tool_error")
            if outcome.get("kind") == "victory" and outcome.get("winningSideId") == "friendly":
                result = "victory"
            elif outcome.get("kind") == "victory" and outcome.get("winningSideId") == "enemy":
                result = "defeat"
            elif outcome.get("kind") == "draw":
                result = "draw"
            else:
                raise ApiFailure("tool_error")
            client.budget.battle_settled(result=result)
            pool.update(account, state="ready", battleId=battle_id, pendingAttemptId=None)
            return result
        data = envelope.get("data")
        snapshot = data.get("snapshot") if isinstance(data, dict) else None
        if not isinstance(snapshot, dict):
            envelope = client.request("GET", f"/api/v1/battles/{battle_id}", label="battle_state")
            continue
        if snapshot.get("phase") == "ended":
            # A terminal command should return a durable settlement. Never
            # fabricate completion from snapshot state alone.
            envelope = client.request("GET", f"/api/v1/battles/{battle_id}", label="battle_state")
            continue
        if not snapshot.get("turnControl", {}).get("acceptsCommands"):
            envelope = client.request("GET", f"/api/v1/battles/{battle_id}", label="battle_state")
            continue
        command = action_for(snapshot)
        command.update({"type": "useSkill", "commandId": f"load-{uuid.uuid4().hex}", "expectedRevision": envelope["revision"]})
        envelope = client.request("POST", f"/api/v1/battles/{battle_id}/commands", command, label="battle_command")
    raise StopRun("Per-battle command budget reached")


def recover_account(client: PlayerClient, account: dict, pool: PlayerPool,
                    *, allow_empty_slot: bool = False) -> bool:
    recovered = client.request("POST", "/api/v1/sessions/recover", {
        "recoveryCode": account["recoveryCode"],
    }, label="player_recover")
    if recovered.get("playerId") != account["playerId"]:
        raise ApiFailure("tool_error")
    if not recovered.get("recoveryConfirmed"):
        client.request("POST", "/api/v1/recovery-code/acknowledge", {}, label="recovery_ack")
    slots = client.request("GET", "/api/v1/save-slots", label="slot_state")
    owned = next((item for item in slots.get("slots", []) if item.get("slotId") == 1), None)
    if not owned:
        raise ApiFailure("tool_error")
    if owned.get("occupied"):
        if account.get("profileId") not in {None, owned.get("profileId")}:
            raise ApiFailure("tool_error")
        loaded = client.request("POST", "/api/v1/save-slots/1/load", {}, label="slot_load")
        if loaded.get("slot", {}).get("profileId") != owned["profileId"]:
            raise ApiFailure("tool_error")
        if account.get("profileId") is None:
            pool.update(account, profileId=owned["profileId"])
    elif not allow_empty_slot or account.get("profileId") is not None:
        raise ApiFailure("tool_error")
    # Recovery revokes the prior session and invalidates its active battles.
    # An in-flight manifest is never recovered implicitly by reuse mode.
    if account.get("battleId"):
        old = account["battleId"]
        prior = client.request("GET", f"/api/v1/battles/{old}",
                               label="prior_battle_state", expected_statuses=frozenset({409}))
        if prior.get("detail", {}).get("code") != "battleNoLongerActive":
            raise ApiFailure("tool_error")
    return bool(owned.get("occupied"))


def provision_player(worker: int, origin: str, args: argparse.Namespace, budget: RunBudget,
                     pool: PlayerPool, account: dict | None) -> dict:
    """Enroll and verify an account/slot; never enter the battle API."""
    outcome = {"worker": worker, "provisioned": False, "reason": "",
               "player_id": None, "profile_id": None}
    new_enrollment = account is None
    try:
        if budget.stop.is_set():
            raise StopRun("Stopped before enrollment")
        client = PlayerClient(worker, origin, args, budget)
        if account is None:
            reservation = pool.reserve_next_player()
            created = client.request("POST", "/api/v1/players", {
                "playerName": reservation["playerName"],
            }, label="player_create")
            code = created.get("recoveryCode")
            player_id = created.get("playerId")
            if not isinstance(code, str) or not code or not isinstance(player_id, str) or not player_id:
                raise ApiFailure("tool_error")
            if any(item is not reservation and
                   (item.get("playerId") == player_id or item.get("recoveryCode") == code)
                   for item in pool.data["accounts"]):
                raise ApiFailure("tool_error")
            # Replace the reservation with the one-time code before any
            # subsequent network request. An uncertain enrollment stays marked.
            pool.update(reservation, playerId=player_id, recoveryCode=code,
                        profileId=None, state="provisioning", battleId=None,
                        reservationId=None)
            account = reservation
            outcome["player_id"] = account["playerId"]
            client.request("POST", "/api/v1/recovery-code/acknowledge", {}, label="recovery_ack")
            slot = client.request("POST", "/api/v1/save-slots/1/create", {}, label="slot_create")
            pool.update(account, profileId=slot["slot"]["profileId"])
            outcome["profile_id"] = account["profileId"]
        else:
            if account.get("state") != "provisioning":
                raise ApiFailure("tool_error")
            outcome["player_id"] = account["playerId"]
            slot_exists = recover_account(client, account, pool, allow_empty_slot=True)
            if not slot_exists:
                slot = client.request("POST", "/api/v1/save-slots/1/create", {}, label="slot_create")
                pool.update(account, profileId=slot["slot"]["profileId"])
            outcome["profile_id"] = account["profileId"]
        # New enrollments must also prove the saved one-time code recovers the
        # same Player ID and owns the just-created slot before becoming ready.
        if new_enrollment:
            recover_account(client, account, pool)
        if not fixed_roster_available(client, account):
            outcome["reason"] = "required_hero_missing_or_profile_mismatch"
            raise ApiFailure("battle_rule")
        if not stage_one_available(client):
            outcome["reason"] = "stage_one_unavailable"
            raise ApiFailure("battle_rule")
        pool.update(account, state="ready")
        outcome["provisioned"] = True
    except (ApiFailure, StopRun, KeyError, TypeError) as exc:
        outcome["reason"] = outcome["reason"] or (
            exc.category if isinstance(exc, ApiFailure) else type(exc).__name__
        )
    except Exception:
        # Never print an unexpected exception: a library may include request
        # headers, cookies, or a response body in its message.
        outcome["reason"] = "tool_error"
    if outcome["reason"]:
        budget.stop.set()
    return outcome


def run_player(worker: int, origin: str, args: argparse.Namespace, budget: RunBudget,
               pool: PlayerPool, account: dict | None,
               initialization_barrier: threading.Barrier | None = None) -> dict:
    """Reuse a ready, recovery-verified account for battles only."""
    outcome = {"worker": worker, "battles_settled": 0, "reason": "",
               "player_id": None, "profile_id": None}
    initialized = False
    client: PlayerClient | None = None
    try:
        if args.mode != "reuse" or account is None or account.get("state") != "ready":
            raise ApiFailure("tool_error")
        outcome["player_id"] = account["playerId"]
        outcome["profile_id"] = account["profileId"]
        with budget.initialization_slots:
            if budget.stop.is_set():
                raise StopRun("Stopped before initialization")
            client = PlayerClient(worker, origin, args, budget)
            pool.update(account, state="initializing")
            recover_account(client, account, pool)
            if not fixed_roster_available(client, account):
                outcome["reason"] = "required_hero_missing_or_profile_mismatch"
                raise ApiFailure("battle_rule")
            if not stage_one_available(client):
                outcome["reason"] = "stage_one_unavailable"
                raise ApiFailure("battle_rule")
            pool.update(account, state="ready")
            with budget.lock:
                budget.initialized_workers += 1
            initialized = True
        if initialization_barrier is not None:
            if budget.stop.is_set():
                raise StopRun("Initialization stopped before battle phase")
            remaining = ((args.init_duration_seconds if budget.separate_initialization
                          else args.duration_seconds - getattr(args, "drain_seconds", 0))
                         - (time.monotonic() - budget.started))
            initialization_barrier.wait(timeout=max(0, remaining))
        client.traffic_phase = "normal"
        for _ in range(args.max_stage_attempts):
            result = fight(client, pool, account)
            if result is None:
                outcome["reason"] = "graceful_stop"
                break
            outcome["battles_settled"] += 1
    except (ApiFailure, StopRun, KeyError, TypeError) as exc:
        outcome["reason"] = outcome["reason"] or (
            exc.category if isinstance(exc, ApiFailure) else type(exc).__name__
        )
    except threading.BrokenBarrierError:
        outcome["reason"] = "initialization_aborted"
        budget.stop.set()
    except Exception:
        outcome["reason"] = "tool_error"
    finally:
        if not initialized:
            budget.stop.set()
        if account is not None and not initialized and account.get("state") == "initializing":
            contacted = (bool(getattr(client, "sent_requests", 0))
                         or any(row.worker == worker for row in budget.rows))
            pool.update(account, state="requires_reconciliation" if contacted else "ready")
        if initialization_barrier is not None and not initialized:
            initialization_barrier.abort()
    return outcome


def reconcile_player(worker: int, origin: str, args: argparse.Namespace,
                     budget: RunBudget, pool: PlayerPool, account: dict) -> bool:
    """Explicitly revoke an interrupted test session/battle, then inspect slot."""
    try:
        client = PlayerClient(worker, origin, args, budget)
        slot_exists = recover_account(client, account, pool, allow_empty_slot=True)
        ready = slot_exists and fixed_roster_available(client, account) and stage_one_available(client)
        if not ready:
            return False
        pool.update(account, state="ready", resolvedAttemptId=account.get("pendingAttemptId"),
                    pendingAttemptId=None)
        return True
    except Exception:
        # Preserve the pending marker and secret for an operator to inspect.
        return False


def percentile95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(.95 * len(ordered)) - 1)]


def summary(rows: list[RequestResult], outcomes: list[dict], elapsed: float,
            budget: RunBudget | None = None) -> dict:
    """Count each attempted request once, separating transport and operation results.

    successful_requests is the legacy HTTP-2xx count, including a rejected
    2xx command. counts.ok accepts expected non-2xx responses (notably a 409
    battleNoLongerActive during recovery). error_rate uses operation categories.
    """
    counts = {kind: sum(row.category == kind for row in rows) for kind in (
        "ok", "api_error", "rate_limit", "battle_rule", "capacity", "timeout", "redirect", "tool_error")}
    latencies = [row.latency_ms for row in rows]
    battle_rows = [row for row in rows if row.phase != "initialization"]
    battle_seconds = ((time.monotonic() - budget.battle_started_at)
                      if budget and budget.battle_started_at is not None else 0)
    return {
        "requests": len(rows), "counts": counts,
        "successful_requests": sum(200 <= row.status < 300 for row in rows),
        "http_successful_requests": sum(200 <= row.status < 300 for row in rows),
        "operation_ok_requests": counts["ok"],
        "expected_non_2xx_ok": sum(row.category == "ok" and not 200 <= row.status < 300
                                    for row in rows),
        "http_2xx_operation_failures": sum(200 <= row.status < 300 and row.category != "ok"
                                           for row in rows),
        "http_responses": sum(row.status > 0 for row in rows),
        "non_json_responses": sum(row.body_format == "non_json" for row in rows),
        "http_non_2xx_responses": sum(row.status > 0 and not 200 <= row.status < 300
                                      for row in rows),
        "no_http_response_requests": sum(row.status == 0 for row in rows),
        "normal_requests": sum(row.phase == "normal" for row in rows),
        "initialization_requests": sum(row.phase == "initialization" for row in rows),
        "initialization_errors": sum(row.phase == "initialization" and row.category != "ok"
                                     for row in rows),
        "drain_requests": sum(row.phase == "drain" for row in rows),
        "battle_phase_requests": len(battle_rows),
        "battle_phase_seconds": round(battle_seconds, 2),
        "battle_average_ms": round(statistics.mean(row.latency_ms for row in battle_rows), 2)
        if battle_rows else 0,
        "battle_p95_ms": round(percentile95([row.latency_ms for row in battle_rows]), 2),
        "battle_requests_per_second": round(len(battle_rows) / battle_seconds, 2)
        if battle_seconds else 0,
        "battle_phase_errors": sum(row.category != "ok" for row in battle_rows),
        "http_429": sum(row.status == 429 for row in rows),
        "average_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "p95_ms": round(percentile95(latencies), 2),
        "requests_per_second": round(len(rows) / elapsed, 2) if elapsed else 0,
        "error_rate": round((len(rows) - counts["ok"]) / len(rows), 4) if rows else 0,
        "timeout_rate": round(counts["timeout"] / len(rows), 4) if rows else 0,
        "workers_with_completed_battles": sum(item.get("battles_settled", 0) > 0 for item in outcomes),
        "workers_stopped_by_budget": sum(item.get("reason") in {"StopRun", "graceful_stop"}
                                         for item in outcomes),
        "workers_gracefully_stopped": sum(item.get("reason") == "graceful_stop"
                                          for item in outcomes),
        "drain_reason": budget.drain_reason if budget else None,
        "workers_initialized": budget.initialized_workers if budget else 0,
        "initialization_seconds": round(
            (budget.initialization_completed_at or time.monotonic()) - budget.started, 2
        ) if budget else 0,
        "worker_error_reasons": {
            reason: sum(item.get("reason") == reason for item in outcomes)
            for reason in ("api_error", "rate_limit", "battle_rule", "capacity", "timeout", "redirect", "tool_error", "KeyError", "TypeError", "initialization_aborted",
                           "required_hero_missing_or_profile_mismatch", "stage_one_unavailable")
            if any(item.get("reason") == reason for item in outcomes)
        },
        "battle_attempts": budget.battle_attempts if budget else 0,
        "peak_client_active_battles": budget.peak_active_battles if budget else 0,
        "settled_battles": budget.battle_settlements if budget else 0,
        "battle_victories": budget.battle_victories if budget else 0,
        "completed_battles": budget.battle_settlements if budget else 0,
        "unfinished_battles": (budget.battle_attempts - budget.battle_settlements) if budget else 0,
        "two_v_two_started": budget.battle_attempts if budget else 0,
        "two_v_two_settled": budget.battle_settlements if budget else 0,
        "two_v_two_victories": budget.battle_victories if budget else 0,
        "two_v_two_defeats": budget.battle_defeats if budget else 0,
        "two_v_two_draws": budget.battle_draws if budget else 0,
        "battles_per_minute": round(budget.battle_settlements * 60 / elapsed, 2)
        if budget and elapsed else 0,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--mode", choices=("provision", "create", "reuse", "reconcile", "inspect"),
                        default="create", help="create is a legacy alias for provision; neither runs battles")
    result.add_argument("--pool-file", type=Path, help="Absolute path in a private 0700 directory outside Git")
    result.add_argument("--base-url", default="https://127.0.0.1:8443")
    result.add_argument("--players", "--concurrency", dest="players", type=int, default=2)
    result.add_argument("--pool-size", type=int,
                        help="Provision target total accounts; defaults to --concurrency")
    result.add_argument("--timeout-seconds", type=float, default=10)
    result.add_argument("--duration-seconds", type=float, default=120)
    result.add_argument("--max-rps", type=float, default=2)
    result.add_argument("--init-max-rps", type=float, default=0.1,
                        help="Shared sensitive-endpoint initialization cap, in addition to --max-rps")
    result.add_argument("--init-general-rps", type=float, default=2,
                        help="Shared general-endpoint initialization cap, in addition to --max-rps")
    result.add_argument("--init-concurrency", type=int, default=2,
                        help="Maximum accounts simultaneously performing initialization/recovery")
    result.add_argument("--max-active-battles", type=int, default=20,
                        help="Client-side cap on simultaneous battles; excess player workers wait")
    result.add_argument("--init-duration-seconds", type=float, default=600,
                        help="Reuse only: hard pre-initialization timeout before the battle clock starts")
    result.add_argument("--init-max-requests", type=int, default=200,
                        help="Reuse only: hard pre-initialization request budget")
    result.add_argument("--max-requests", type=int, default=500)
    result.add_argument("--drain-seconds", type=float, default=60,
                        help="Reuse only: reserve this time within --duration-seconds to finish active battles")
    result.add_argument("--drain-requests-per-battle", type=int, default=12,
                        help="Reuse only: request headroom per active or proposed battle; --max-requests remains hard")
    result.add_argument("--max-error-rate", type=float, default=.2)
    result.add_argument("--max-commands-per-battle", type=int, default=120)
    result.add_argument("--max-battles-per-player", "--max-stage-attempts",
                        dest="max_stage_attempts", type=int, default=100,
                        help="Additional per-worker battle cap within the global request/time budgets")
    result.add_argument("--csv", type=Path)
    result.add_argument("--execute", action="store_true", help="Make write requests; omitted by default")
    result.add_argument("--allow-production", action="store_true")
    result.add_argument("--owner-authorization", default="")
    result.add_argument("--confirm-reconcile", default="",
                        help="Explicitly acknowledge that recovery abandons unfinished test battles")
    result.add_argument("--reconcile-rows", default="",
                        help="Required 1-based comma-separated in_flight pool rows for reconciliation")
    result.add_argument("--allow-insecure-local-tls", action="store_true")
    result.add_argument("--ca-file", type=Path, help="Trusted CA for an isolated HTTPS server")
    return result


def parse_reconcile_rows(value: str) -> tuple[int, ...]:
    parts = [part.strip() for part in value.split(",")]
    if not value or any(not part.isascii() or not part.isdecimal() for part in parts):
        raise ValueError("--reconcile-rows requires explicit 1-based row numbers")
    rows = tuple(int(part) for part in parts)
    if any(row < 1 or row > 100 for row in rows) or len(rows) != len(set(rows)):
        raise ValueError("--reconcile-rows must contain distinct pool rows 1–100")
    return rows


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if (args.players < 1 or args.players > 100 or
            args.pool_size is not None and not 1 <= args.pool_size <= 100 or
            args.max_requests < 1 or args.init_max_requests < 1 or
            args.max_rps <= 0 or args.init_max_rps <= 0 or args.init_general_rps <= 0 or
            args.init_duration_seconds <= 0 or
            args.init_concurrency < 1 or args.init_concurrency > 100 or
            args.max_active_battles < 1 or args.max_active_battles > 30 or
            args.duration_seconds <= 0 or
            args.drain_seconds < 0 or args.drain_requests_per_battle < 0 or
            args.timeout_seconds <= 0 or not 0 <= args.max_error_rate <= 1 or
            args.max_commands_per_battle < 1 or args.max_stage_attempts < 1):
        raise SystemExit("Invalid limits: players 1–100; all budgets positive; error rate 0–1")
    if args.mode == "reuse" and args.drain_seconds >= args.duration_seconds:
        raise SystemExit("--drain-seconds must be less than --duration-seconds in reuse mode")
    if args.pool_size is not None and args.mode not in {"provision", "create"}:
        raise SystemExit("--pool-size applies only to --mode provision")
    if args.mode == "inspect" and args.execute:
        raise SystemExit("Inspection is read-only; do not pass --execute")
    if args.mode != "reconcile" and args.reconcile_rows:
        raise SystemExit("--reconcile-rows applies only to --mode reconcile")
    try:
        origin, local = validate_target(args)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.csv and args.csv.exists():
        raise SystemExit("CSV path already exists; refusing to overwrite it")
    if args.mode == "reconcile" and args.confirm_reconcile != RECONCILE_CONFIRMATION:
        raise SystemExit("Reconciliation requires explicit interrupted-battle confirmation")
    try:
        reconcile_rows = parse_reconcile_rows(args.reconcile_rows) if args.mode == "reconcile" else ()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if args.mode == "inspect":
        if args.pool_file is None:
            raise SystemExit("Inspection requires --pool-file")
        try:
            report = PlayerPool(args.pool_file, origin, create=False).inspect(args.players)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            raise SystemExit(str(exc)) from exc
        print(json.dumps(report, sort_keys=True))
        return 0
    if not args.execute:
        print(json.dumps({"mode": "DRY_RUN_ZERO_REQUESTS", "account_mode": args.mode,
                          "origin": origin, "players": args.players,
                          "scenario": {"stageId": STAGE_ID, "battleIndex": STAGE_INDEX,
                                       "battleSize": 2, "playerTeam": TEAM,
                                       "playerFormation": FORMATION},
                          "pool_size": args.pool_size,
                          "max_requests": args.max_requests, "max_rps": args.max_rps,
                          "init_max_rps": args.init_max_rps,
                          "init_general_rps": args.init_general_rps,
                          "init_duration_seconds": args.init_duration_seconds,
                          "init_max_requests": args.init_max_requests,
                          "init_concurrency": args.init_concurrency,
                          "max_active_battles": args.max_active_battles,
                          "drain_seconds": args.drain_seconds,
                          "drain_requests_per_battle": args.drain_requests_per_battle,
                          "duration_seconds": args.duration_seconds, "local": local}, sort_keys=True))
        return 0
    if args.pool_file is None:
        raise SystemExit("Executed runs require --pool-file in a private directory outside Git")
    try:
        with PlayerPool(args.pool_file, origin, create=args.mode in {"provision", "create"}) as player_pool:
            accounts = player_pool.data["accounts"]
            if args.mode in {"provision", "create"}:
                target_size = args.pool_size if args.pool_size is not None else args.players
                if any(item.get("state") == "enrollment_pending" for item in accounts):
                    raise ValueError("Enrollment outcome is uncertain; inspect the pool and database before any replacement")
                if any(item.get("state") in {"in_flight", "initializing", "requires_reconciliation",
                                             "uncertain_launch", "active_battle"} for item in accounts):
                    raise ValueError("Pool has interrupted accounts; reconcile before expansion")
                provisioning = [item for item in accounts if item.get("state") == "provisioning"]
                if len(accounts) > target_size:
                    raise ValueError("Pool exceeds requested target; choose a larger --pool-size")
                if provisioning:
                    # Resume these identities first. Never mask a failed
                    # recovery by creating extra replacement players.
                    selected: list[dict | None] = provisioning[:args.players]
                elif len(accounts) >= target_size:
                    selected = []
                else:
                    selected = [None] * (target_size - len(accounts))
            elif args.mode == "reuse":
                eligible = [item for item in accounts if item.get("state") == "ready"
                            and item.get("playerId") and item.get("recoveryCode")
                            and item.get("profileId")]
                if len(eligible) < args.players:
                    raise ValueError("Not enough ready credentialed accounts; provision or reconcile first")
                selected = eligible[:args.players]
            else:
                if len(reconcile_rows) != args.players:
                    raise ValueError("--concurrency must equal the number of explicitly selected reconciliation rows")
                if any(row > len(accounts) for row in reconcile_rows):
                    raise ValueError("A selected reconciliation row is outside the pool")
                selected = [accounts[row - 1] for row in reconcile_rows]
                if any(item.get("state") not in {"in_flight", "initializing", "requires_reconciliation",
                                                    "uncertain_launch", "active_battle"}
                       or not isinstance(item.get("playerId"), str) or not item["playerId"]
                       or not isinstance(item.get("recoveryCode"), str) or not item["recoveryCode"]
                       for item in selected):
                    raise ValueError("Only credentialed interrupted accounts may be reconciled")
            budget = RunBudget(args)
            if not selected:
                print(json.dumps({"account_mode": "provision", "pool_total": len(accounts),
                                  "accounts_attempted": 0, "accounts_provisioned": 0,
                                  "requests": 0, "battles_started": 0}, sort_keys=True))
                return 0
            with ThreadPoolExecutor(max_workers=min(args.players, len(selected))) as executor:
                if args.mode == "reconcile":
                    outcomes = list(executor.map(
                        lambda pair: reconcile_player(pair[0], origin, args, budget, player_pool, pair[1]),
                        enumerate(selected),
                    ))
                    report = {"reconciled_ready": sum(outcomes),
                              "still_provisioning_or_failed": len(outcomes) - sum(outcomes),
                              "rowResults": [{"row": row, "status": "ready" if ok else "failed_kept_interrupted"}
                                             for row, ok in zip(reconcile_rows, outcomes)],
                              "pendingEnrollmentsUntouched": sum(
                                  item.get("state") == "enrollment_pending" for item in accounts),
                              "requests": len(budget.rows),
                              "counts": summary(budget.rows, [], time.monotonic() - budget.started)["counts"]}
                    print(json.dumps(report, sort_keys=True))
                    return 0 if all(outcomes) else 1
                worker_function = provision_player if args.mode in {"provision", "create"} else run_player
                barrier = (threading.Barrier(len(selected), action=budget.initialization_complete)
                           if args.mode == "reuse" else None)
                futures = [executor.submit(worker_function, worker, origin, args, budget,
                                           player_pool, account, barrier)
                           if barrier is not None else
                           executor.submit(worker_function, worker, origin, args, budget,
                                           player_pool, account)
                           for worker, account in enumerate(selected)]
                outcomes = [future.result() for future in as_completed(futures)]
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    for key in ("player_id", "profile_id"):
        present = [item[key] for item in outcomes if item[key] is not None]
        if len(present) != len(set(present)):
            raise RuntimeError("Independent player/profile identity invariant failed")
    elapsed = time.monotonic() - budget.started
    report = summary(budget.rows, outcomes, elapsed, budget)
    if args.mode in {"provision", "create"}:
        report.update({"account_mode": "provision", "pool_total": len(player_pool.data["accounts"]),
                       "accounts_attempted": len(selected),
                       "accounts_provisioned": sum(item["provisioned"] for item in outcomes),
                       "concurrency_limit": args.players})
        print(json.dumps(report, sort_keys=True))
        return 0 if (report["accounts_provisioned"] == len(selected)
                     and not report["worker_error_reasons"]) else 1
    interrupted_states = {"in_flight", "initializing", "requires_reconciliation",
                          "uncertain_launch", "active_battle"}
    pending = sum(account is not None and account.get("state") in interrupted_states
                  for account in selected)
    active = sum(account is not None and account.get("state") == "active_battle"
                 for account in selected)
    uncertain = sum(account is not None and account.get("state") == "uncertain_launch"
                    for account in selected)
    # Initialization markers need verification but are not battle attempts.
    # A launch without a response remains uncertain, not confirmed active.
    report["accounts_pending_reconciliation"] = pending
    report["accounts_requiring_verification"] = pending
    report["last_confirmed_active_battles"] = active
    report["uncertain_launches"] = uncertain
    report["actual_server_active_battles"] = None
    report["unfinished_battles"] = max(report["unfinished_battles"], active + uncertain)
    report.update({"account_mode": args.mode, "pool_total": len(player_pool.data["accounts"]),
                   "accounts_attempted": len(selected), "concurrency_limit": args.players,
                   "init_max_rps": args.init_max_rps,
                   "init_general_rps": args.init_general_rps,
                   "init_duration_seconds": args.init_duration_seconds,
                   "init_max_requests": args.init_max_requests,
                   "init_concurrency": args.init_concurrency,
                   "max_active_battles": args.max_active_battles,
                   "drain_seconds": args.drain_seconds,
                   "drain_requests_per_battle": args.drain_requests_per_battle})
    print(json.dumps(report, sort_keys=True))
    if args.csv:
        with args.csv.open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("worker", "endpoint", "latency_ms", "http_status", "category"))
            for row in budget.rows:
                writer.writerow((row.worker, row.endpoint, f"{row.latency_ms:.2f}", row.status, row.category))
    return 0 if (report["workers_with_completed_battles"] == len(selected)
                 and report["unfinished_battles"] == 0
                 and report["accounts_pending_reconciliation"] == 0
                 and not report["worker_error_reasons"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
