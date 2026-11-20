# Архитектур

```
Хөтөч (React, :5173) ──/api──▶ FastAPI (:8000) ──▶ PostgreSQL (:5432)
                                   │
                                   └─▶ шинжилгээний хөдөлгүүр (services/) ──▶ embedding загвар (LaBSE / E5)
                                                                          └─▶ LLM (сонголттой, ФШ-26)
```

| Давхарга | Бүлэг 3-ын ангилал | Хаана |
|---|---|---|
| Дэлгэц | «boundary» | `frontend/src/pages`, `components` |
| API | (boundary ↔ control) | `backend/app/api/routers` |
| Логик | «control» | `backend/app/services`, router доторх энгийн CRUD |
| Өгөгдөл | «entity» | `backend/app/models` → `alembic/versions` |

Дүрэм: дэлгэц зөвхөн API-г дуудна; router нь бизнес логикийг `services/`-д шилжүүлнэ; шинжилгээ entity-г getter/setter-ээр (ORM attribute) уншиж, бичнэ.

## Шинжилгээний урсгал (UC3)

1. `POST /api/courses/{id}/analysis` → `AnalysisRun(status=running)` үүсгээд арын ажил эхлүүлнэ (ФБШ-02).
2. `CourseAnalysis.start()`: текст бэлтгэх → Блумын түвшин → хос бүрийн оноо → `s ≥ θ` бол `Link(status=proposed)` → Δ → хамрагдаагүй.
3. Баталгаажсан холбоосыг дахин бичихгүй (UC3 5а).
4. Frontend `GET /api/runs/{id}`-г явц дуусах хүртэл асууна.

Үйл ажиллагааны диаграмууд: диплом Бүлэг 2 (Зураг: хичээлийн / хөтөлбөрийн шинжилгээ, өгөгдөл импорт, хувилбар).
