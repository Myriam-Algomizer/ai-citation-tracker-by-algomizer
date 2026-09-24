#!/usr/bin/env python3
"""Parse GEO log entries into runs.json, pages.json and validation.txt.

Usage:
  python parse_logs.py --logs <file-or-folder> [more ...] --config config.json --out workdir/

Accepts .md / .txt files holding one or more "=== GEO LOG ENTRY ===" blocks,
files saved as RTF by TextEdit or Word, entries wrapped in code fences, and raw
answers with no log block at all (counted from their inline links).
"""
import argparse, json, os, re
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qsl, urlencode

TRACKING = re.compile(r"^(utm_|fbclid$|gclid$|msclkid$|mc_cid$|mc_eid$|ref$|ref_src$|source$|srsltid$)", re.I)
FIELDS = ["brand", "competitors", "timestamp", "llm", "provider", "model", "mode", "prompt", "web_search_used", "brands_mentioned"]
RTF_DEST = {"fonttbl", "colortbl", "stylesheet", "info", "expandedcolortbl", "listtable", "listoverridetable", "generator", "pict"}


def strip_rtf(s):
    """Small RTF-to-text converter. Enough for TextEdit / Word exports of plain log text."""
    out, i, n = [], 0, len(s)
    stack, skip, uc, pending = [], False, 1, 0
    while i < n:
        c = s[i]
        if c == "{":
            stack.append((skip, uc)); i += 1
            if s.startswith("\\*", i): skip = True
        elif c == "}":
            if stack: skip, uc = stack.pop()
            i += 1
        elif c == "\\":
            i += 1
            if i >= n: break
            c2 = s[i]
            if c2 in "\\{}":
                if not skip: out.append(c2)
                i += 1
            elif c2 == "'":
                hx = s[i + 1:i + 3]; i += 3
                if pending: pending -= 1
                elif not skip:
                    try: out.append(bytes.fromhex(hx).decode("cp1252"))
                    except Exception: pass
            elif c2 in "\r\n":
                if not skip: out.append("\n")
                i += 1
            elif c2 == "~":
                if not skip: out.append(" ")
                i += 1
            elif c2.isalpha():
                m = re.match(r"([a-zA-Z]+)(-?\d+)? ?", s[i:]); word, num = m.group(1), m.group(2); i += m.end()
                if word in RTF_DEST: skip = True
                elif word == "uc" and num: uc = int(num)
                elif word == "u" and num:
                    if not skip:
                        cp = int(num); cp = cp + 65536 if cp < 0 else cp
                        out.append(chr(cp))
                    pending = uc
                elif word in ("par", "line"):
                    if not skip: out.append("\n")
                elif word == "tab":
                    if not skip: out.append("\t")
            else:
                i += 1
        else:
            if pending and c not in "\r\n": pending -= 1
            elif not skip and c not in "\r\n": out.append(c)
            i += 1
    return "".join(out)


def read_text(path):
    raw = open(path, "rb").read().decode("utf-8", errors="ignore")
    was_rtf = raw.lstrip().startswith("{\\rtf")
    return (strip_rtf(raw) if was_rtf else raw), was_rtf


def norm_url(u):
    u = u.strip().strip("<>").rstrip(".,;")
    s = urlsplit(u)
    host = s.netloc.lower()
    if host.startswith("www."): host = host[4:]
    q = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True) if not TRACKING.match(k)]
    return f"https://{host}{s.path.rstrip('/')}" + (("?" + urlencode(q)) if q else "")


def domain(u):
    return urlsplit(u).netloc


def parse_ts(t):
    if not t or "UNKNOWN" in t.upper(): return None
    t = t.strip()
    t = re.sub(r"\s+(UTC|GMT|Z)$", " +00:00", t)
    t = re.sub(r"([+-]\d{2})$", r"\1:00", t)
    t = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", t)
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            d = datetime.strptime(t, fmt)
            if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
            return d.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return None


def url_lines(section, with_count):
    """Lines look like: <n>. <url> | <title> | <times cited> | <names from the operator's list, or unknown>.
    The title can hold pipes, so fields are read from the right."""
    rows = []
    for line in section.splitlines():
        m = re.match(r"\s*\d+[.)]\s+(\S+)\s*(.*)$", line)
        if not (m and m.group(1).startswith("http")): continue
        parts = [x.strip() for x in m.group(2).strip().strip("|").split("|")]
        parts = [x for x in parts if x != ""]
        count, names = 1, ""
        if with_count and parts:
            if parts[-1].isdigit():
                count = int(parts.pop())
            elif len(parts) >= 2 and parts[-2].isdigit():
                names = parts.pop(); count = int(parts.pop())
        rows.append({"url": norm_url(m.group(1)), "title": " | ".join(parts), "count": count, "names": names})
    return rows


