.PHONY: dev backend frontend

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
