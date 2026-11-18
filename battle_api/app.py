"""Small async FastAPI transport for the process-local battle registry."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import os
from pathlib import Path
import secrets
import threading
from typing import Annotated
import uuid

from fastapi import Depends, FastAPI, HTTPException, Path as ApiPath, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .adapter import CONTRACT_VERSION, BattleAdapterError, BattleRegistry
from .attempts import BattleAttemptConflict, BattleAttemptRegistry
from .debug_routes import create_debug_router
from game.formation_rules import formation_demonstration_catalogue
from .models import (
    ArenaStateResponse,
    ArenaVictoryCommitResponse,
    BattlePreviewRequest,
    BattlePreviewResponse,
    ConfirmSaveSlotOverwriteRequest,
    CreateArenaBattleRequest,
    CreateArenaRunRequest,
    CreateBattleRequest,
    CreatePlayerRequest,
    CreateStageBattleRequest,
    EmptySaveSlotRequest,
    EmptyAuthenticatedRequest,
    FormationDemonstrationResponse,
    HeroRosterResponse,
    HttpErrorResponse,
    PlayerProgressionResponse,
    PlayerSessionResponse,
    RecoverPlayerRequest,
    RecoveryCodeReplacementResponse,
    RetryableHttpErrorResponse,
    SaveSlotActionResponse,
    SaveSlotListResponse,
    StageId,
    StructuredStagesResponse,
    UseSkillCommand,
    VictoryCommitResponse,
)
from .progression import (
    ArenaAccessError,
    ProgressionStore,
    ProgressionStoreError,
    PublicBattleAccessError,
    SaveSlotAccessError,
    StageAccessError,
    hero_unlock_sources,
    stages_response,
)
from .public_identity import (
    AuthenticatedSession,
    IssuedIdentity,
    PublicIdentityError,
    PublicIdentityService,
    canonical_client_ip,
)
from .public_config import PublicConfigurationError, validate_public_configuration
from .release_mode import engineering_enabled

app = FastAPI(title="Legends of Champions Tactics Battle API", version="1.0.0")

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)


def _cors_origins() -> list[str]:
    if not engineering_enabled():
        origin = os.getenv("BATTLE_API_PUBLIC_ORIGIN")
        return [origin] if origin else []
    configured = os.getenv("BATTLE_API_CORS_ORIGINS")
    if configured is None:
        return list(DEFAULT_CORS_ORIGINS)
    return [
        origin.strip()
        for origin in configured.split(",")
        if origin.strip() and origin.strip() != "*"
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=not engineering_enabled(),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
registry = BattleRegistry()
battle_attempt_registry = BattleAttemptRegistry()
_player_battle_locks: dict[str, threading.RLock] = {}
_player_battle_locks_guard = threading.Lock()
DEFAULT_PROGRESSION_DATABASE = (
    Path(__file__).resolve().parents[1] / "data" / "player_progression.sqlite3"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _configured_progression_store() -> ProgressionStore | None:
    if engineering_enabled():
        return ProgressionStore(
            Path(os.getenv("BATTLE_API_PROGRESSION_DB", DEFAULT_PROGRESSION_DATABASE))
        )
    configured = os.getenv("BATTLE_API_PUBLIC_DB")
    if not configured:
        return None
    path = Path(configured)
    if not path.is_absolute():
        return None
    resolved = path.resolve(strict=False)
    if resolved == REPOSITORY_ROOT or REPOSITORY_ROOT in resolved.parents:
        return None
    return ProgressionStore(
        resolved,
        public_mode=True,
        allow_public_initialize=False,
    )


progression_store = _configured_progression_store()


def _configured_identity_service() -> PublicIdentityService | None:
    if engineering_enabled() or progression_store is None:
        return None
    try:
        validate_public_configuration()
    except PublicConfigurationError:
        return None
    key = os.getenv("BATTLE_API_PUBLIC_HMAC_KEY")
    rate_key = os.getenv("BATTLE_API_RATE_LIMIT_HMAC_KEY")
    # validate_public_configuration has already established both independent
    # values and their minimum lengths; retain defensive guards for typing.
    if key is None or rate_key is None:
        return None
    return PublicIdentityService(
        progression_store,
        key=key.encode("utf-8"),
        key_version=int(os.getenv("BATTLE_API_PUBLIC_HMAC_KEY_VERSION", "1")),
        rate_limit_key=rate_key.encode("utf-8"),
    )


identity_service = _configured_identity_service()


def _player_battle_lock(player_id: str) -> threading.RLock:
    with _player_battle_locks_guard:
        return _player_battle_locks.setdefault(player_id, threading.RLock())


def _remove_process_battle(battle_id: str) -> None:
    registry.remove(battle_id)
    battle_attempt_registry.remove_battle(battle_id)


def _cleanup_expired_process_battles(battle_ids: list[str]) -> None:
    for battle_id in battle_ids:
        _remove_process_battle(battle_id)


def _invalidate_public_player_battles(
    store: ProgressionStore,
    *,
    player_id: str,
    reason: str,
) -> None:
    """End unfinished battle authority and evict only ended RAM sessions."""

    battle_ids = store.invalidate_player_battles_after_revocation(
        player_id=player_id,
        reason=reason,
    )
    _cleanup_expired_process_battles(battle_ids)


def _retry_public_terminal_pending(
    store: ProgressionStore,
    *,
    session: AuthenticatedSession | IssuedIdentity,
) -> dict | None:
    """Finish an already recorded outcome before owner context is revoked."""

    pending = store.public_terminal_pending_battle(
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    if pending is None:
        return None
    settlement = store.settle_public_battle(
        battle_id=pending["battleId"],
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
        outcome=pending["outcome"],
    )
    _remove_process_battle(pending["battleId"])
    return settlement

if engineering_enabled():
    app.include_router(create_debug_router(registry))


def get_progression_store() -> ProgressionStore:
    if progression_store is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "publicStoreNotConfigured",
                "message": "Public player storage is not configured.",
                "retryable": False,
            },
        )
    return progression_store


def get_identity_service() -> PublicIdentityService:
    if identity_service is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "publicIdentityNotConfigured",
                "message": "Public player identity is not configured.",
                "retryable": False,
            },
        )
    return identity_service


def get_optional_identity_service() -> PublicIdentityService | None:
    if engineering_enabled():
        return None
    return get_identity_service()


def _store_unavailable(exc: ProgressionStoreError) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "code": "progressionStoreUnavailable",
            "message": str(exc),
            "retryable": True,
        },
    )


def _access_error(exc: StageAccessError) -> HTTPException:
    status = 404 if exc.code in {"stageNotFound", "stageBattleNotFound"} else 409
    return HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": exc.message},
    )


def _save_slot_error(exc: SaveSlotAccessError) -> HTTPException:
    if exc.code in {"authenticationRequired", "sessionRevoked", "sessionExpired"}:
        status = 401
    elif exc.code == "recoveryConfirmationRequired":
        status = 403
    else:
        status = 422 if exc.code == "invalidSaveSlot" else 409
    return HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": exc.message},
    )


def _arena_error(exc: ArenaAccessError) -> HTTPException:
    status = 404 if exc.code in {"arenaRunNotFound", "arenaNodeNotFound"} else 409
    return HTTPException(
        status_code=status,
        detail={"code": exc.code, "message": exc.message},
    )


def _battle_attempt_error(exc: BattleAttemptConflict) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={"code": "battleAttemptConflict", "message": str(exc)},
    )


def _public_battle_error(exc: PublicBattleAccessError) -> HTTPException:
    if exc.code == "battleNotFound":
        status = 404
    elif exc.code in {"battleCapacityReached"}:
        status = 503
    else:
        status = 409
    return HTTPException(
        status_code=status,
        detail={
            "code": exc.code,
            "message": exc.message,
            **({"retryable": True} if status == 503 else {}),
        },
    )


def _fresh_battle_seed() -> int:
    """Return server-owned entropy for one new player-facing attempt."""

    return secrets.randbits(256)


def _public_lifecycle_fields(store: ProgressionStore, record: dict) -> dict:
    return {
        "serverNow": store._timestamp(),
        "expiresAt": record.get("expiresAt"),
        "lifecycleStatus": record.get("lifecycleStatus"),
        "terminalReason": record.get("terminalReason"),
        "settlementStatus": (
            "settled" if record.get("settlementAt") else
            "pending" if record.get("lifecycleStatus") == "terminalPending" else
            "none"
        ),
    }


def _strip_public_seed_fields(envelope: dict) -> None:
    """Never expose server-owned combat entropy through a Public envelope."""

    envelope.pop("seed", None)
    envelope.pop("seedHex", None)
    data = envelope.get("data")
    if isinstance(data, dict):
        data.pop("seed", None)
        data.pop("seedHex", None)


def _public_launch(
    *,
    session: AuthenticatedSession,
    store: ProgressionStore,
    attempt_id: str | None,
    fingerprint: tuple,
    battle_type: str,
    context: dict,
    factory: Callable[[int, str, str], tuple[object, dict]],
) -> tuple[object, dict]:
    """Reserve, construct, activate, then expose one Public battle."""
    with _player_battle_lock(session.player_id):
        binding = store.public_launch_binding(
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
        )
        if attempt_id is not None:
            existing = battle_attempt_registry.get(
                attempt_id=attempt_id,
                profile_id=binding["profileId"],
                fingerprint=fingerprint,
                player_id=session.player_id,
                session_generation=session.generation,
            )
            if existing is not None:
                existing_session, envelope = existing
                record = store.authorize_public_battle(
                    battle_id=existing_session.battle_id,
                    player_id=session.player_id,
                    session_id=session.session_id,
                    session_generation=session.generation,
                )
                _cleanup_expired_process_battles(record.pop("expiredBattleIds", []))
                if record["lifecycleStatus"] == "terminalPending":
                    outcome = registry.adapter.snapshot(existing_session).get("outcome")
                    if outcome is None:
                        raise PublicBattleAccessError(
                            "battleSettlementPending",
                            "The authoritative battle result is pending durable settlement.",
                        )
                    settlement = store.settle_public_battle(
                        battle_id=existing_session.battle_id,
                        player_id=session.player_id,
                        session_id=session.session_id,
                        session_generation=session.generation,
                        outcome=outcome,
                    )
                    envelope["settlement"] = settlement
                    envelope.update({
                        "serverNow": settlement["settledAt"],
                        "expiresAt": settlement["settledAt"],
                        "lifecycleStatus": "settled",
                        "settlementStatus": "settled",
                    })
                    registry.remove(existing_session.battle_id)
                    return existing_session, envelope
                if record["lifecycleStatus"] == "settled":
                    settlement = store.public_battle_receipt(
                        battle_id=existing_session.battle_id,
                        player_id=session.player_id,
                        session_id=session.session_id,
                        session_generation=session.generation,
                    )
                    if settlement is None:
                        raise ProgressionStoreError("The settled battle receipt is missing.")
                    envelope["settlement"] = settlement
                    envelope.update({
                        "serverNow": settlement["settledAt"],
                        "expiresAt": settlement["settledAt"],
                        "lifecycleStatus": "settled",
                        "settlementStatus": "settled",
                    })
                    return existing_session, envelope
                if record["lifecycleStatus"] != "active":
                    _remove_process_battle(existing_session.battle_id)
                    raise PublicBattleAccessError(
                        "battleNoLongerActive",
                        "This launch attempt belongs to a battle that is no longer active.",
                    )
                cached_snapshot = envelope.get("data", {}).get("snapshot", {})
                if cached_snapshot.get("phase") == "ended":
                    # A previous create response could have been interrupted
                    # between automatic terminal engine resolution and the
                    # first durable settlement write.  Never replay that
                    # cached terminal envelope as an active confirmed result.
                    outcome = cached_snapshot.get("outcome")
                    store.mark_public_battle_terminal_pending(
                        battle_id=existing_session.battle_id,
                        player_id=session.player_id,
                        session_id=session.session_id,
                        session_generation=session.generation,
                        outcome=outcome,
                    )
                    settlement = store.settle_public_battle(
                        battle_id=existing_session.battle_id,
                        player_id=session.player_id,
                        session_id=session.session_id,
                        session_generation=session.generation,
                        outcome=outcome,
                    )
                    envelope["settlement"] = settlement
                    envelope.update({
                        "serverNow": settlement["settledAt"],
                        "expiresAt": settlement["settledAt"],
                        "lifecycleStatus": "settled",
                        "settlementStatus": "settled",
                    })
                    registry.remove(existing_session.battle_id)
                    return existing_session, envelope
                envelope.update(_public_lifecycle_fields(store, record))
                return existing_session, envelope

        battle_id = f"battle.{uuid.uuid4().hex}"
        seed = _fresh_battle_seed()
        seed_hex = f"{seed:064x}"
        reservation = store.reserve_public_battle(
            battle_id=battle_id,
            player_id=session.player_id,
            session_id=session.session_id,
            session_generation=session.generation,
            seed_hex=seed_hex,
            battle_type=battle_type,  # type: ignore[arg-type]
            context=context,
            build_version=os.getenv("LOCT_BUILD_VERSION", "pre-alpha"),
            capacity=int(os.getenv("BATTLE_API_PUBLIC_BATTLE_CAPACITY", "20")),
            provisional_ttl_seconds=int(
                os.getenv("BATTLE_API_PUBLIC_PROVISIONAL_TTL_SECONDS", "120")
            ),
        )
        _cleanup_expired_process_battles(reservation.pop("expiredBattleIds", []))
        retain_for_retry = False
        try:
            created_session, envelope = factory(
                seed, battle_id, reservation["profileId"]
            )
            _strip_public_seed_fields(envelope)
            record = store.activate_public_battle(
                battle_id=battle_id,
                player_id=session.player_id,
                session_id=session.session_id,
                session_generation=session.generation,
                inactivity_seconds=int(
                    os.getenv("BATTLE_API_PUBLIC_INACTIVITY_SECONDS", "1800")
                ),
            )
            envelope.update(_public_lifecycle_fields(store, record))
            bound = battle_attempt_registry.bind(
                attempt_id=attempt_id,
                profile_id=reservation["profileId"],
                fingerprint=fingerprint,
                session=created_session,
                envelope=envelope,
                player_id=session.player_id,
                session_generation=session.generation,
            )
            created_session, envelope = bound
            snapshot = envelope.get("data", {}).get("snapshot", {})
            if snapshot.get("phase") == "ended":
                retain_for_retry = True
                outcome = snapshot.get("outcome")
                store.mark_public_battle_terminal_pending(
                    battle_id=battle_id,
                    player_id=session.player_id,
                    session_id=session.session_id,
                    session_generation=session.generation,
                    outcome=outcome,
                )
                settlement = store.settle_public_battle(
                    battle_id=battle_id,
                    player_id=session.player_id,
                    session_id=session.session_id,
                    session_generation=session.generation,
                    outcome=outcome,
                )
                envelope["settlement"] = settlement
                envelope.update({
                    "serverNow": settlement["settledAt"],
                    "expiresAt": settlement["settledAt"],
                    "lifecycleStatus": "settled",
                    "settlementStatus": "settled",
                })
                registry.remove(battle_id)
            return created_session, envelope
        except Exception:
            if not retain_for_retry:
                _remove_process_battle(battle_id)
                store.abandon_public_reservation(
                    battle_id=battle_id, reason="constructionOrActivationFailed"
                )
            raise


def _authorized_public_record(
    *,
    store: ProgressionStore,
    session: AuthenticatedSession,
    battle_id: str,
) -> dict:
    record = store.authorize_public_battle(
        battle_id=battle_id,
        player_id=session.player_id,
        session_id=session.session_id,
        session_generation=session.generation,
    )
    _cleanup_expired_process_battles(record.pop("expiredBattleIds", []))
    return record


def _require_process_session(battle_id: str):
    battle = registry.get(battle_id)
    if battle is None:
        raise PublicBattleAccessError(
            "battleNoLongerActive",
            "The battle is no longer active on this server.",
        )
    return battle


SESSION_COOKIE = "__Host-loct_session"
CSRF_COOKIE = "__Host-loct_csrf"
SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60


def _identity_error(exc: PublicIdentityError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


def _require_public_origin(request: Request) -> None:
    expected = os.getenv("BATTLE_API_PUBLIC_ORIGIN")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "publicOriginNotConfigured",
                "message": "Public same-origin security is not configured.",
            },
        )
    if request.headers.get("origin") != expected:
        raise HTTPException(
            status_code=403,
            detail={"code": "originInvalid", "message": "Request origin is invalid."},
        )


def _set_session_cookies(
    response: Response,
    *,
    session_token: str,
    csrf_token: str,
) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=SESSION_MAX_AGE_SECONDS,
        secure=True,
        httponly=True,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE,
        csrf_token,
        max_age=SESSION_MAX_AGE_SECONDS,
        secure=True,
        httponly=False,
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"


def _clear_session_cookies(response: Response) -> None:
    for name, httponly in ((SESSION_COOKIE, True), (CSRF_COOKIE, False)):
        response.delete_cookie(
            name, path="/", secure=True, httponly=httponly, samesite="lax"
        )
    response.headers["Cache-Control"] = "no-store"


def _session_payload(
    issued: IssuedIdentity | AuthenticatedSession,
    *,
    recovery_code: str | None = None,
) -> dict:
    return {
        "contractVersion": CONTRACT_VERSION,
        "playerId": issued.player_id,
        "playerName": issued.display_name,
        "expiresAt": issued.expires_at,
        "recoveryConfirmed": issued.recovery_confirmed,
        "csrfToken": issued.csrf_token,
        "recoveryCode": recovery_code,
    }


async def get_public_session(
    request: Request,
    response: Response,
    service: Annotated[
        PublicIdentityService | None, Depends(get_optional_identity_service)
    ],
) -> AuthenticatedSession | None:
    if service is None:
        return None
    try:
        unsafe = request.method not in {"GET", "HEAD", "OPTIONS"}
        supplied: str | None = None
        if unsafe:
            _require_public_origin(request)
            session_token = request.cookies.get(SESSION_COOKIE)
            # Preserve the typed authentication contract: an absent or invalid
            # session is a 401 even when the request also lacks a CSRF token.
            # This first validation is read-only, so rejected requests cannot
            # extend or rotate the session.
            supplied = request.headers.get("X-CSRF-Token")
            await asyncio.to_thread(
                service.validate_session,
                session_token,
                touch=False,
                rotate=False,
                require_confirmed=True,
                csrf_token=supplied,
                require_csrf=True,
            )
            cookie_csrf = request.cookies.get(CSRF_COOKIE)
            if not supplied or not cookie_csrf or not secrets.compare_digest(
                supplied, cookie_csrf
            ):
                raise PublicIdentityError(
                    "csrfInvalid", "The request verification token is invalid.", 403
                )
        session = await asyncio.to_thread(
            service.validate_session,
            request.cookies.get(SESSION_COOKIE),
            touch=unsafe,
            rotate=unsafe,
            require_confirmed=True,
            csrf_token=supplied,
            require_csrf=supplied is not None,
        )
        if session.rotated_token:
            _set_session_cookies(
                response,
                session_token=session.rotated_token,
                csrf_token=session.csrf_token,
            )
        return session
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc


async def _unconfirmed_session(
    request: Request,
    response: Response,
    service: PublicIdentityService,
) -> AuthenticatedSession:
    try:
        _require_public_origin(request)
        supplied = request.headers.get("X-CSRF-Token")
        await asyncio.to_thread(
            service.validate_session,
            request.cookies.get(SESSION_COOKIE),
            touch=False,
            rotate=False,
            require_confirmed=False,
            csrf_token=supplied,
            require_csrf=True,
        )
        cookie_csrf = request.cookies.get(CSRF_COOKIE)
        if not supplied or not cookie_csrf or not secrets.compare_digest(
            supplied, cookie_csrf
        ):
            raise PublicIdentityError(
                "csrfInvalid", "The request verification token is invalid.", 403
            )
        session = await asyncio.to_thread(
            service.validate_session,
            request.cookies.get(SESSION_COOKIE),
            touch=True,
            rotate=True,
            require_confirmed=False,
            csrf_token=supplied,
            require_csrf=True,
        )
        if session.rotated_token:
            _set_session_cookies(
                response,
                session_token=session.rotated_token,
                csrf_token=session.csrf_token,
            )
        return session
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc


async def _read_progression(
    store: ProgressionStore, session: AuthenticatedSession | None = None
) -> dict:
    try:
        return await asyncio.to_thread(
            store.read_progression,
            session.player_id if session else None,
            session.session_id if session else None,
            session.generation if session else None,
        )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc


async def _run_slot_action(
    store: ProgressionStore,
    action: Callable[..., dict],
    *args: object,
) -> dict:
    try:
        return await asyncio.to_thread(action, *args)
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    if not engineering_enabled():
        store = get_progression_store()
        try:
            await asyncio.to_thread(store.ensure_initialized)
            await asyncio.to_thread(validate_public_configuration)
        except ProgressionStoreError as exc:
            raise _store_unavailable(exc) from exc
        except PublicConfigurationError as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "publicConfigurationInvalid",
                    "message": str(exc),
                    "retryable": False,
                },
            ) from exc
        get_identity_service()
    return {"status": "ok", "contractVersion": "1.0"}


@app.get("/api/v1/heroes", response_model=HeroRosterResponse)
async def list_heroes() -> dict:
    return {
        "contractVersion": CONTRACT_VERSION,
        "heroes": await asyncio.to_thread(
            registry.adapter.roster, hero_unlock_sources()
        ),
    }


@app.get(
    "/api/v1/manual/formation-demonstration",
    response_model=FormationDemonstrationResponse,
)
async def formation_demonstration() -> FormationDemonstrationResponse:
    """Return exhaustive static formation facts without creating a battle."""

    return FormationDemonstrationResponse.model_validate(
        formation_demonstration_catalogue()
    )


@app.post(
    "/api/v1/players",
    response_model=PlayerSessionResponse,
    response_model_exclude_none=True,
)
async def create_player(
    request_body: CreatePlayerRequest,
    request: Request,
    response: Response,
    service: Annotated[PublicIdentityService, Depends(get_identity_service)],
) -> dict:
    _require_public_origin(request)
    try:
        issued = await asyncio.to_thread(service.enroll, request_body.player_name)
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc
    _set_session_cookies(
        response, session_token=issued.session_token, csrf_token=issued.csrf_token
    )
    return _session_payload(issued, recovery_code=issued.recovery_code)


@app.post(
    "/api/v1/sessions/recover",
    response_model=PlayerSessionResponse,
    response_model_exclude_none=True,
)
async def recover_player(
    request_body: RecoverPlayerRequest,
    request: Request,
    response: Response,
    service: Annotated[PublicIdentityService, Depends(get_identity_service)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    _require_public_origin(request)
    trusted = frozenset(
        value.strip()
        for value in os.getenv("BATTLE_API_TRUSTED_PROXY_IPS", "").split(",")
        if value.strip()
    )
    peer = request.client.host if request.client else "127.0.0.1"
    try:
        client_ip = canonical_client_ip(
            peer, request.headers.get("X-Forwarded-For"), trusted
        )
        def recover_and_revoke_old_battles() -> IssuedIdentity:
            issued_identity = service.recover(request_body.recovery_code, client_ip)
            with _player_battle_lock(issued_identity.player_id):
                _retry_public_terminal_pending(store, session=issued_identity)
                _invalidate_public_player_battles(
                    store,
                    player_id=issued_identity.player_id,
                    reason="sessionRecovered",
                )
            return issued_identity

        issued = await asyncio.to_thread(recover_and_revoke_old_battles)
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    _set_session_cookies(
        response, session_token=issued.session_token, csrf_token=issued.csrf_token
    )
    return _session_payload(issued)


@app.get(
    "/api/v1/sessions/current",
    response_model=PlayerSessionResponse,
    response_model_exclude_none=True,
)
async def current_player_session(
    request: Request,
    response: Response,
    service: Annotated[PublicIdentityService, Depends(get_identity_service)],
) -> dict:
    try:
        session = await asyncio.to_thread(
            service.validate_session,
            request.cookies.get(SESSION_COOKIE),
            touch=False,
            rotate=False,
            require_confirmed=False,
        )
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc
    response.headers["Cache-Control"] = "no-store"
    return _session_payload(session)


@app.post(
    "/api/v1/sessions/refresh",
    response_model=PlayerSessionResponse,
    response_model_exclude_none=True,
)
async def refresh_player_session(
    request_body: EmptyAuthenticatedRequest,
    response: Response,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
) -> dict:
    del request_body
    if session is None:  # Development removes this route at registration time.
        raise HTTPException(status_code=404, detail="Not found")
    response.headers["Cache-Control"] = "no-store"
    return _session_payload(session)


@app.post(
    "/api/v1/recovery-code/acknowledge",
    response_model=PlayerSessionResponse,
    response_model_exclude_none=True,
)
async def acknowledge_recovery_code(
    request_body: EmptyAuthenticatedRequest,
    request: Request,
    response: Response,
    service: Annotated[PublicIdentityService, Depends(get_identity_service)],
) -> dict:
    del request_body
    session = await _unconfirmed_session(request, response, service)
    try:
        confirmed = await asyncio.to_thread(service.acknowledge, session)
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc
    response.headers["Cache-Control"] = "no-store"
    return _session_payload(confirmed)


@app.post(
    "/api/v1/recovery-code/forgot",
    response_model=RecoveryCodeReplacementResponse,
)
async def replace_recovery_code(
    request_body: EmptyAuthenticatedRequest,
    request: Request,
    response: Response,
    service: Annotated[PublicIdentityService, Depends(get_identity_service)],
) -> dict:
    del request_body
    session = await _unconfirmed_session(request, response, service)
    try:
        code = await asyncio.to_thread(service.replace_code, session)
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc
    response.headers["Cache-Control"] = "no-store"
    return {"contractVersion": CONTRACT_VERSION, "recoveryCode": code}


@app.post("/api/v1/sessions/logout", status_code=204)
async def logout_player(
    request_body: EmptyAuthenticatedRequest,
    request: Request,
    response: Response,
    service: Annotated[PublicIdentityService, Depends(get_identity_service)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> Response:
    del request_body
    session = await _unconfirmed_session(request, response, service)
    try:
        def logout_and_revoke_battles() -> None:
            with _player_battle_lock(session.player_id):
                _retry_public_terminal_pending(store, session=session)
                _invalidate_public_player_battles(
                    store,
                    player_id=session.player_id,
                    reason="sessionLogout",
                )
                service.logout(session)

        await asyncio.to_thread(logout_and_revoke_battles)
    except PublicIdentityError as exc:
        raise _identity_error(exc) from exc
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    _clear_session_cookies(response)
    response.status_code = 204
    return response


@app.get(
    "/api/v1/save-slots",
    response_model=SaveSlotListResponse,
    responses={503: {"model": RetryableHttpErrorResponse}},
)
async def list_save_slots(
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    result = await _run_slot_action(
        store,
        store.list_save_slots,
        session.player_id if session else None,
        session.session_id if session else None,
        session.generation if session else None,
    )
    return {"contractVersion": CONTRACT_VERSION, **result}


@app.post(
    "/api/v1/save-slots/{slot_id}/create",
    response_model=SaveSlotActionResponse,
    responses={
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def create_save_slot(
    slot_id: int,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
    request: EmptySaveSlotRequest | None = None,
) -> dict:
    del request
    if session is not None:
        def create_owned_slot() -> dict:
            with _player_battle_lock(session.player_id):
                _retry_public_terminal_pending(store, session=session)
                store.assert_public_battle_context_change_allowed(
                    player_id=session.player_id
                )
                result = store.create_save_slot(
                    slot_id, session.player_id, session.session_id, session.generation
                )
                _invalidate_public_player_battles(
                    store,
                    player_id=session.player_id,
                    reason="saveContextChanged",
                )
                return result

        result = await _run_slot_action(store, create_owned_slot)
    else:
        result = await _run_slot_action(store, store.create_save_slot, slot_id)
    return {"contractVersion": CONTRACT_VERSION, **result}


@app.post(
    "/api/v1/save-slots/{slot_id}/load",
    response_model=SaveSlotActionResponse,
    responses={
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def load_save_slot(
    slot_id: int,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
    request: EmptySaveSlotRequest | None = None,
) -> dict:
    del request
    if session is not None:
        def load_owned_slot() -> dict:
            with _player_battle_lock(session.player_id):
                _retry_public_terminal_pending(store, session=session)
                store.assert_public_battle_context_change_allowed(
                    player_id=session.player_id
                )
                result = store.load_save_slot(
                    slot_id, session.player_id, session.session_id, session.generation
                )
                _invalidate_public_player_battles(
                    store,
                    player_id=session.player_id,
                    reason="saveContextChanged",
                )
                return result

        result = await _run_slot_action(store, load_owned_slot)
    else:
        result = await _run_slot_action(store, store.load_save_slot, slot_id)
    return {"contractVersion": CONTRACT_VERSION, **result}


@app.post(
    "/api/v1/save-slots/{slot_id}/overwrite",
    response_model=SaveSlotActionResponse,
    responses={
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def overwrite_save_slot(
    slot_id: int,
    request: ConfirmSaveSlotOverwriteRequest,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    if request.confirm_overwrite is not True:
        raise _save_slot_error(
            SaveSlotAccessError(
                "overwriteConfirmationRequired",
                f"Confirmed overwrite is required for save slot {slot_id}.",
            )
        )
    if session is not None:
        def overwrite_owned_slot() -> dict:
            with _player_battle_lock(session.player_id):
                _retry_public_terminal_pending(store, session=session)
                store.assert_public_battle_context_change_allowed(
                    player_id=session.player_id
                )
                # Release any non-terminal lease before deleting the old
                # profile it references.  terminalPending is intentionally
                # retained and its FK safely blocks destructive overwrite.
                _invalidate_public_player_battles(
                    store,
                    player_id=session.player_id,
                    reason="saveContextChanged",
                )
                return store.overwrite_save_slot(
                    slot_id, session.player_id, session.session_id, session.generation
                )

        result = await _run_slot_action(store, overwrite_owned_slot)
    else:
        result = await _run_slot_action(store, store.overwrite_save_slot, slot_id)
    return {"contractVersion": CONTRACT_VERSION, **result}


@app.get(
    "/api/v1/progression",
    response_model=PlayerProgressionResponse,
    responses={
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def get_progression(
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    return {
        "contractVersion": CONTRACT_VERSION,
        **await _read_progression(store, session),
    }


@app.get(
    "/api/v1/arena",
    response_model=ArenaStateResponse,
    responses={
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def get_arena_state(
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    try:
        state = await asyncio.to_thread(
            store.read_arena_state,
            session.player_id if session else None,
            session.session_id if session else None,
            session.generation if session else None,
        )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    return {"contractVersion": CONTRACT_VERSION, **state}


@app.post(
    "/api/v1/arena/runs",
    response_model=ArenaStateResponse,
    responses={
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def create_arena_run(
    request: CreateArenaRunRequest,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    try:
        state = await asyncio.to_thread(
            store.create_arena_run,
            list(request.squad_definition_ids),
            player_id=session.player_id if session else None,
            session_id=session.session_id if session else None,
            session_generation=session.generation if session else None,
        )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    except ArenaAccessError as exc:
        raise _arena_error(exc) from exc
    return {"contractVersion": CONTRACT_VERSION, **state}


@app.post(
    "/api/v1/arena/runs/{run_id}/abandon",
    response_model=ArenaStateResponse,
    responses={409: {"model": HttpErrorResponse}, 503: {"model": RetryableHttpErrorResponse}},
)
async def abandon_arena_run(
    run_id: str,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    try:
        if session is not None:
            def abandon_owned_run() -> dict:
                with _player_battle_lock(session.player_id):
                    _retry_public_terminal_pending(store, session=session)
                    store.assert_public_battle_context_change_allowed(
                        player_id=session.player_id
                    )
                    _invalidate_public_player_battles(
                        store,
                        player_id=session.player_id,
                        reason="arenaRunAbandoned",
                    )
                    return store.abandon_arena_run(
                        run_id=run_id,
                        player_id=session.player_id,
                        session_id=session.session_id,
                        session_generation=session.generation,
                    )

            state = await asyncio.to_thread(abandon_owned_run)
        else:
            state = await asyncio.to_thread(store.abandon_arena_run, run_id=run_id)
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    except ArenaAccessError as exc:
        raise _arena_error(exc) from exc
    return {"contractVersion": CONTRACT_VERSION, **state}


@app.post(
    "/api/v1/arena/runs/{run_id}/nodes/{node_index}/battles",
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def create_arena_battle(
    run_id: str,
    node_index: Annotated[int, ApiPath(ge=1, le=12)],
    request: CreateArenaBattleRequest,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    def create_attempt(
        profile_id: str,
        *,
        seed: int | None = None,
        battle_id: str | None = None,
    ) -> tuple[object, dict]:
        node = store.arena_node_for_launch(
            run_id=run_id,
            node_index=node_index,
            player_team=list(request.player_team),
            player_formation=request.player_formation,
            player_id=session.player_id if session else None,
            session_id=session.session_id if session else None,
            session_generation=session.generation if session else None,
        )
        if node["profileId"] != profile_id:
            raise SaveSlotAccessError(
                "activeSaveSlotChanged",
                "The active save slot changed; start the Arena battle again.",
            )
        return registry.create(
            seed=seed if seed is not None else _fresh_battle_seed(),
            battle_id=battle_id,
            battle_size=node["battleSize"],
            player_team=list(request.player_team),
            enemy_composition_mode="specified",
            enemy_team=list(node["enemyDefinitionIds"]),
            enemy_control_mode="computer",
            player_formation=request.player_formation,
            enemy_formation=node["enemyFormation"],
            fixed_computer_formation=True,
            progression_profile_id=node["profileId"],
            arena_run_id=run_id,
            arena_node_index=node_index,
        )

    try:
        fingerprint = (
            "arena", run_id, node_index, tuple(request.player_team),
            request.player_formation,
        )
        if session is None:
            profile_id = await asyncio.to_thread(store.active_profile_id)
            _, envelope = await asyncio.to_thread(
                battle_attempt_registry.get_or_create,
                profile_id=profile_id,
                attempt_id=request.attempt_id,
                fingerprint=fingerprint,
                factory=lambda: create_attempt(profile_id),
            )
        else:
            _, envelope = await asyncio.to_thread(
                _public_launch,
                session=session,
                store=store,
                attempt_id=request.attempt_id,
                fingerprint=fingerprint,
                battle_type="arena",
                context={"runId": run_id, "nodeIndex": node_index},
                factory=lambda seed, battle_id, profile_id: create_attempt(
                    profile_id, seed=seed, battle_id=battle_id
                ),
            )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    except ArenaAccessError as exc:
        raise _arena_error(exc) from exc
    except BattleAttemptConflict as exc:
        raise _battle_attempt_error(exc) from exc
    except PublicBattleAccessError as exc:
        raise _public_battle_error(exc) from exc
    return envelope


@app.post(
    "/api/v1/arena/battles/{battle_id}/completion",
    response_model=ArenaVictoryCommitResponse,
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def commit_arena_battle_completion(
    battle_id: str,
    auth: Annotated[AuthenticatedSession | None, Depends(get_public_session)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    if auth is not None:
        try:
            receipt = await asyncio.to_thread(
                store.public_battle_receipt,
                battle_id=battle_id,
                player_id=auth.player_id,
                session_id=auth.session_id,
                session_generation=auth.generation,
            )
        except PublicBattleAccessError as exc:
            raise _public_battle_error(exc) from exc
        except ProgressionStoreError as exc:
            raise _store_unavailable(exc) from exc
        except SaveSlotAccessError as exc:
            raise _save_slot_error(exc) from exc
        if receipt is None or "arena" not in receipt:
            raise _arena_error(ArenaAccessError(
                "battleSettlementPending",
                "The Arena battle has no durable friendly-victory receipt.",
            ))
        return {"contractVersion": CONTRACT_VERSION, **receipt}

    session = registry.get(battle_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "battleNotFound", "message": "Battle was not found."},
        )
    if (
        session.arena_run_id is None
        or session.arena_node_index is None
        or session.progression_profile_id is None
    ):
        raise _arena_error(ArenaAccessError(
            "battleNotArenaScoped", "This battle does not belong to an Arena Run."
        ))

    def commit_if_won() -> dict:
        with session.lock:
            snapshot = registry.adapter.snapshot(session)
            if snapshot["phase"] != "ended" or snapshot.get("outcome") != {
                "kind": "victory", "winningSideId": "friendly"
            }:
                raise ArenaAccessError(
                    "friendlyVictoryRequired",
                    "Only an authoritative friendly victory can advance Arena.",
                )
            return store.commit_arena_victory(
                run_id=session.arena_run_id,
                node_index=session.arena_node_index,
                battle_id=battle_id,
                expected_profile_id=session.progression_profile_id,
            )

    try:
        result = await asyncio.to_thread(commit_if_won)
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    except ArenaAccessError as exc:
        raise _arena_error(exc) from exc
    return {
        "contractVersion": CONTRACT_VERSION,
        "battleId": battle_id,
        **result,
    }


@app.get(
    "/api/v1/stages",
    response_model=StructuredStagesResponse,
    responses={
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def list_stages(
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    return stages_response(await _read_progression(store, session))


@app.post(
    "/api/v1/battles",
    responses={
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def create_battle(
    request: CreateBattleRequest,
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    try:
        profile_id = await asyncio.to_thread(store.active_profile_id)
        await asyncio.to_thread(
            store.assert_player_team_unlocked, list(request.player_team), profile_id
        )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except StageAccessError as exc:
        raise _access_error(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    _, envelope = await asyncio.to_thread(
        registry.create,
        seed=request.seed,
        battle_size=request.battle_size,
        player_team=list(request.player_team),
        enemy_composition_mode=request.enemy_composition_mode,
        enemy_team=list(request.enemy_team) if request.enemy_team else None,
        enemy_control_mode=request.enemy_control_mode,
        player_formation=request.player_formation,
        enemy_formation=request.enemy_formation,
    )
    return envelope


@app.post(
    "/api/v1/stages/{stage_id}/battles/{battle_index}",
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def create_stage_battle(
    stage_id: StageId,
    battle_index: Annotated[int, ApiPath(ge=1)],
    request: CreateStageBattleRequest,
    session: Annotated[
        AuthenticatedSession | None, Depends(get_public_session)
    ],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    if session is not None and "seed" in request.model_fields_set:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "publicSeedForbidden",
                "message": "Public battle requests must omit seed.",
            },
        )

    def create_attempt(
        profile_id: str,
        *,
        seed: int | None = None,
        battle_id: str | None = None,
    ) -> tuple[object, dict]:
        battle = store.assert_stage_battle_access(
            stage_id,
            battle_index,
            expected_profile_id=profile_id,
            mode=request.mode,
            player_id=session.player_id if session else None,
            session_id=session.session_id if session else None,
            session_generation=session.generation if session else None,
        )
        store.assert_player_team_unlocked(
            list(request.player_team),
            profile_id,
            player_id=session.player_id if session else None,
            session_id=session.session_id if session else None,
            session_generation=session.generation if session else None,
        )

        if len(request.player_team) != battle.battle_size:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalidStageBattleConfiguration",
                    "message": "playerTeam must contain exactly the fixed battle size.",
                },
            )
        valid_player_formations = {
            1: {None},
            2: {"front-rear", "side-by-side"},
            3: {"one-front-two-rear", "two-front-one-rear", "all-front"},
        }[battle.battle_size]
        if request.player_formation not in valid_player_formations:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalidStageBattleConfiguration",
                    "message": (
                        "playerFormation must be valid for this stage battle size."
                    ),
                },
            )

        return registry.create(
            seed=(
                seed if seed is not None else
                request.seed if request.seed is not None else _fresh_battle_seed()
            ),
            battle_id=battle_id,
            battle_size=battle.battle_size,
            player_team=list(request.player_team),
            enemy_composition_mode="specified",
            enemy_team=list(battle.enemy_definition_ids),
            enemy_control_mode="computer",
            player_formation=request.player_formation,
            enemy_formation=battle.formation,
            fixed_computer_formation=True,
            stage_id=stage_id,
            stage_battle_index=battle_index,
            stage_mode=request.mode,
            progression_profile_id=profile_id,
        )

    try:
        fingerprint = (
            "stage", stage_id, battle_index, request.mode,
            tuple(request.player_team), request.player_formation,
            request.seed if session is None else None,
        )
        if session is None:
            profile_id = await asyncio.to_thread(store.active_profile_id)
            _, envelope = await asyncio.to_thread(
                battle_attempt_registry.get_or_create,
                profile_id=profile_id,
                attempt_id=request.attempt_id,
                fingerprint=fingerprint,
                factory=lambda: create_attempt(profile_id),
            )
        else:
            _, envelope = await asyncio.to_thread(
                _public_launch,
                session=session,
                store=store,
                attempt_id=request.attempt_id,
                fingerprint=fingerprint,
                battle_type="stage",
                context={
                    "stageId": stage_id,
                    "battleIndex": battle_index,
                    "mode": request.mode,
                },
                factory=lambda seed, battle_id, profile_id: create_attempt(
                    profile_id, seed=seed, battle_id=battle_id
                ),
            )
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except StageAccessError as exc:
        raise _access_error(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    except BattleAttemptConflict as exc:
        raise _battle_attempt_error(exc) from exc
    except PublicBattleAccessError as exc:
        raise _public_battle_error(exc) from exc
    return envelope


@app.get(
    "/api/v1/battles/{battle_id}",
    responses={404: {"model": HttpErrorResponse}},
)
async def get_battle(
    battle_id: str,
    auth: Annotated[AuthenticatedSession | None, Depends(get_public_session)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    if auth is not None:
        def public_snapshot() -> dict:
            with _player_battle_lock(auth.player_id):
                record = _authorized_public_record(
                    store=store, session=auth, battle_id=battle_id
                )
                if record["lifecycleStatus"] != "active":
                    raise PublicBattleAccessError(
                        "battleNoLongerActive", "The battle is no longer active."
                    )
                battle = _require_process_session(battle_id)
                with battle.lock:
                    snapshot = registry.adapter.snapshot(battle)
                    envelope = registry.adapter.envelope(battle, snapshot)
                envelope.update(_public_lifecycle_fields(store, record))
                return envelope
        try:
            return await asyncio.to_thread(public_snapshot)
        except PublicBattleAccessError as exc:
            raise _public_battle_error(exc) from exc
        except ProgressionStoreError as exc:
            raise _store_unavailable(exc) from exc
        except SaveSlotAccessError as exc:
            raise _save_slot_error(exc) from exc

    battle = registry.get(battle_id)
    if battle is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "battleNotFound", "message": "Battle was not found."},
        )
    def locked_snapshot() -> dict:
        with battle.lock:
            snapshot = registry.adapter.snapshot(battle)
            return registry.adapter.envelope(battle, snapshot)

    return await asyncio.to_thread(locked_snapshot)


@app.post(
    "/api/v1/battles/{battle_id}/commands",
    responses={404: {"model": HttpErrorResponse}},
)
async def submit_command(
    battle_id: str,
    command: UseSkillCommand,
    auth: Annotated[AuthenticatedSession | None, Depends(get_public_session)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    if auth is not None:
        def public_submit() -> dict:
            with _player_battle_lock(auth.player_id):
                record = _authorized_public_record(
                    store=store, session=auth, battle_id=battle_id
                )
                if record["lifecycleStatus"] == "settled":
                    receipt = store.public_battle_receipt(
                        battle_id=battle_id,
                        player_id=auth.player_id,
                        session_id=auth.session_id,
                        session_generation=auth.generation,
                    )
                    if receipt is None:
                        raise ProgressionStoreError(
                            "The settled battle receipt is missing."
                        )
                    return {
                        "contractVersion": CONTRACT_VERSION,
                        "battleId": battle_id,
                        "revision": command.expected_revision,
                        "data": None,
                        "settlement": receipt,
                        "serverNow": receipt["settledAt"],
                        "expiresAt": receipt["settledAt"],
                        "lifecycleStatus": "settled",
                        "settlementStatus": "settled",
                    }
                if record["lifecycleStatus"] in {"abandoned", "expired"}:
                    raise PublicBattleAccessError(
                        "battleNoLongerActive", "The battle is no longer active."
                    )
                battle = _require_process_session(battle_id)
                with battle.lock:
                    if record["lifecycleStatus"] == "resolving":
                        current_snapshot = registry.adapter.snapshot(battle)
                        outcome = current_snapshot.get("outcome")
                        if outcome is None:
                            # Engine resolution completed but the post-action
                            # inactivity write failed.  Finish that write
                            # before replaying the cached command or accepting
                            # a later command; never strand a live battle in
                            # the in-flight state.
                            record = store.touch_public_battle_after_action(
                                battle_id=battle_id,
                                player_id=auth.player_id,
                                session_id=auth.session_id,
                                session_generation=auth.generation,
                            )
                            cached = battle.command_results.get(command.command_id)
                            if cached is not None:
                                envelope = registry.adapter.envelope(battle, cached)
                                envelope["revision"] = cached["revision"]
                                envelope.update(_public_lifecycle_fields(store, record))
                                return envelope
                        else:
                            settlement = store.settle_public_battle(
                                battle_id=battle_id,
                                player_id=auth.player_id,
                                session_id=auth.session_id,
                                session_generation=auth.generation,
                                outcome=outcome,
                            )
                            cached = battle.command_results.get(command.command_id)
                            envelope = (
                                registry.adapter.envelope(battle, cached)
                                if cached is not None else {
                                    "contractVersion": CONTRACT_VERSION,
                                    "battleId": battle_id,
                                    "revision": battle.revision,
                                    "data": None,
                                }
                            )
                            envelope["settlement"] = settlement
                            envelope.update({
                                "serverNow": settlement["settledAt"],
                                "expiresAt": settlement["settledAt"],
                                "lifecycleStatus": "settled",
                                "settlementStatus": "settled",
                            })
                            _remove_process_battle(battle_id)
                            return envelope
                    if record["lifecycleStatus"] == "terminalPending":
                        outcome = registry.adapter.snapshot(battle).get("outcome")
                        if outcome is None:
                            raise ProgressionStoreError(
                                "The pending battle outcome is missing from the engine session."
                            )
                        settlement = store.settle_public_battle(
                            battle_id=battle_id,
                            player_id=auth.player_id,
                            session_id=auth.session_id,
                            session_generation=auth.generation,
                            outcome=outcome,
                        )
                        cached = battle.command_results.get(command.command_id)
                        envelope = (
                            registry.adapter.envelope(battle, cached)
                            if cached is not None else {
                                "contractVersion": CONTRACT_VERSION,
                                "battleId": battle_id,
                                "revision": battle.revision,
                                "data": None,
                            }
                        )
                        envelope["settlement"] = settlement
                        envelope.update({
                            "serverNow": settlement["settledAt"],
                            "expiresAt": settlement["settledAt"],
                            "lifecycleStatus": "settled",
                            "settlementStatus": "settled",
                        })
                        _remove_process_battle(battle_id)
                        return envelope
                    if record["lifecycleStatus"] != "active":
                        raise PublicBattleAccessError(
                            "battleNoLongerActive", "The battle is no longer active."
                        )
                    action_started = False

                    def accepted() -> None:
                        nonlocal action_started
                        store.begin_public_battle_action(
                            battle_id=battle_id,
                            player_id=auth.player_id,
                            session_id=auth.session_id,
                            session_generation=auth.generation,
                        )
                        action_started = True

                    try:
                        result = registry.adapter.submit(
                            battle,
                            command.model_dump(by_alias=True),
                            on_accepted=accepted,
                        )
                    except Exception:
                        if action_started:
                            authority_ended = store.cancel_public_battle_action(
                                battle_id=battle_id,
                                player_id=auth.player_id,
                                session_id=auth.session_id,
                                session_generation=auth.generation,
                            )
                            if authority_ended:
                                _remove_process_battle(battle_id)
                        raise
                    settlement = None
                    snapshot = result.get("snapshot", {})
                    if action_started and snapshot.get("phase") == "ended":
                        outcome = snapshot.get("outcome")
                        try:
                            settlement = store.settle_public_battle(
                                battle_id=battle_id,
                                player_id=auth.player_id,
                                session_id=auth.session_id,
                                session_generation=auth.generation,
                                outcome=outcome,
                            )
                        except Exception:
                            store.mark_public_battle_terminal_pending(
                                battle_id=battle_id,
                                player_id=auth.player_id,
                                session_id=auth.session_id,
                                session_generation=auth.generation,
                                outcome=outcome,
                            )
                            raise
                        lifecycle = {
                            "serverNow": settlement["settledAt"],
                            "expiresAt": settlement["settledAt"],
                            "lifecycleStatus": "settled",
                            "settlementStatus": "settled",
                        }
                    elif action_started:
                        record = store.touch_public_battle_after_action(
                            battle_id=battle_id,
                            player_id=auth.player_id,
                            session_id=auth.session_id,
                            session_generation=auth.generation,
                        )
                        lifecycle = _public_lifecycle_fields(store, record)
                    else:
                        lifecycle = _public_lifecycle_fields(store, record)
                    envelope = registry.adapter.envelope(battle, result)
                    envelope["revision"] = result["revision"]
                    envelope.update(lifecycle)
                    if settlement is not None:
                        envelope["settlement"] = settlement
                        _remove_process_battle(battle_id)
                    return envelope
        try:
            return await asyncio.to_thread(public_submit)
        except PublicBattleAccessError as exc:
            raise _public_battle_error(exc) from exc
        except ProgressionStoreError as exc:
            raise _store_unavailable(exc) from exc
        except SaveSlotAccessError as exc:
            raise _save_slot_error(exc) from exc
        except (StageAccessError, ArenaAccessError) as exc:
            raise HTTPException(
                status_code=409,
                detail={"code": exc.code, "message": exc.message},
            ) from exc

    battle = registry.get(battle_id)
    if battle is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "battleNotFound", "message": "Battle was not found."},
        )
    result = await asyncio.to_thread(
        registry.adapter.submit, battle, command.model_dump(by_alias=True)
    )
    envelope = registry.adapter.envelope(battle, result)
    # Cached idempotent responses retain their original revision and snapshot.
    # Keep the envelope internally consistent instead of pairing old data with
    # the session's newer revision.
    envelope["revision"] = result["revision"]
    return envelope


@app.post(
    "/api/v1/battles/{battle_id}/preview",
    response_model=BattlePreviewResponse,
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        422: {"model": HttpErrorResponse},
    },
)
async def preview_battle_action(
    battle_id: str,
    request: BattlePreviewRequest,
    auth: Annotated[AuthenticatedSession | None, Depends(get_public_session)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    """Return audited current-revision combat facts without executing action."""
    if auth is not None:
        def public_preview() -> dict:
            with _player_battle_lock(auth.player_id):
                record = _authorized_public_record(
                    store=store, session=auth, battle_id=battle_id
                )
                if record["lifecycleStatus"] != "active":
                    raise PublicBattleAccessError(
                        "battleNoLongerActive", "The battle is no longer active."
                    )
                battle = _require_process_session(battle_id)
                with battle.lock:
                    try:
                        data = registry.adapter.preview(
                            battle, request.model_dump(by_alias=True)
                        )
                    except BattleAdapterError as exc:
                        status = 409 if exc.code in {
                            "battleEnded", "notYourTurn", "staleRevision",
                        } else 422
                        raise HTTPException(
                            status_code=status,
                            detail={"code": exc.code, "message": exc.message},
                        ) from exc
                    envelope = registry.adapter.envelope(battle, data)
                envelope.update(_public_lifecycle_fields(store, record))
                return envelope
        try:
            return await asyncio.to_thread(public_preview)
        except PublicBattleAccessError as exc:
            raise _public_battle_error(exc) from exc
        except ProgressionStoreError as exc:
            raise _store_unavailable(exc) from exc
        except SaveSlotAccessError as exc:
            raise _save_slot_error(exc) from exc

    battle = registry.get(battle_id)
    if battle is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "battleNotFound", "message": "Battle was not found."},
        )

    def locked_preview() -> dict:
        with battle.lock:
            try:
                data = registry.adapter.preview(
                    battle, request.model_dump(by_alias=True)
                )
            except BattleAdapterError as exc:
                status = 409 if exc.code in {
                    "battleEnded",
                    "notYourTurn",
                    "staleRevision",
                } else 422
                raise HTTPException(
                    status_code=status,
                    detail={"code": exc.code, "message": exc.message},
                ) from exc
            return registry.adapter.envelope(battle, data)

    return await asyncio.to_thread(locked_preview)


@app.post(
    "/api/v1/battles/{battle_id}/resign",
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def resign_battle(
    battle_id: str,
    auth: Annotated[AuthenticatedSession | None, Depends(get_public_session)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    if auth is None:
        raise HTTPException(status_code=404, detail="Not found")

    def resign_owned() -> dict:
        with _player_battle_lock(auth.player_id):
            battle = registry.get(battle_id)
            if battle is not None:
                with battle.lock:
                    result = store.resign_public_battle(
                        battle_id=battle_id,
                        player_id=auth.player_id,
                        session_id=auth.session_id,
                        session_generation=auth.generation,
                    )
            else:
                result = store.resign_public_battle(
                    battle_id=battle_id,
                    player_id=auth.player_id,
                    session_id=auth.session_id,
                    session_generation=auth.generation,
                )
            if result.get("lifecycleStatus") in {"abandoned", "expired", "settled"}:
                _remove_process_battle(battle_id)
            return {"contractVersion": CONTRACT_VERSION, **result}

    try:
        return await asyncio.to_thread(resign_owned)
    except PublicBattleAccessError as exc:
        raise _public_battle_error(exc) from exc
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc


@app.post(
    "/api/v1/battles/{battle_id}/completion",
    response_model=VictoryCommitResponse,
    responses={
        404: {"model": HttpErrorResponse},
        409: {"model": HttpErrorResponse},
        503: {"model": RetryableHttpErrorResponse},
    },
)
async def commit_battle_completion(
    battle_id: str,
    auth: Annotated[AuthenticatedSession | None, Depends(get_public_session)],
    store: Annotated[ProgressionStore, Depends(get_progression_store)],
) -> dict:
    if auth is not None:
        try:
            receipt = await asyncio.to_thread(
                store.public_battle_receipt,
                battle_id=battle_id,
                player_id=auth.player_id,
                session_id=auth.session_id,
                session_generation=auth.generation,
            )
        except PublicBattleAccessError as exc:
            raise _public_battle_error(exc) from exc
        except ProgressionStoreError as exc:
            raise _store_unavailable(exc) from exc
        except SaveSlotAccessError as exc:
            raise _save_slot_error(exc) from exc
        if receipt is None or "progression" not in receipt:
            raise _access_error(StageAccessError(
                "battleSettlementPending",
                "The stage battle has no durable friendly-victory receipt.",
            ))
        return {"contractVersion": CONTRACT_VERSION, **receipt}

    session = registry.get(battle_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "battleNotFound",
                "message": "Battle was not found.",
            },
        )
    if session.stage_id is None or session.stage_battle_index is None:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "battleNotStageScoped",
                "message": "Arena battles do not update structured-stage progression.",
            },
        )

    def commit_if_won() -> dict:
        with session.lock:
            snapshot = registry.adapter.snapshot(session)
            outcome = snapshot.get("outcome")
            if snapshot["phase"] != "ended" or outcome != {
                "kind": "victory",
                "winningSideId": "friendly",
            }:
                raise StageAccessError(
                    "friendlyVictoryRequired",
                    "Only an authoritative friendly victory can be committed.",
                )
            return store.commit_victory(
                battle_id=battle_id,
                stage_id=session.stage_id,
                battle_index=session.stage_battle_index,
                mode=session.stage_mode or "learner",
                expected_profile_id=session.progression_profile_id,
            )

    try:
        result = await asyncio.to_thread(commit_if_won)
    except ProgressionStoreError as exc:
        raise _store_unavailable(exc) from exc
    except StageAccessError as exc:
        raise _access_error(exc) from exc
    except SaveSlotAccessError as exc:
        raise _save_slot_error(exc) from exc
    return {
        "contractVersion": CONTRACT_VERSION,
        "battleId": battle_id,
        **result,
    }


def _apply_release_route_gate() -> None:
    """Keep Public battle HTTP entry points closed until explicitly opted in.

    Batch 2 exercises the owner-bound Stage/Arena battle surface only in
    isolated test processes.  A normal Public process therefore retains the
    Batch 1 fail-closed boundary; Batch 3 can opt its isolated process into the
    new routes without ever exposing the generic engineering battle creator.
    """

    if engineering_enabled():
        public_identity_prefixes = (
            "/api/v1/players",
            "/api/v1/sessions",
            "/api/v1/recovery-code",
        )
        app.router.routes = [
            route
            for route in app.router.routes
            if not getattr(route, "path", "").startswith(public_identity_prefixes)
        ]
        return

    public_battles_enabled = (
        os.getenv("BATTLE_API_ENABLE_PUBLIC_BATTLES", "0") == "1"
    )
    if not public_battles_enabled:
        app.router.routes = [
            route
            for route in app.router.routes
            if "/battles" not in getattr(route, "path", "")
        ]
        return

    app.router.routes = [
        route
        for route in app.router.routes
        if getattr(route, "path", "") != "/api/v1/battles"
    ]


_apply_release_route_gate()

# Public battle entry points remain default-off in Batch 2.  The isolated
# opt-in process reconciles any RAM-dependent lease before serving traffic;
# an old in-memory engine session cannot be resumed after a process restart.
if (
    not engineering_enabled()
    and os.getenv("BATTLE_API_ENABLE_PUBLIC_BATTLES", "0") == "1"
    and progression_store is not None
):
    _cleanup_expired_process_battles(
        progression_store.reconcile_public_battles_after_restart()
    )