def parse_entry(block, issues):
    head, _, ans = block.partition("\nanswer:")
    meta = {}
    for k in FIELDS:
        m = re.search(rf"^\s*{k}\s*:[ \t]*(.*)$", head, flags=re.M | re.I)
        meta[k] = m.group(1).strip() if m else ""
    h = head + "\nanswer:"
    m = re.search(r"^\s*citations\s*:(.*?)(?=^\s*(?:sources_retrieved|answer)\s*:)", h, flags=re.M | re.S | re.I)
    listed = url_lines(m.group(1), True) if m else []
    m = re.search(r"^\s*sources_retrieved\s*:(.*?)(?=^\s*answer\s*:)", h, flags=re.M | re.S | re.I)
    retrieved = url_lines(m.group(1), False) if m else []
    if "<<<" not in ans: issues.append("opening <<< marker missing (tolerated)")
    ans = re.sub(r"^\s*<<<\s*", "", ans)
    ans = re.sub(r"\s*>>>\s*$", "", ans.strip()).strip()
    return meta, listed, retrieved, ans


def split_entries(text):
    text = re.sub(r"^\s*```[a-zA-Z]*\s*$", "", text, flags=re.M)
    return re.findall(r"=== GEO LOG ENTRY ===(.*?)(?:=== END ===|\Z)", text, flags=re.S)


