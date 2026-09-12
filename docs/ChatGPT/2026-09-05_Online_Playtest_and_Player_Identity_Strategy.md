# Legends of Champions Tactics --- Online Play Test & Player Identity Strategy

**Date:** 5 September 2026 **Status:** Planning decision / pre-alpha
online playtest

## 1. Current Technical Context

Legends of Champions Tactics uses Python as the authoritative combat
engine/backend and Next.js/JavaScript as the browser frontend. The
immediate goal is to make the game available online for external
testing.

Desktop/mobile app packaging is paused. The priorities brought forward
are online deployment and responsive browser layout.

## 2. Online Playtest Strategy

The first online build should prioritize:

-   stable and reliable access;
-   an always-on Python backend;
-   very low friction for testers;
-   simple deployment and updates;
-   useful playtest data collection;
-   a path toward future PvP.

A tester should ideally receive a URL, open it, choose a player name,
and begin playing without installing software.

### Hosting Direction

The Python backend is authoritative and should be treated as core game
infrastructure. A free host that routinely sleeps and creates noticeable
cold starts is therefore not preferred. Artificial periodic keep-alive
pings should not be a dependency of the architecture.

Target structure:

    Browser
       |
       v
    Next.js Web Frontend
       |
     HTTPS
       |
       v
    Always-on FastAPI + Python Combat Engine
       |
       +--> Persistent player storage
       |
       +--> Future temporary/PvP storage

An always-on low-cost/free VM and reliable managed hosting should be
compared before deployment. Stability and maintenance effort matter more
than choosing a service solely because it is free.

A restricted/private itch.io project can later act as a
playtest/distribution page for unfinished builds, while the actual
application can remain hosted separately.

## 3. Backend Components

**FastAPI:** Keep FastAPI as the API layer around the authoritative
Python combat engine.

**WebSocket:** Useful for future PvP, rooms, matchmaking and
server-pushed events, but it does not need to be introduced everywhere
merely to deploy the current single-player prototype.

**Persistent database:** PostgreSQL/Supabase is suitable for player
identity, progress, completed stages, saved teams, settings and playtest
history.

**Redis:** Potentially useful later for PvP rooms, matchmaking queues,
temporary battle state, reconnect support and coordination between
multiple backend instances. Do not add it yet unless shared temporary
state is actually required.

## 4. Saving Strategy During Pre-Alpha

Completely removing saving is possible for very short tests, but is not
preferred. Returning testers should not unnecessarily lose progress, and
persistent identity improves playtest data.

At the same time, conventional registration is unnecessary. Initially do
not require email, password, verification, Google/Apple login, account
recovery or cross-device synchronization.

## 5. Lightweight Player Name System

The agreed direction is a lightweight player identity system.

First visit:

    Choose Your Player Name

    [ RavenKnight ]

    Available

    [ Start Playing ]

The backend checks whether the name is occupied. If it is taken, the
player is asked to choose another.

The visible player name must NOT be the authentication credential.

Internally:

    Player
    ------
    id              UUID
    display_name    RavenKnight
    normalized_name ravenknight
    auth_token      random secret token
    created_at
    last_seen
    build_version

The browser stores a secret authentication token. The player normally
never needs to see or enter it.

Returning visit:

    Open game
       |
    Browser sends stored token
       |
    Backend identifies player
       |
    Load progress
       |
    Welcome back, RavenKnight

## 6. Player Name Rules

Recommended initial rules:

-   3--20 characters;
-   letters/numbers, optionally underscore;
-   case-insensitive uniqueness;
-   no leading/trailing spaces;
-   basic reserved-name/profanity filtering.

For example, Raven, raven, RAVEN and RaVeN should all map to the same
normalized name.

The UI should preferably say **Choose Your Player Name** rather than
**Register** so onboarding remains lightweight.

## 7. Accepted Pre-Alpha Limitation

Without a recovery credential, identity is initially tied to the
browser/device containing the authentication token.

Clearing browser storage, using private browsing, changing browsers or
changing devices may cause the tester to be treated as a new player.
This is acceptable during pre-alpha.

The game should state that playtest progress may be reset between
builds.

An optional recovery code can be considered later before implementing
full accounts.

## 8. Suggested Initial Persistent Data

### Player

    id
    display_name
    normalized_name
    auth_token / authentication reference
    created_at
    last_seen
    build_version

### Player Progress

    player_id
    tutorial_completed
    current_stage
    completed_stages
    saved_team
    settings

### Battle Record / Playtest Telemetry

    battle_id
    player_id
    build_version
    stage
    selected_heroes
    formation
    result
    round_count
    duration
    retries

