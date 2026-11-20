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

## links

| Арга | Зам | Хариуцагч | Тайлбар |
|---|---|---|---|
| GET | `/api/links/{link_id}` | А10 | үндэслэлАвах(): хоёр талын текст, оноо, таарсан үг, түвшин |
| POST | `/api/links` | А10 | гараарҮүсгэх() |
| POST | `/api/links/{link_id}/confirm` | А10 | батлах() |
| POST | `/api/links/{link_id}/strength` | А10 | хүчӨөрчлөх() |
| POST | `/api/links/{link_id}/reject` | А10 | татгалзах() |
| GET | `/api/links/{link_id}/history` | А10 | холбоосынТүүхАвах() |

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