def find_brands(ans, log_line, entities):
    """Known entities named in the answer, ordered by first appearance."""
    logged = [b.strip().lower() for b in log_line.split(";")] if log_line else []
    hits = []
    for e in entities:
        names = [e["name"]] + e.get("aliases", [])
        pos = None
        for nm in names:
            m = re.search(rf"(?<![\w-]){re.escape(nm)}(?!\w)", ans)
            if m and (pos is None or m.start() < pos): pos = m.start()
        if pos is None: continue
        if e.get("common_word"):
            bold = any(re.search(rf"\*\*\s*{re.escape(nm)}\s*[:.]?\s*\*\*", ans) for nm in names)
            linked = any(d in ans for d in e.get("domains", []))
            in_log = any(nm.lower() in logged for nm in names)
            if not (bold or linked or in_log): continue
        hits.append((pos, e["name"]))
    return [n for _, n in sorted(hits)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", nargs="+", required=True)
    ap.add_argument("--config", default="", help="optional. When absent, brand and competitors are read from the logs and config.json is written to --out")
    ap.add_argument("--out", required=True)
    ap.add_argument("--default-prompt", default="")
    ap.add_argument("--default-llm", default="")
    a = ap.parse_args()
    cfg = json.load(open(a.config)) if a.config else None

    files = []
    for p in a.logs:
        if os.path.isdir(p):
            files += sorted(os.path.join(p, f) for f in os.listdir(p) if f.lower().endswith((".md", ".txt", ".rtf", ".log")))
        else:
            files.append(p)

    report = []
    if cfg is None:
        seen_b, seen_c = Counter(), []
        for f in files:
            for b in split_entries(read_text(f)[0]):
                mb = re.search(r"^\s*brand\s*:[ \t]*(.+)$", b, flags=re.M | re.I)
                mc = re.search(r"^\s*competitors\s*:[ \t]*(.+)$", b, flags=re.M | re.I)
                if mb and "[" not in mb.group(1): seen_b[mb.group(1).strip()] += 1
                if mc and "[" not in mc.group(1): seen_c += [x.strip() for x in re.split(r"[;,]", mc.group(1)) if x.strip()]
        if not seen_b: raise SystemExit("No --config given and no 'brand:' line found in the logs. Ask the user for the brand and competitors.")
        if len(seen_b) > 1: report.append(f"logs name more than one brand: {dict(seen_b)}. Most frequent one used.")
        cfg = {"prepared_by": "", "brand": {"name": seen_b.most_common(1)[0][0], "aliases": [], "domains": []},
               "competitors": [{"name": c, "aliases": [], "domains": []} for c in dict.fromkeys(seen_c)]}
        os.makedirs(a.out, exist_ok=True)
        json.dump(cfg, open(os.path.join(a.out, "config.json"), "w"), indent=1, ensure_ascii=False)
        print(f"config.json written from the logs: brand={cfg['brand']['name']}, competitors={[c['name'] for c in cfg['competitors']]}. Add domains and aliases before build_sheet.py.")
    entities = [cfg["brand"]] + cfg.get("competitors", [])
    known = {n.lower() for e in entities for n in [e["name"]] + e.get("aliases", [])}

    runs = []
    for f in files:
        text, was_rtf = read_text(f)
        base = os.path.basename(f)
        blocks = split_entries(text)
        if was_rtf: report.append(f"{base}: RTF file (TextEdit or Word). Converted. Save as plain text to avoid this.")
        if not blocks:
            report.append(f"{base}: no log block. Treated as a raw answer.")
            blocks = [None]
        for b in blocks:
            issues = []
            if b is None:
                meta, listed, retrieved, ans = {k: "" for k in FIELDS}, [], [], text.strip()
            else:
                meta, listed, retrieved, ans = parse_entry(b, issues)
            inline = [norm_url(u) for u in re.findall(r"\]\((https?://[^)\s]+)\)", ans)]
            bare = re.sub(r"\]\(https?://[^)\s]+\)", "", ans)
            inline += [norm_url(u) for u in re.findall(r"https?://[^\s)\]>|\"']+", bare)]
            cites, kind = Counter(), {}
            if inline:
                for u in inline: cites[u] += 1; kind[u] = "Cited in text"
                for c in listed:
                    got = cites.get(c["url"], 0)
                    if got != c["count"]:
                        issues.append(f"log lists {c['count']} citation(s) for {c['url']}, answer text has {got}. Answer text used.")
            elif listed:
                for c in listed: cites[c["url"]] += c["count"]; kind[c["url"]] = "Listed by the model"
                issues.append("answer text holds no links. Counts come from the model's own list, which can be wrong.")
            for c in retrieved:
                if c["url"] not in cites: cites[c["url"]] = 1; kind[c["url"]] = "Retrieved by search"
            if not cites: issues.append("no citations or sources found")
            ts = parse_ts(meta["timestamp"])
            if not ts: issues.append("timestamp unknown")
            if not meta["model"] or "UNKNOWN" in meta["model"].upper(): issues.append("model unknown")
            logged = [x.strip() for x in meta["brands_mentioned"].split(";") if x.strip()]
            new = list(dict.fromkeys(x for x in logged if x.lower() not in known))
            runs.append({
                "file": base, "timestamp": ts, "timestamp_raw": meta["timestamp"] or "UNKNOWN",
                "llm": meta["llm"] or a.default_llm or "UNKNOWN", "model": meta["model"] or "UNKNOWN",
                "mode": meta["mode"] or "UNKNOWN", "prompt": meta["prompt"] or a.default_prompt or "UNKNOWN PROMPT",
                "web_search_used": meta["web_search_used"], "answer": ans,
                "brands": find_brands(ans, meta["brands_mentioned"], entities), "new_names": new,
                "citations": [{"url": u, "count": n, "kind": kind[u]} for u, n in cites.items()],
                "titles": {c["url"]: c["title"] for c in listed + retrieved if c["title"]},
                "page_names": {c["url"]: c["names"] for c in listed if c.get("names")},
                "issues": issues,
            })
            report += [f"{base}: {i}" for i in issues]

    real = {r["prompt"] for r in runs if r["prompt"] != "UNKNOWN PROMPT"}
    if len(real) == 1:
        only = next(iter(real))
        for r in runs:
            if r["prompt"] == "UNKNOWN PROMPT":
                r["prompt"] = only; report.append(f"{r['file']}: prompt missing. Assigned to the only prompt in this log set.")
    prompts = {}
    for r in runs:
        k = re.sub(r"\W+", " ", r["prompt"].lower()).strip()
        prompts.setdefault(k, {"id": f"P{len(prompts) + 1}", "text": r["prompt"]})
        r["prompt_id"] = prompts[k]["id"]
    runs.sort(key=lambda r: (r["timestamp"] is None, r["timestamp"] or "", r["file"]))
    for i, r in enumerate(runs, 1): r["id"] = f"R{i}"

    pages = {}
    for r in runs:
        for c in r["citations"]:
            p = pages.setdefault(c["url"], {"url": c["url"], "domain": domain(c["url"]), "title": "", "source": "", "type": "",
                                            "brand_mentioned": "not checked", "competitors_mentioned": "not checked", "citations": 0})
            p["citations"] += c["count"]
            if not p["title"] and r["titles"].get(c["url"]): p["title"] = r["titles"][c["url"]]
            p.setdefault("_names", []).append(r.get("page_names", {}).get(c["url"], ""))
    bname = cfg["brand"]["name"]
    for p in pages.values():
        said = " ; ".join(p.pop("_names")).lower()
        if not said.strip(" ;") or said.strip(" ;") in ("unknown", "none"): 
            if "none" in said and "unknown" not in said: p["brand_mentioned"], p["competitors_mentioned"] = "No (per model)", "none (per model)"
            continue
        def has(e): return any(re.search(rf"(?<!\w){re.escape(n.lower())}(?!\w)", said) for n in [e["name"]] + e.get("aliases", []))
        comps = [c["name"] for c in cfg.get("competitors", []) if has(c)]
        p["brand_mentioned"] = "Yes (per model)" if has(cfg["brand"]) else "No (per model)"
        p["competitors_mentioned"] = (", ".join(comps) + " (per model)") if comps else "none (per model)"
    page_list = sorted(pages.values(), key=lambda p: -p["citations"])

    os.makedirs(a.out, exist_ok=True)
    json.dump({"prompts": list(prompts.values()), "runs": runs}, open(os.path.join(a.out, "runs.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(page_list, open(os.path.join(a.out, "pages.json"), "w"), indent=1, ensure_ascii=False)
    open(os.path.join(a.out, "validation.txt"), "w").write("\n".join(report) + "\n")

    per = Counter((r["prompt_id"], r["llm"]) for r in runs)
    print(f"{len(runs)} runs, {len(prompts)} prompt(s), {len(page_list)} unique pages")
    for (p, l), n in sorted(per.items()): print(f"  {p} x {l}: {n} runs")
    print("validation notes:")
    for x in report or ["none"]: print("  -", x)


if __name__ == "__main__":
    main()
