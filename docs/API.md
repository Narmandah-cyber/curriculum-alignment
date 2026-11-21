# API гэрээ

Backend асаахад бүрэн баримт `http://localhost:8000/docs` (Swagger) дээр гарна. Энэ файл нь хоёр гишүүний **тохиролцоо**: endpoint нэмэх, өөрчлөхдөө энд мөн засна.

Бүх хүсэлт (нэвтрэхээс бусад) `Authorization: Bearer <token>` толгойтой. Алдаа: `{"detail": "..."}`. Хэрэгжээгүй endpoint `501` буцаана.

## Бэлэн

| Арга | Зам | Тайлбар |
|---|---|---|
| GET | `/api/health` | Ажиллаж буй эсэх |
| POST | `/api/auth/login` | form: `username`=имэйл, `password` → `{access_token}` |
| GET | `/api/auth/me` | Нэвтэрсэн хэрэглэгч, үүргүүд |
| GET / POST | `/api/programs` | Хөтөлбөрүүд / үүсгэх (coordinator, admin) |
| GET / POST | `/api/programs/{id}/plos` | PLO жагсаах / нэмэх (coordinator) |

## users

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| GET | `/api/users` | А3 | Бүх хэрэглэгч (админ) |
| POST | `/api/users` | А3 | Хэрэглэгч үүсгэх, үүрэг оноох |
| PATCH | `/api/users/{user_id}` | А3 | мэдээлэлЗасах(), идэвхгүйБолгох() |
| POST | `/api/users/{user_id}/roles/{role}` | А3 | үүрэгОноох() |
| DELETE | `/api/users/{user_id}/roles/{role}` | А3 | үүрэгЦуцлах() |

## courses

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| GET | `/api/courses` | Б2 | Багшийн хичээлүүд (хянах самбар) |
| POST | `/api/courses` | Б2 | Хичээл үүсгэх + анхны хувилбар |
| GET | `/api/courses/{course_id}` | Б2 |  |
| PATCH | `/api/courses/{course_id}` | Б2 |  |
| DELETE | `/api/courses/{course_id}` | Б2 |  |
| GET | `/api/courses/{course_id}/versions` | Б3 | хувилбаруудАвах() |
| POST | `/api/courses/{course_id}/versions` | Б3 | хөтөлбөрШинэчлэх(хичээлийнЖил): хуулах → түүхэндШилжүүлэх → идэвхжүүлэх |
| GET | `/api/versions/compare` | Б3 | ?v1=&v2= → ялгааТооцох() |
| GET | `/api/versions/{version_id}/clos` | Б2 |  |
| POST | `/api/versions/{version_id}/clos` | Б2 | засахБоломжтойЭсэх() шалгана (түүх бол 409) |
| PATCH | `/api/clos/{clo_id}` | Б2 | текстЗасах(), блумТүвшинЗасах() (ФШ-21) |
| DELETE | `/api/clos/{clo_id}` | Б2 |  |
| GET | `/api/versions/{version_id}/items` | Б2 |  |
| POST | `/api/versions/{version_id}/items` | Б2 |  |
| PATCH | `/api/items/{item_id}` | Б2 |  |
| DELETE | `/api/items/{item_id}` | Б2 |  |
| POST | `/api/versions/{version_id}/import` | Б2 | CSV импорт (ФШ-06), алдаатай мөрийн жагсаалт буцаана |

Оролт, гаралт (Б2, Б3 — хэрэгжсэн; бүрэн схем: `/docs`):

- `GET /api/courses?mine=true` → `CourseOut[]`: `{id, code, name, credits, teacher_id, active_version: VersionOut, summary: {analyzed, coverage, proposed, uncovered_clos, level_gaps}}`. `mine=false` — coordinator/admin бүх хичээл.
- `POST /api/courses` (зөвхөн `teacher`): `{code, name, credits, academic_year: "2026-2027"}` → v1 идэвхтэй хувилбартай `CourseOut`. Код давхардвал 409.
- `VersionOut`: `{id, course_id, version_no, academic_year, status, previous_version_id, created_at, clo_count, item_count}`.
- `POST /api/courses/{id}/versions`: `{academic_year}` → шинэ `VersionOut`; тухайн оны хувилбар байвал 409.
- `GET /api/versions/compare?v1=&v2=` → `{v1, v2, added, modified, removed, changes: [{change, kind: clo|item, key, old_text, new_text}]}`. CLO-г кодоор, элементийг гарчгаар тааруулна.
- `POST /api/versions/{id}/clos`: `{code, text, bloom_level?}` — `bloom_level` өгвөл `level_source=manual`, үгүй бол автомат.
- `PATCH /api/clos/{id}`: `{code?, text?, bloom_level?}` — `bloom_level: null` бол автомат руу буцна (ФШ-21).
- `CloOut` / `ItemOut` нэмэлт талбар: `level_reason` — түвшний үндэслэл (ФШ-11): «Үйл үг: «зохиох»», «Ангилагч: итгэл 0.41», «Гараар зассан».
- `POST /api/versions/{id}/items`: `{type, title, text, question_text?, bloom_level?}`.
- `POST /api/versions/{id}/import?kind=clo|item` (multipart `file`) → `{imported, errors: [{row, reason}]}`. Багана дутуу бол 400.
- Эрх (ФБШ-04): засах — зөвхөн хичээлийн багш (403); харах — багш, coordinator, admin. Түүх хувилбарыг засвал 409.

