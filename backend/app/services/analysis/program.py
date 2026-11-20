"""Control: ХөтөлбөрийнШинжилгээ (UC8). Хариуцагч: А9. Бүлэг 2: Зураг (UC8 дараалал), (хөтөлбөрийн үйл ажиллагаа).

    start                 ↔ эхлүүлэх(p, b, τ)
    _extract_skills       ↔ урЧадварЯлгах()            (А8)
    _merge_skills         ↔ урЧадваруудНэгтгэх()       (А8)
    _frequencies          ↔ давтамжТооцох()            f(k) = n(k) / N
    _propose_plo_cs2023   ↔ PLO_CS2023СаналГаргах()
    _propose_plo_skill    ↔ PLO_урЧадварСаналГаргах()
    _missing_skills       ↔ дутууУрЧадварТодорхойлох()
"""
from sqlalchemy.orm import Session

from app.models import AnalysisRun


class ProgramAnalysis:
    def __init__(self, db: Session):
        self.db = db

    def start(self, program_id: int, batch_id: int, min_frequency: float, user_id: int) -> AnalysisRun:
        raise NotImplementedError("А9")
