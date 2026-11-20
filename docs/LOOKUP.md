# Лавлах хүснэгтүүд (lookup)

Дипломын бичвэр (Бүлэг 2–3) ба кодын нэршлийн харгалзаа. Код, хүснэгт, баганын нэр **англи**, бичвэр **монгол**.
Шинэ зүйл нэмбэл энд мөн нэмнэ.

## 1. Нэр томьёо

| Монгол (бичвэр) | Англи | Кодонд |
|---|---|---|
| Хөтөлбөр | program | `Program`, `programs` |
| Хөтөлбөрийн суралцахуйн үр дүн | program learning outcome | `Plo`, `plos` |
| Хичээл | course | `Course`, `courses` |
| Хичээлийн хувилбар | course version | `CourseVersion`, `course_versions` |
| Хичээлийн суралцахуйн үр дүн | course learning outcome | `Clo`, `clos` |
| Сургалтын элемент (лекц, лаборатори, бие даалт, шалгалт) | learning item (lecture, lab, assignment, exam) | `LearningItem`, `learning_items`, `type` |
| Ажлын зарлал / зарлалын багц | job posting / posting batch | `JobPosting`, `PostingBatch` |
| Ур чадвар | skill | `Skill`, `skills` |
| CS2023 нэгж | CS2023 knowledge unit | `Cs2023Unit`, `cs2023_units` |
| Шинжилгээ (нэг удаагийн ажиллагаа) | analysis run | `AnalysisRun`, `analysis_runs` |
| Холбоос | link | `Link`, `links` |
| Өөрчлөлтийн түүх | link history | `LinkHistory`, `link_history` |
| Блумын түвшин | Bloom level | `bloom_level` (1–6) |
| Түвшний эх (автомат / гараар) | level source | `level_source`: `auto` / `manual` |
| Түвшний зөрүү Δ | level gap | `level_gap` |
| Хамрагдаагүй CLO | uncovered CLO | — (тооцоолно) |
| Зорилгогүй элемент | unaligned item | — (тооцоолно) |
| Хөтөлбөрт дутуу ур чадвар | missing skill | `/runs/{id}/missing-skills` |

## 2. Классын харгалзаа (Бүлэг 2 → Бүлэг 3 → код)

Бүлэг 2-ын класс = Бүлэг 3-ын **«control»**. Өгөгдөл нь **«entity»** (ORM загвар).

| Бүлэг 2 / «control» | «entity» (`app/models`) | Хүснэгт | Backend модуль | Хариуцагч |
|---|---|---|---|---|
| Хэрэглэгч | `User`, `Role`, `UserRole` | users, roles, user_roles | `routers/auth.py`, `routers/users.py` | А2, А3 |
| Хөтөлбөр | `Program`, `ProgramCourse` | programs, program_courses | `routers/programs.py` | А4 |
| PLO | `Plo` | plos | `routers/programs.py` | А4 |
| Хичээл | `Course` | courses | `routers/courses.py` | Б2 |
| ХичээлийнХувилбар | `CourseVersion` | course_versions | `routers/courses.py` | Б3 |
| CLO | `Clo` | clos | `routers/courses.py` | Б2 |
| СургалтынЭлемент | `LearningItem` | learning_items | `routers/courses.py` | Б2 |
| CS2023Нэгж | `Cs2023Unit` | cs2023_units | `routers/admin.py` | А5 |
| ЗарлалынБагц | `PostingBatch` | posting_batches | `routers/postings.py`, `services/importers` | А7 |
| АжлынЗарлал | `JobPosting`, `PostingSkill` | job_postings, posting_skills | `routers/postings.py` | А7, А8 |
| УрЧадвар | `Skill` | skills | `services/analysis/program.py` | А8 |
| ХичээлийнШинжилгээ | `AnalysisRun` | analysis_runs | `services/analysis/course.py` | Б5 |
| ХөтөлбөрийнШинжилгээ | `AnalysisRun` | analysis_runs | `services/analysis/program.py` | А9 |
| Холбоос | `Link` | links | `routers/links.py` | А10 |
| ӨөрчлөлтийнТүүх | `LinkHistory` | link_history | `routers/links.py` | А10 |
| БлумынТоль | `BloomVerb` | bloom_verbs | `services/bloom/levels.py` | Б4 |
| ШинжилгээнийТохиргоо | `Setting` | settings | `routers/admin.py`, `core/config.py` | А3 |
| Тайлан | `Report` | reports | `routers/reports.py` | А12 |
| (нийтлэг NLP) | — | — | `services/nlp/` | А6 |

## 3. Хэрэглээний тохиолдол → API → дэлгэц

