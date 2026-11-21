// Энгийн CSV задлагч (хашилттай талбар, мөр доторх таслал, "" escape). Файлыг илгээхээс өмнө урьдчилан шалгахад.
export function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], field = "", quoted = false;
  const s = text.replace(/^﻿/, "");
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (quoted) {
      if (c === '"' && s[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"') quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && s[i + 1] === "\n") i++;
      row.push(field); rows.push(row); row = []; field = "";
    } else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows.filter((r) => r.some((x) => x.trim() !== ""));
}

/** Толгой, заавал баганатай мөрийг шалгана: { rows: тоо, errors: [{row, reason}], missing: [багана] } */
export function checkCsv(text: string, required: string[]) {
  const [head = [], ...body] = parseCsv(text);
  const cols = head.map((h) => h.trim().toLowerCase());
  const missing = required.filter((r) => !cols.includes(r));
  const errors: { row: number; reason: string }[] = [];
  if (!missing.length) {
    body.forEach((r, i) => {
      const empty = required.filter((c) => !(r[cols.indexOf(c)] ?? "").trim());
      if (empty.length) errors.push({ row: i + 2, reason: `Хоосон: ${empty.join(", ")}` });
    });
  }
  return { rows: body.length, errors, missing };
}
