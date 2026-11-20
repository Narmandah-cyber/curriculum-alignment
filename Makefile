.PHONY: up down logs test lint migrate revision seed shell-db

up:            ## Бүх системийг асаах
	docker compose up --build
down:
	docker compose down
logs:
	docker compose logs -f backend
test:          ## Backend тест
	cd backend && pytest -q
lint:
	cd backend && ruff check . && cd ../frontend && npm run typecheck
migrate:       ## Migration хэрэгжүүлэх
	docker compose exec backend alembic upgrade head
revision:      ## Шинэ migration: make revision m="add x"
	docker compose exec backend alembic revision --autogenerate -m "$(m)"
seed:
	docker compose exec backend python -m app.seed
shell-db:
	docker compose exec db psql -U uyaldaa uyaldaa