## postings

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| GET | `/api/programs/{program_id}/batches` | А7 |  |
| POST | `/api/programs/{program_id}/batches` | А7 | CSV → мөр шалгах → хувийн мэдээлэл арилгах → хадгалах |
| GET | `/api/batches/{batch_id}/postings` | А7 | Ялгасан ур чадвартай нь |

## analysis

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| POST | `/api/courses/{course_id}/analysis` | Б5 | body: {method, llm} → AnalysisRun (арын ажил) |
| POST | `/api/programs/{program_id}/analysis` | А9 | body: {batch_id, min_frequency} |
| GET | `/api/runs/{run_id}` | А11 | Төлөв, явц (%) |
| GET | `/api/versions/{version_id}/matrix` | Б5 | CLO × элемент (ФШ-22) |
| GET | `/api/versions/{version_id}/gaps` | Б5 | Хамрагдаагүй CLO, зорилгогүй элемент, түвшний зөрүү (ФШ-12, 13) |
| GET | `/api/programs/{program_id}/matrix` | А9 | ?kind=plo-course|plo-cs2023 (ФШ-23) |
| GET | `/api/runs/{run_id}/missing-skills` | А9 | Хөтөлбөрт дутуу ур чадвар (ФШ-18) |

Хичээлийн шинжилгээ (Б5 — хэрэгжсэн):

- `POST /api/courses/{id}/analysis`: `{method: rule|embedding|hybrid, llm: bool}` → **202** `{id, status: "running", progress, version_id, threshold, notice}`. Арын ажлаар (BackgroundTasks) гүйнэ. CLO эсвэл элемент байхгүй бол 409. Embedding загвар бэлэн биш бол дүрмийн аргаар гүйж, `method=rule` болно.
- Frontend явцыг `GET /api/runs/{id}`-ээр асууна; А11 хэрэгжээгүй (501) үед матрицын `run` талбараар.
- `GET /api/versions/{id}/matrix` → `{version, clos, items, cells: [{link_id, clo_id, item_id, score, strength, status, level_gap, method, matched_terms, llm_explanation}], run, proposed, confirmed}`. Татгалзсан холбоос орохгүй.
- `GET /api/versions/{id}/clo-plo` → `{version, programs, plos, clos, cells: [{link_id, clo_id, plo_id, score, strength, status, level_gap, method, matched_terms}], proposed, confirmed}` (ФШ-14). PLO нь `program_courses`-аар (А4 `attach_course`) хичээл хамааруулсан хөтөлбөрүүдийнх. Δ = L(CLO) − L(PLO). Хичээлийн шинжилгээ (`POST /courses/{id}/analysis`) CLO–элемент ба CLO–PLO саналыг хамт гаргана.
- Бүх `/versions/{id}/...` унших endpoint түүх хувилбарт ч ажиллана (ФШ-07, зөвхөн харах).
- `GET /api/versions/{id}/gaps` → `{match, below, above, unaligned, level_gaps: [{link_id, clo, item, level_gap, status, score}], uncovered_clos: [CloOut + has_proposed], unaligned_items}`. Үнэлгээний элемент = lab, assignment, exam. Хамрагдаагүй = баталгаажсан холбоосгүй (ФШ-13).

## links

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| GET | `/api/links/{link_id}` | А10 | үндэслэлАвах(): хоёр талын текст, оноо, таарсан үг, түвшин |
| POST | `/api/links` | А10 | гараарҮүсгэх() |
| POST | `/api/links/{link_id}/confirm` | А10 | батлах() |
| POST | `/api/links/{link_id}/strength` | А10 | хүчӨөрчлөх() |
| POST | `/api/links/{link_id}/reject` | А10 | татгалзах() |
| GET | `/api/links/{link_id}/history` | А10 | холбоосынТүүхАвах() |

