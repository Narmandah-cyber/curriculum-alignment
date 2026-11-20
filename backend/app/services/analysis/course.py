"""Control: ХичээлийнШинжилгээ (UC3). Хариуцагч: Б5. Бүлэг 2: Зураг (UC3 дараалал), (хичээлийн үйл ажиллагаа).

Аргын нэр ↔ Бүлэг 3-ын control класс:
    start              ↔ эхлүүлэх(v, арга)
    _prepare           ↔ текстБэлтгэх()
    _bloom_level       ↔ блумТүвшинТодорхойлох()
    _topic_score       ↔ сэдвийнОнооТооцох()
    _propose_link      ↔ холбоосСаналҮүсгэх()
    _classify_gap      ↔ түвшнийЗөрүүАнгилах()
    _mark_uncovered    ↔ хамрагдаагүйТэмдэглэх() / зорилгогүйТэмдэглэх()
    _save              ↔ үрДүнХадгалах()
"""
from sqlalchemy.orm import Session

from app.models import AnalysisRun


class CourseAnalysis:
    def __init__(self, db: Session):
        self.db = db

    def start(self, version_id: int, method: str, user_id: int, llm: bool = False) -> AnalysisRun:
        raise NotImplementedError("Б5")
