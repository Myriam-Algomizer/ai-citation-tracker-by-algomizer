# Log format

One entry per run. One file per entry is the norm. A file may hold several entries.

```
=== GEO LOG ENTRY ===
brand: Remote
competitors: Deel; Rippling; Papaya Global; Oyster
timestamp: 2026-09-21 14:27:00 +01:00
llm: ChatGPT
provider: OpenAI
model: GPT-5.6 Luna
mode: web search
prompt: What is the best payroll software for a startup with remote employees in several countries?
web_search_used: yes
brands_mentioned: Deel; Remote; Rippling; Papaya Global
citations:
1. https://www.deel.com/use-cases/run-global-payroll/ | Global Payroll | Deel | 1 | Deel
2. https://remote.com/blog/eor-peo/deel-vs-rippling-vs-remote-vs-papaya-global | Deel vs Rippling vs Remote vs Papaya Global | 3 | Remote; Deel; Rippling; Papaya Global
sources_retrieved:
1. https://example.com/page | Page title
answer:
<<<
The full answer, word for word, links intact.
>>>
=== END ===
```

## Fields

| Field | Notes |
|---|---|
| `brand`, `competitors` | Operator fields. Optional when the user names them in chat. The parser builds config.json from them when no config is passed. |
| `timestamp` | Any of: `YYYY-MM-DD HH:MM:SS +01:00`, `YYYY-MM-DD HH:MM +01`, `... UTC`. `UNKNOWN` is accepted. Runs are numbered by timestamp. |
| `llm` | Decides the tab the run lands in. |
| `brands_mentioned` | Used to spot new names outside the user's list, and to confirm brands whose name is a common word. Brand presence itself is read from the answer text. |
| `citations` | `<n>. <url> | <title> | <times cited> | <names from the list on that page>`. The last field is optional. Titles may contain pipes; fields are read from the right. |
| `sources_retrieved` | Optional. Pages the LLM pulled in its search that the answer text does not cite inline. Used for Claude. Counted once per run and labelled "Retrieved by search". |
| `answer` | Verbatim, between `<<<` and `>>>`. A missing `<<<` is tolerated. |

## How citations are counted

1. Links inside the answer text are the count of record. Label: "Cited in text".
2. When the answer text holds no links, the model's own `citations` list is used. Label: "Listed by the model". The validation report flags it, since models miscount.
3. `sources_retrieved` pages are added once each. Label: "Retrieved by search".

The three labels appear in the sheet's Kind column so the operator never mixes them.

URLs are normalized: tracking parameters (`utm_*`, `ref`, `source`, `gclid`...) removed, `www.` removed, trailing slash removed, host lowercased.

## What the parser tolerates

RTF files saved with an .md ending, code fences around the entry, stray backticks after `=== END ===`, a missing `<<<`, entries from older prompt versions (with `run:` or `region:` lines, or without `brand:`), and raw answers with no log block. A raw answer is counted from its inline links; its timestamp and model read UNKNOWN.
