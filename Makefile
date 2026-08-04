.PHONY: dev backend frontend lan

# Override this when Wi-Fi is not en0, for example:
# make lan LAN_HOST=192.168.1.42
LAN_HOST ?= $(shell ipconfig getifaddr en0 2>/dev/null)

# Start the Python adapter and the web client together for local development.
# Press Ctrl-C once to stop both child processes.
dev:
	@set -e; \
	backend_pid=''; frontend_pid=''; \
	cleanup() { \
		[ -z "$$backend_pid" ] || kill "$$backend_pid" 2>/dev/null || true; \
		[ -z "$$frontend_pid" ] || kill "$$frontend_pid" 2>/dev/null || true; \
	}; \
	trap cleanup INT TERM EXIT; \
	.venv/bin/uvicorn battle_api.app:app --reload --port 8001 & backend_pid=$$!; \
	(cd web-ui && npm run dev) & frontend_pid=$$!; \
	wait $$backend_pid $$frontend_pid

backend:
	.venv/bin/uvicorn battle_api.app:app --reload --port 8001

frontend:
	cd web-ui && npm run dev

# Opt-in LAN development mode. It binds both development servers only to the
# selected LAN address and limits browser API access to that same origin.
lan:
	@test -n "$(LAN_HOST)" || { echo "Could not detect a LAN address. Run: make lan LAN_HOST=<your-LAN-IP>"; exit 2; }
	@echo "Game: http://$(LAN_HOST):3001  API: http://$(LAN_HOST):8001"
	@set -e; \
	backend_pid=''; frontend_pid=''; \
	cleanup() { \
		[ -z "$$backend_pid" ] || kill "$$backend_pid" 2>/dev/null || true; \
		[ -z "$$frontend_pid" ] || kill "$$frontend_pid" 2>/dev/null || true; \
	}; \
	trap cleanup INT TERM EXIT; \
	BATTLE_API_CORS_ORIGINS="http://localhost:3001,http://127.0.0.1:3001,http://$(LAN_HOST):3001" .venv/bin/uvicorn battle_api.app:app --reload --host "$(LAN_HOST)" --port 8001 & backend_pid=$$!; \
	(cd web-ui && NEXT_PUBLIC_BATTLE_API_URL="http://$(LAN_HOST):8001" npm run dev -- --hostname "$(LAN_HOST)") & frontend_pid=$$!; \
	wait $$backend_pid $$frontend_pid
