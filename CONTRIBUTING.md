# Хамтран ажиллах дүрэм

## Git урсгал

1. `main`-д шууд push хийхгүй. Ажил бүрт салбар: `feat/A6-nlp-core`, `fix/B2-csv-error`, `docs/...`.
2. Ажлын дугаар `docs/ASSIGNMENTS.md`-ээс. Commit: `А6: косинус ижил төстэй байдал нэмэв`.
3. Pull request нээж, **нөгөө гишүүн** хянаж батална. CI ногоон байх ёстой.
4. Merge хийсний дараа салбараа устгаж, `ASSIGNMENTS.md`-д `[x]` тэмдэглэнэ.

```bash
git switch main && git pull
git switch -c feat/A6-nlp-core
# ... ажил ...
git push -u origin feat/A6-nlp-core      # → GitHub дээр PR нээх
```

## Дууссан гэж үзэх шалгуур

- Тест бичсэн, `pytest` / `npm run build` амжилттай
- Шинэ endpoint бол `docs/API.md`, шинэ нэр томьёо бол `docs/LOOKUP.md` шинэчилсэн
- ORM загвар өөрчилсөн бол migration: `make revision m="..."` (eсвэл `alembic revision --autogenerate -m "..."`)
- Дэлгэц бол Figma-тай харьцуулсан зураг PR-д хавсаргасан

## Код

- **Python:** `ruff check .`; функц, классын docstring монголоор болно, нэр англиар. Control классын үйлдэлтэй холбогдох функцэд Бүлэг 3-ын нэрийг docstring-д бичнэ (`""" ... ↔ сэдвийнОнооТооцох()"""`).
- **TypeScript:** `strict`; API-ийн төрлийг `src/api/types.ts`-д `backend/app/schemas.py`-тэй ижил байлгана.
- Нууц үг, токен, бодит өгөгдлийг commit хийхгүй (`.env`, `data/private/`).
- Тоон утгыг (босго, жин) кодонд шууд бичихгүй — `settings` / `.env`-ээс уншина.
