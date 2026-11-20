"""Үр дүнг Бүлэг 4-т оруулах хэлбэрээр бичих: Markdown, LaTeX хүснэгт, P–R муруйн CSV, JSON."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path

from app.evaluation.metrics import PRF

METHOD_NAMES = {"rule": "Дүрэмд суурилсан", "embedding": "Embedding", "hybrid": "Хосолсон"}
GAP_NAMES = {"below": "Доогуур", "match": "Нийцсэн", "above": "Дээгүүр"}


def f(x: float | None, nd: int = 3) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


def _jsonable(o):
    if isinstance(o, PRF):
        return {"tp": o.tp, "fp": o.fp, "fn": o.fn, "precision": o.precision, "recall": o.recall, "f1": o.f1}
    if is_dataclass(o):
        return {k: _jsonable(v) for k, v in asdict(o).items()} | (
            {k: _jsonable(getattr(o, k)) for k in ("test", "test_at_default") if hasattr(o, k)})
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, list | tuple):
        return [_jsonable(v) for v in o]
    return o


def agreement_md(r: dict) -> str:
    lines = [f"### Тэмдэглэгчдийн тохироо — {'СА3 холбоос' if r['task'] == 'links' else 'СА4 Блумын түвшин'}", "",
             f"- Мөрийн тоо: {r['n']}",
             f"- Санал нийлсэн хувь (p_o): {f(r['observed'])}",
             f"- Cohen's kappa: **{f(r['kappa'])}** ({r['interpretation']}, Landis & Koch)"]
    if "kappa_binary" in r:
        lines.append(f"- Kappa (холбоотой эсэх, хүчийг тооцохгүй): {f(r['kappa_binary'])}")
    if "adjacent" in r:
        lines.append(f"- ±1 түвшний зөрүүтэй тохироо: {f(r['adjacent'])}")
    lines += [f"- Зөрүүтэй мөр: {len(r['disagreements'])}", "", "Будлиантын матриц (мөр = A, багана = B):", "",
              "| A \\ B | " + " | ".join(r["labels"]) + " |", "|---" * (len(r["labels"]) + 1) + "|"]
    lines += [f"| {lab} | " + " | ".join(str(x) for x in row) + " |" for lab, row in zip(r["labels"], r["confusion"], strict=False)]
    return "\n".join(lines) + "\n"


def links_md(r: dict) -> str:
    lines = ["### СА3: CLO ↔ сургалтын элементийн холбоос", "",
             f"Нийт хос: {r['n']} (dev {r['n_dev']}, test {r['n_test']}); алтан стандартаар холбоотой: {r['positives']}.",
             "θ-г dev хэсэгт F1-ээр сонгож, test хэсэгт тайлагнав." + (f" **Анхаар:** {r['note']}" if r["note"] else ""), "",
             f"| Арга | θ (dev) | P | R | F1 | F1 @ θ={r['default_threshold']} | 3 ангиллын macro-F1 | κ (систем–мэргэжилтэн) | Хугацаа (с) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for m in r["results"]:
        name = METHOD_NAMES.get(m.method, m.method)
        if not m.available:
            lines.append(f"| {name} | — | — | — | — | — | — | — | боломжгүй: {m.reason} |")
            continue
        lines.append(f"| {name} | {f(m.threshold, 2)} | {f(m.test.precision)} | {f(m.test.recall)} | **{f(m.test.f1)}** | "
                     f"{f(m.test_at_default.f1)} | {f(m.strength_macro_f1)} | {f(m.kappa_vs_gold)} | {f(m.seconds, 2)} |")
    return "\n".join(lines) + "\n"


def bloom_md(r: dict) -> str:
    lines = ["### СА4: Блумын түвшин", "",
             f"- Объект: {r['n']}; macro-F1: **{f(r['macro_f1'])}**; нарийвчлал: {f(r['accuracy'])}; "
             f"κ: {f(r['kappa'])}; ±1 тохироо: {f(r['adjacent'])}; хугацаа: {f(r['seconds'], 2)} с"]
    for src, name in (("verb", "толиор"), ("classifier", "ангилагчаар")):
        s = r["by_source"][src]
        lines.append(f"- {name} тогтоосон: {s['n']} объект, нарийвчлал {f(s['accuracy'])}")
    for k, name in (("clo", "CLO"), ("assessment", "Үнэлгээний элемент")):
        if k in r["subsets"]:
            lines.append(f"- {name}: {r['subsets'][k]['n']} объект, macro-F1 {f(r['subsets'][k]['macro_f1'])}")
    labs = r["labels"]
    lines += ["", "| Түвшин | " + " | ".join(labs) + " |", "|---" * (len(labs) + 1) + "|",
              "| F1 | " + " | ".join(f(r["per_class_f1"][x], 2) for x in labs) + " |", "",
              "Будлиантын матриц (мөр = мэргэжилтэн, багана = систем):", "",
              "| | " + " | ".join(labs) + " |", "|---" * (len(labs) + 1) + "|"]
    lines += [f"| {lab} | " + " | ".join(str(x) for x in row) + " |" for lab, row in zip(labs, r["confusion"], strict=False)]
    return "\n".join(lines) + "\n"


def gaps_md(r: dict) -> str:
    if not r.get("n"):
        return "### СА4: Түвшний зөрүү\n\nХарьцуулах хос алга (холбоотой CLO–үнэлгээний хосын түвшин тэмдэглэгдээгүй).\n"
    labs = ["below", "match", "above"]
    lines = ["### СА4: Түвшний зөрүү (Δ)", "",
             f"Алтан стандартаар холбоотой CLO–үнэлгээний {r['n']} хос. Нарийвчлал {f(r['accuracy'])}, "
             f"macro-F1 **{f(r['macro_f1'])}**, κ {f(r['kappa'])}.",
             f"«Доогуур» (үнэлгээ CLO-оос доогуур) илрүүлэлт: P {f(r['below'].precision)}, R {f(r['below'].recall)}, "
             f"F1 {f(r['below'].f1)}.", "", "| мэргэжилтэн \\ систем | " + " | ".join(GAP_NAMES[x] for x in labs) + " |",
             "|---|---|---|---|"]
    lines += [f"| {GAP_NAMES[lab]} | " + " | ".join(str(x) for x in row) + " |" for lab, row in zip(labs, r["confusion"], strict=False)]
    return "\n".join(lines) + "\n"


def links_tex(r: dict) -> str:
    rows = []
    for m in r["results"]:
        name = METHOD_NAMES.get(m.method, m.method)
        if m.available:
            rows.append(f"{name} & {m.threshold:.2f} & {m.test.precision:.3f} & {m.test.recall:.3f} & "
                        f"\\textbf{{{m.test.f1:.3f}}} & {m.strength_macro_f1:.3f} & {m.seconds:.2f} \\\\ \\hline")
        else:
            rows.append(f"{name} & \\multicolumn{{6}}{{c|}}{{боломжгүй}} \\\\ \\hline")
    return ("\\begin{table}[H]\n\\centering\n\\caption{СА3: холбоос тодорхойлох аргуудын үр дүн (test хэсэг)}\n"
            "\\label{tab:sa3-results}\n\\begin{tabular}{|l|c|c|c|c|c|c|}\n\\hline\n"
            "Арга & $\\theta$ & P & R & F1 & macro-F1 (3 ангилал) & Хугацаа (с) \\\\ \\hline\n"
            + "\n".join(rows) + "\n\\end{tabular}\n\\end{table}\n")


def bloom_tex(r: dict) -> str:
    labs = r["labels"]
    return ("\\begin{table}[H]\n\\centering\n\\caption{СА4: Блумын түвшин тодорхойлолтын үр дүн}\n"
            "\\label{tab:sa4-results}\n\\begin{tabular}{|l|" + "c|" * len(labs) + "}\n\\hline\n"
            "Түвшин & " + " & ".join(labs) + " \\\\ \\hline\n"
            "F1 & " + " & ".join(f"{r['per_class_f1'][x]:.2f}" for x in labs) + " \\\\ \\hline\n"
            "\\end{tabular}\n\\\\[4pt] macro-F1 = " + f"{r['macro_f1']:.3f}" + ", $\\kappa$ = " + f"{r['kappa']:.3f}"
            + "\n\\end{table}\n")


def write_report(out_dir: Path, *, agreements: list[dict] = (), links: dict | None = None,
                 bloom: dict | None = None, gaps: dict | None = None) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    md = ["# Туршилтын үр дүн", ""]
    tex = []
    md += [agreement_md(a) for a in agreements]
    if links:
        md.append(links_md(links))
        tex.append(links_tex(links))
        for m in links["results"]:
            if m.available:
                with open(out_dir / f"curve_{m.method}.csv", "w", encoding="utf-8", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(m.curve[0]))
                    w.writeheader()
                    w.writerows(m.curve)
    if bloom:
        md.append(bloom_md(bloom))
        tex.append(bloom_tex(bloom))
    if gaps:
        md.append(gaps_md(gaps))
    files = [out_dir / "results.md", out_dir / "results.tex", out_dir / "results.json"]
    files[0].write_text("\n".join(md), encoding="utf-8")
    files[1].write_text("\n".join(tex), encoding="utf-8")
    files[2].write_text(json.dumps(_jsonable({"agreements": list(agreements), "links": links, "bloom": bloom,
                                              "gaps": gaps}), ensure_ascii=False, indent=2), encoding="utf-8")
    return files