| UC | Нэр | Гол ФШ | API (`docs/API.md`) | Дэлгэц (Figma / `frontend/src/pages`) | Хариуцагч |
|---|---|---|---|---|---|
| — | Нэвтрэх | ФШ-01 | `POST /api/auth/login` | proto-01 / `LoginPage` | А2, Б1 |
| UC2 | Хичээлийн өгөгдөл бүртгэх | ФШ-04–06 | `/api/courses`, `/api/versions/{id}/clos|items|import` | proto-03 / `CourseDataPage` | Б2, Б6 |
| UC3 | Хичээлийн уялдааг үнэлэх | ФШ-10–13 | `POST /api/courses/{id}/analysis` | proto-04 / `AnalysisDialog` | Б5, Б6 |
| UC4 | Холбоос баталгаажуулах | ФШ-19–21 | `/api/links/{id}/confirm|strength|reject` | proto-05 / `MatrixPage` | А10, Б7 |
| UC5 | Хамрах хүрээний матриц харах | ФШ-22, 24 | `GET /api/versions/{id}/matrix`, `/gaps` | proto-02, 05, 06 | Б5, Б7 |
| UC6 | Хөтөлбөр, PLO бүртгэх | ФШ-03 | `/api/programs`, `/api/programs/{id}/plos` | proto-07 / `ProgramAnalysisPage` | А4, Б8 |
| UC7 | Ажлын зарлал оруулах | ФШ-08, 15 | `POST /api/programs/{id}/batches` | proto-08 / `PostingImportPage` | А7, Б8 |
| UC8 | Хөтөлбөрийн уялдааг үнэлэх | ФШ-15–18, 23 | `POST /api/programs/{id}/analysis` | proto-07 / `ProgramAnalysisPage` | А9, Б8 |
| UC9 | Тайлан татах | ФШ-25 | `POST /api/runs/{id}/reports` | (матриц дээрх товч) | А12 |
| UC10 | Хэрэглэгч, эрх удирдах | ФШ-02 | `/api/users` | proto-09 / `AdminPage` | А3, Б8 |
| UC11 | Жишиг өгөгдөл, тохиргоо удирдах | ФШ-09, 11 | `/api/settings`, `/api/bloom-verbs`, `/api/cs2023` | proto-09 / `AdminPage` | А3, А5, Б8 |
| UC12 | Хичээлийн хөтөлбөр шинэчлэх | ФШ-07 | `POST /api/courses/{id}/versions`, `/api/versions/compare` | proto-10 / `VersionHistoryPage` | Б3, Б6 |

## 4. Тогтсон утгууд (enum)

| Багана | Утгууд | Утга |
|---|---|---|
| `roles.name` | `teacher`, `coordinator`, `admin` | багш, хөтөлбөрийн хариуцагч, админ |
| `course_versions.status` | `active`, `history` | идэвхтэй, түүх (засахгүй) |
| `learning_items.type` | `lecture`, `lab`, `assignment`, `exam` | лекц, лаборатори, бие даалт, шалгалт |
| `*.level_source` | `auto`, `manual` | автомат, гараар |
| `analysis_runs.scope` | `course`, `program` | |
| `analysis_runs.method` / `links.method` | `rule`, `embedding`, `hybrid` | дүрэм, embedding, хосолсон |
| `analysis_runs.status` | `running`, `done`, `failed` | |
| `links.source_type` | `clo`, `plo` | |
| `links.target_type` | `item`, `plo`, `cs2023`, `skill` | |
| `links.strength` | `direct`, `partial` | шууд, хэсэгчлэн |
| `links.level_gap` | `match`, `below`, `above` | нийцсэн, доогуур, дээгүүр |
| `links.status` | `proposed`, `confirmed`, `rejected` | санал, баталгаажсан, татгалзсан |
| `reports.format` | `pdf`, `csv` | |

## 5. Шинжилгээний параметрүүд

| Тэмдэг | Утга | Тохиргооны түлхүүр | Анхны утга |
|---|---|---|---|
| θ | Холбоосын босго | `LINK_THRESHOLD` | 0.5 (жишээ; тэмдэглэгээтэй өгөгдлөөр сонгоно) |
| λ | Embedding-ийн жин, `s = λ·s_emb + (1−λ)·s_rule` | `HYBRID_LAMBDA` | 0.7 (жишээ) |
| τ | Ур чадварын давтамжийн доод хэмжээ, `f(k) = n(k)/N` | `min_skill_frequency` | 0.1 (жишээ) |
| Δ | `L(үнэлгээ) − L(CLO)` | — | `services/bloom/levels.py:level_gap` |