This can answer questions such as which heroes/formations are used,
where players lose, whether they retry, battle length and whether
testers return.

## 9. Active Battle State

For the first small-scale test, active battle state can remain in Python
memory if necessary: HP, statuses, cooldowns, formation, current
round/turn, summons and temporary calculations.

A backend restart could therefore terminate an active battle. This is
acceptable for the earliest pre-alpha test but should not be the
long-term architecture.

Before serious PvP, reconnection or multi-instance deployment, battle
state should become recoverable, potentially using Redis or another
server-side persistence mechanism.

## 10. Current Implementation Priorities

Implement/investigate now:

1.  Select a stable always-on host for FastAPI + Python.
2.  Put the Next.js frontend online.
3.  Configure HTTPS and production API URLs.
4.  Implement unique player-name creation.
5.  Generate a secure hidden authentication token.
6.  Implement basic persistent player progress.
7.  Record pseudonymous battle telemetry.
8.  Make GitHub deployment/update workflow simple.
9.  Prepare a restricted external playtest entry point when ready.

Defer:

-   full email/password registration;
-   social login;
-   cross-device account system;
-   account recovery UI;
-   friend system;
-   matchmaking;
-   full PvP networking;
-   Redis unless required;
-   mobile/desktop application packaging.

## 11. Working Decision

> **Web-first, always-on authoritative Python backend, no conventional
> registration, lightweight unique player names, hidden browser
> authentication token, basic persistent saves, and playtest
> telemetry.**

The objective is to make entering Legends almost effortless while
retaining enough identity and persistence for repeated external testing
and useful analysis. The architecture should remain deliberately simple
now while leaving a clear path toward proper accounts, recoverable
battle/session state, matchmaking and PvP later.


## 12. Update — 12 September 2026: Pre-Alpha Backend Hosting and Multi-Device Identity

### Backend Hosting Decision
Proceed with **Google Compute Engine e2-micro** as the preferred always-on FastAPI + Python combat-engine server for the first external pre-alpha test. Cost is the primary infrastructure constraint while the game is not generating revenue. Railway remains technically suitable and is a future option if managed deployment, logging, scaling, or reduced server-maintenance effort becomes worth its recurring cost.

The turn-based backend is expected to be lightweight and bursty, but actual suitability must be confirmed by measuring the real service. Begin with one VM and one application worker unless measurement demonstrates otherwise. Measure CPU, RAM, request latency, errors, and representative concurrent battles. Keep static frontend/art/audio assets off the Python VM where practical.

### Persistence Decision
Keep the **existing SQLite persistence system** for the first small, single-VM online pre-alpha test. SQLite remains backend-authoritative for current persistent player/progression data. Live battle state remains process-local/in-memory and is not checkpointed yet.

Because the SQLite database resides with the VM, add an appropriate backup strategy. SQLite is the pre-alpha persistence choice, not the final online account database. Reconsider PostgreSQL/Supabase when multi-instance deployment, stronger cloud recovery, larger-scale telemetry, mature accounts, or serious PvP justify it.

### Player Name + Recovery Code
The earlier browser/device-only identity limitation is superseded by a lightweight **Player Name + Recovery Code** design.

Each player has one stable backend player UUID. The unique display/player name is not itself an authentication credential. On player creation, the backend generates a recovery code and the player is instructed to save it. Each authorized browser/device receives its own hidden random authentication token.

Same-device access uses the stored device token automatically. On a new laptop, iPad, phone, or browser, the player enters **Player Name + Recovery Code**. After successful verification, the backend issues a new device authentication token and loads the same stable player UUID and server-side progress.

Recommended identity separation:

    Player
    ------
    id
    display_name
    normalized_name
    recovery_code_hash / secure recovery verifier
    created_at
    last_seen
    build_version

    Device Authentication
    ---------------------
    player_id
    device_token_hash / authentication reference
    created_at
    last_seen
    revoked_at (optional)

Recovery codes and device tokens must be generated securely, and server persistence should store secure verification material rather than treating readable credentials as ordinary player data.

Full email/password registration, email verification, social login, conventional account-management UI, and advanced recovery remain deferred.

### Updated Working Direction

> **For the first online pre-alpha: web-first; Google e2-micro as the initial always-on authoritative FastAPI/Python backend; existing SQLite persistence with backup; lightweight unique player names plus recovery codes; per-device hidden authentication tokens; in-memory active battles; and pseudonymous playtest telemetry.**

This keeps infrastructure cost and implementation complexity low while preserving migration paths toward managed hosting, PostgreSQL/Supabase, recoverable battle state, full account systems, Redis, matchmaking, and PvP.
