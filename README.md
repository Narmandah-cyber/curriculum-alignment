# Уялдаа — сургалтын уялдааг шинжлэх веб систем

Сургалтын хөтөлбөр, хичээлийн суралцахуйн үр дүн (PLO, CLO), агуулга, үнэлгээний уялдаа ба хамрах хүрээг
хэлний боловсруулалт (NLP)-аар шинжилж, саналыг багш баталгаажуулдаг веб систем.
ШУТИС-МХТС-ийн бакалаврын дипломын ажил — Г.Нармандах, О.Мэнд-Амар.

**Стек:** React + TypeScript (Vite) · FastAPI · SQLAlchemy / Alembic · PostgreSQL · Docker Compose

## Хурдан эхлэх (Docker)

```bash
git clone https://github.com/Narmandah-cyber/curriculum-alignment.git
cd curriculum-alignment
cp .env.example .env
docker compose up --build        # эсвэл: make up
```

| Хаяг | |
|---|---|
| http://localhost:5173 | Вэб (нэвтрэх: `admin@example.com` / `admin123`, `.env`-ээс солино) |
| http://localhost:8000/docs | API баримт (Swagger) |

Эхний асаалтад migration болон `data/seed/`-ийн өгөгдөл автоматаар ачаалагдана.

## Docker-гүй хөгжүүлэх

```bash
# 1) PostgreSQL-ийг л docker-оор
docker compose up -d db

# 2) Backend
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env
alembic upgrade head && python -m app.seed
uvicorn app.main:app --reload

# 3) Frontend (шинэ терминалд)
cd frontend && npm install && npm run dev
```

## Тест, шалгалт

```bash
cd backend && pytest -q && ruff check .      # PostgreSQL шаардлагагүй (SQLite)
cd frontend && npm run build
```
GitHub Actions (`.github/workflows/ci.yml`) PR бүр дээр эдгээрийг ажиллуулна.

## Бүтэц

```
backend/
  app/models/        «entity» — ERD-ийн 21 хүснэгт
  app/api/routers/   API (хэрэгжээгүй нь 501 буцаана, хариуцагчийн дугаартай)
  app/services/      «control» — nlp/, bloom/, analysis/, importers/
  alembic/           migration
  tests/
frontend/src/
  pages/             «boundary» — прототипийн 10 дэлгэц
  components/        Sidebar/TopBar, Button, Tag, BloomLevel
  api/               fetch, төрлүүд
data/seed/           Блумын үйл үг, CS2023 (жишиг)
data/samples/        CSV загварууд (ЖИШЭЭ өгөгдөл)
docs/                доорх баримтууд
```

## Баримтууд

| Файл | Юу байгаа |
|---|---|
| [docs/ASSIGNMENTS.md](docs/ASSIGNMENTS.md) | Хэн юу хийх, ажлын дугаар (А1…, Б1…), дараалал |
| [docs/LOOKUP.md](docs/LOOKUP.md) | Монгол ↔ англи нэр, класс ↔ хүснэгт ↔ модуль, UC → API → дэлгэц, enum, параметрүүд |
| [docs/API.md](docs/API.md) | Endpoint-уудын гэрээ |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Давхарга, шинжилгээний урсгал |
| [docs/DATA.md](docs/DATA.md) | CSV формат, нууцлал, тэмдэглэгээний заавар |
| [docs/ANNOTATION.md](docs/ANNOTATION.md) | СА3, СА4 тэмдэглэх дүрэм, туршилтын хэрэгсэл (`python -m app.evaluation`) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Git урсгал, код бичих дүрэм |

Холбоос: Figma прототип — https://www.figma.com/design/5srA4sxi0KJgr2MBffcn4g