Frontend (Б7) дуудаж буй оролт — **А10 хэрэгжүүлэхдээ баталгаажуулна уу**:
`POST /api/links` `{source_type, source_id, target_type, target_id, strength}`; `POST /api/links/{id}/strength` `{strength: direct|partial}`; `confirm`, `reject` — body-гүй. Амжилттай бол ямар ч JSON буцааж болно (frontend матрицыг дахин ачаална).

## reports

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| POST | `/api/runs/{run_id}/reports` | А12 | ?format=pdf|csv |
| GET | `/api/reports/{report_id}/download` | А12 |  |

## admin

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| GET | `/api/settings` | А3 |  |
| PUT | `/api/settings/{key}` | А3 | утгаШалгах() → утгаОноох() |
| GET | `/api/bloom-verbs` | А3 |  |
| POST | `/api/bloom-verbs` | А3 |  |
| DELETE | `/api/bloom-verbs/{verb_id}` | А3 |  |
| POST | `/api/cs2023/import` | А5 | жишигАчаалах(файл) |
| GET | `/api/cs2023` | А5 | ?area=&q= |

## Б8-ийн хүлээж буй хариу (санал)

Хөтөлбөрийн шинжилгээ (proto-07), зарлал оруулах (proto-08), админ (proto-09) дэлгэцүүд доорх хэлбэрийг хүлээж байна (`frontend/src/api/types.ts`, `api/program.ts`). Endpoint `501` буцаавал дэлгэц "хэрэгжүүлэгдэж байна" мэдэгдэл харуулна. **А хэрэгжүүлэхдээ энэ хэлбэрийг баталгаажуулах эсвэл өөрчилж, энд засна уу.**

| Endpoint | Хариуцагч | Хүсэлт | Хариу |
|---|---|---|---|
| `POST /api/programs/{id}/courses/{course_id}` | А4 | body-гүй | дурын JSON |
| `GET /api/programs/{id}/batches` | А7 | — | `[{id, program_id, name, created_at, posting_count}]` |
| `POST /api/programs/{id}/batches` | А7 | multipart: `name`, `file` (CSV, заавал `title`, `text`; сонголттой `posted_date`, `source`) | `{id, program_id, name, created_at, posting_count, errors: [{row, reason}]}` |
| `GET /api/batches/{id}/postings` | А7 | — | `[{id, title, posted_date, source, skills: [str], status: processed\|no_skills\|pending}]` |
| `POST /api/programs/{id}/analysis` | А9 | `{batch_id, min_frequency?}` | AnalysisRun (`{id, status, progress, ...}`), явцыг `GET /api/runs/{id}`-ээр асууна |
| `GET /api/programs/{id}/matrix?kind=plo-cs2023\|plo-course` | А9 | — | `{kind, rows: [{id, code, name}], cols: [{id, code, name}], cells: [{link_id, row_id, col_id, score, strength, status}], run, covered_cols?}` |
| `GET /api/runs/{id}/missing-skills` | А9 | — | `{run_id, total_postings, extracted_skills, market_coverage, min_frequency, skills: [{skill, frequency, count}]}` (`frequency` 0–1) |
| `GET /api/users` | А3 | — | `[User]` (`{id, email, full_name, is_active, roles}`) |
| `POST /api/users` | А3 | `{full_name, email, password, roles: [teacher\|coordinator\|admin]}` | `User` |
| `PATCH /api/users/{id}` | А3 | `{full_name?, email?, is_active?}` | `User` |
| `POST`/`DELETE /api/users/{id}/roles/{role}` | А3 | body-гүй | дурын JSON |
| `GET /api/settings` | А3 | — | `[{key, value}]`; түлхүүр: `embedding_model`, `link_threshold`, `direct_threshold`, `llm_enabled` |
| `PUT /api/settings/{key}` | А3 | `{value: str}` | `{key, value}`; буруу утгад 422 (босго 0–1, `link_threshold < direct_threshold`) |
| `GET`/`POST /api/bloom-verbs` | А3 | `{verb, level}` | `[{id, verb, level}]` / `{id, verb, level}` |
| `DELETE /api/bloom-verbs/{id}` | А3 | — | 204 |
| `GET /api/cs2023` | А5 | — | `[{id, area, code, title}]` |
