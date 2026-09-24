---
name: geo-prompt-sampler
description: Turn repeated runs of the same GEO / AI-visibility prompt into one aggregated citation report. The operator asks a prompt several times in ChatGPT, Claude, Perplexity, Gemini or AI Overview, logs each answer with a standard capture prompt, and this skill merges the logs into an Excel workbook (one tab per LLM, one tab for all LLMs, one tab with the full answers) plus a short summary of brand mention rates, top cited pages and domains, content types, competitor presence and run-to-run stability. Use this skill whenever the user uploads or pastes GEO log entries or saved LLM answers and wants them aggregated, asks for an AI citation analysis, a citation sheet, brand mentions across runs, which pages or domains the LLMs cite for a prompt, or asks for the capture prompt, the log format, or how many runs they need. Trigger on "GEO log", "log entries", "runs", "aggregate the answers", "citation analysis", "capture prompt", "prompt sampling", even when the user does not name the skill.
---

# GEO prompt sampler

One LLM answer is one draw. Ask the same question eight times and the brands mostly hold while the sources change almost every time. This skill measures a prompt the way the paid GEO tools do: many runs, one aggregate, every figure backed by a run count.

The operator does the capture. This skill does the aggregation.

## What the user gives you

1. **Brand**: the company being tracked.
2. **Competitors**: a short list. The sheet highlights these and ignores every other vendor, because listing every name on every page buries the signal.
3. **Log files**: one entry per run, in the format in `references/log-format.md`. Usually `.md` files. Pasted text works too: save it to a file first.

Brand and competitors can arrive in the chat or inside the logs (`brand:` and `competitors:` lines). Chat wins when both exist. When neither exists, ask for them in one question before doing anything else, since the whole sheet is built around them.

If the user only wants the capture prompt, give them the block from `references/capture-prompt.md` with their brand and competitors filled in, plus the operator rules under it. Stop there.

## Workflow

### 1. Write config.json

```json
{"prepared_by": "",
 "brand": {"name": "Remote", "aliases": ["Remote.com"], "domains": ["remote.com"], "common_word": true},
 "competitors": [{"name": "Deel", "aliases": [], "domains": ["deel.com", "help.letsdeel.com"]}]}
```

- `domains`: the company's own sites, including help centers and docs on separate hosts. Infer them from what you know and from the cited URLs. They drive the orange (competitor's own site) and blue (brand's own site) highlights. State the domains you assumed in the chat summary so the user can correct them.
- `aliases`: other spellings that appear in answers ("Papaya" for "Papaya Global").
- `common_word`: set true when the name is an everyday word (Remote, Notion, Square, Monday). The parser then counts the brand only where it is bolded, linked to its domain, or listed in the log's `brands_mentioned` line. Without this, "remote employees" at the start of a sentence counts as a mention.
- `prepared_by`: the user's company when they produce reports for clients. It prints in the title bar. Leave empty otherwise.

### 2. Parse the logs

```bash
python scripts/parse_logs.py --logs <files or folder> --config config.json --out work/
```

Add `--default-llm ChatGPT` or `--default-prompt "..."` when a file is a raw answer with no log block and the user has told you where it came from. Skip `--config` to have the script build it from the logs' `brand:` and `competitors:` lines, then add domains and aliases to `work/config.json` yourself.

Read the printed validation notes. They matter for the summary: RTF files, missing timestamps, and cases where the model's own citation count disagrees with the answer text.

### 3. Fill pages.json

Open `work/pages.json` and fill `title`, `source`, `type`, `brand_mentioned`, `competitors_mentioned` for each page, following `references/page-classification.md`. This is the step that needs you: it means opening the cited pages and reading what they are and who they name.

Never guess a mention. A cell reads `Yes`, `No`, a list of names, `none`, a `(per model)` value from the log, or `not checked`.

### 4. Build the workbook

```bash
python scripts/build_sheet.py --work work/ --config config.json --out /mnt/user-data/outputs/<brand>-ai-citation-analysis-<YYYYMMDD>.xlsx
```

The script writes the workbook and `work/summary.json`, and prints every figure you need for the chat summary. Present the file.

### 5. Write the chat summary

Short, in this order. Each figure once. Plain sentences.

1. Scope: runs per LLM, prompts, dates, total citations and pages.
2. The brand: answers naming it out of runs, per LLM, and where it sits in the order. Then competitors in one line.
3. Sources: top domains with runs cited, the top page, which content types dominate, how many pages the brand's competitors own.
4. What repeated runs revealed: pages seen in one run only, source stability, shared pages between LLMs.
5. New names outside the user's list, when any showed up more than once.
6. Warnings: run counts under the floor, validation problems, pages left unopened, domains you assumed.

Give "X of N answers" always. Add the range only when that prompt-LLM pair has 7 runs or more; below that the run-count warning carries the message. Say two brands are level when `overlap_notes` lists them. Explain figures in plain words ("cited in 3 of 8 runs"); keep Jaccard, Wilson and bootstrap out of the chat unless the user asks how a number was computed, then read `references/metrics.md`.

## The workbook

Tabs: **All LLMs**, one per LLM, **Prompts** (only with 2 or more prompts), **Answers**.

Citation tab columns: Rank, Page URL, Domain, Title, Source, Type, Citations, Citation %, Appearance rate, Cited in runs, Kind, Models (All LLMs tab only), Prompts (only with 2 or more prompts), `<Brand>` mentioned, Competitors mentioned.

- **`<Brand>` mentioned**: does this cited page name the user's brand. `Yes` in blue marks pages already working for them. `No` on a heavily cited page that names competitors marks a page worth getting onto.
- **Competitors mentioned**: which competitors from the user's list the page names. Yellow cell when it names any.
- **Domain** cell: orange when the site belongs to a competitor, blue when it belongs to the brand.
- **Kind**: "Cited in text", "Listed by the model" or "Retrieved by search". See `references/log-format.md`.
- **Cited in runs**: run IDs. The cell links to the first of those runs in the Answers tab, which holds every full answer. This keeps the citation tabs clean while the evidence stays one click away.

The layout follows the exports of commercial GEO tools so the user can work with it the way they already do: filter, sort, paste into client reports.

## Boundaries

- Work only from the logs provided. Do not run the prompts yourself to add runs unless the user asks; your own session carries context that biases the answer.
- Keep ChatGPT-style inline citations and Claude-style retrieved sources apart. The Kind column exists for that; the summary should say which kind each LLM's numbers are.
- Under 7 runs, report counts and warn. Do not rank brands on 3 or 4 runs.

## Reference files

- `references/capture-prompt.md`: the prompt the operator sends after each answer, operator rules, per-LLM notes. Read when the user asks for the prompt or how to capture.
- `references/log-format.md`: entry format, field rules, how citations are counted, what the parser tolerates. Read when a log fails to parse or the user asks about the format.
- `references/page-classification.md`: how to fill pages.json. Read at step 3.
- `references/metrics.md`: formulas, run-count floors, sources. Read when the user asks how a figure is computed or how many runs to collect.
