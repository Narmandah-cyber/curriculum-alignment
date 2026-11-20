"""Туршилтын хэрэгсэл (Бүлэг 4). Ажиллуулах: `cd backend && python -m app.evaluation <команд>`.

    export     Системд оруулсан хичээлээс хоосон тэмдэглэх файл гаргах
    agreement  Хоёр тэмдэглэгчийн тохироо (kappa)
    merge      Хоёр тэмдэглэгээг gold.csv болгон нэгтгэх (зөрүүтэйг хэлэлцүүлэхээр тэмдэглэнэ)
    evaluate   Системийн аргуудыг gold.csv-тэй харьцуулж results.md / .tex / .json бичих

Заавар: docs/ANNOTATION.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[3] / "data" / "private" / "annotations"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m app.evaluation", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("export", help="хоосон тэмдэглэх файл гаргах (DATABASE_URL-ийн ӨС-аас)")
    e.add_argument("courses", nargs="+", help="хичээлийн код(ууд), жишээ: ӨС201 ПХ305")
    e.add_argument("--out", type=Path, default=DEFAULT_DIR)
    e.add_argument("--dev-ratio", type=float, default=0.3, help="θ сонгох dev хэсгийн хувь (анхдагч 0.3)")

    for name, helptext in (("agreement", "хоёр тэмдэглэгчийн kappa"), ("merge", "gold.csv үүсгэх")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("task", choices=["links", "bloom"])
        s.add_argument("--dir", type=Path, default=DEFAULT_DIR)
        s.add_argument("--a", type=Path, help="анхдагч: <dir>/<task>_annotator_A.csv")
        s.add_argument("--b", type=Path, help="анхдагч: <dir>/<task>_annotator_B.csv")

    v = sub.add_parser("evaluate", help="системийн үнэлгээ")
    v.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    v.add_argument("--methods", nargs="+", default=["rule", "embedding", "hybrid"])
    v.add_argument("--out", type=Path, help="анхдагч: <dir>/results")
    v.add_argument("--lam", type=float, help="λ (анхдагч: тохиргооноос)")

    args = p.parse_args(argv)
    try:
        return COMMANDS[args.cmd](args)
    except (ValueError, FileNotFoundError) as err:
        print(f"Алдаа: {err}", file=sys.stderr)
        return 1


def _paths(args) -> tuple[Path, Path]:
    return (args.a or args.dir / f"{args.task}_annotator_A.csv", args.b or args.dir / f"{args.task}_annotator_B.csv")


def cmd_export(args) -> int:
    from app.db.session import SessionLocal
    from app.evaluation.annotation import export_templates
    with SessionLocal() as db:
        r = export_templates(db, args.courses, args.out, args.dev_ratio)
    print(f"СА3: {r.links} хос, СА4: {r.bloom} объект")
    for f in r.files:
        print(f"  {f}")
    print("Тэмдэглэгч бүр зөвхөн өөрийн файлыг бөглөнө (docs/ANNOTATION.md).")
    return 0


def cmd_agreement(args) -> int:
    from app.evaluation.evaluate import agreement
    from app.evaluation.report import agreement_md
    print(agreement_md(agreement(*_paths(args), args.task)))
    return 0


def cmd_merge(args) -> int:
    from app.evaluation.annotation import merge
    out = args.dir / f"{args.task}_gold.csv"
    r = merge(*_paths(args), args.task, out)
    print(f"{out}: {r['rows']} мөр, зөрүүтэй {r['disputed']}, kappa {r['kappa']:.3f}")
    if r["disputed"]:
        print("disputed=1 мөрүүдийг хамтдаа хэлэлцэж, хоосон шошгыг бөглөнө үү. Дараа нь `evaluate`.")
    return 0


def cmd_evaluate(args) -> int:
    from app.core.config import get_settings
    from app.evaluation.evaluate import agreement, evaluate_bloom, evaluate_gaps, evaluate_links, gold_ready
    from app.evaluation.report import write_report
    s = get_settings()
    links_gold, bloom_gold = args.dir / "links_gold.csv", args.dir / "bloom_gold.csv"
    if not links_gold.exists() and not bloom_gold.exists():
        raise FileNotFoundError(f"{args.dir}-д links_gold.csv эсвэл bloom_gold.csv алга (эхлээд `merge`)")
    agreements, links, bloom, gaps = [], None, None, None
    for task in ("links", "bloom"):
        a, b = args.dir / f"{task}_annotator_A.csv", args.dir / f"{task}_annotator_B.csv"
        if a.exists() and b.exists():
            agreements.append(agreement(a, b, task))
    if links_gold.exists():
        gold_ready(links_gold, "links")
        links = evaluate_links(links_gold, args.methods, lam=args.lam if args.lam is not None else s.hybrid_lambda,
                               default_threshold=s.link_threshold)
    if bloom_gold.exists():
        gold_ready(bloom_gold, "bloom")
        bloom = evaluate_bloom(bloom_gold)
    if links and bloom:
        gaps = evaluate_gaps(links_gold, bloom_gold)
    files = write_report(args.out or args.dir / "results", agreements=agreements, links=links, bloom=bloom, gaps=gaps)
    print(files[0].read_text(encoding="utf-8"))
    print("Файлууд: " + ", ".join(str(f) for f in files))
    return 0


COMMANDS = {"export": cmd_export, "agreement": cmd_agreement, "merge": cmd_merge, "evaluate": cmd_evaluate}

if __name__ == "__main__":
    raise SystemExit(main())
