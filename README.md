# GEO Prompt Sampler

A Claude skill that turns repeated runs of one AI-visibility prompt into a single citation report.

Ask ChatGPT the same question eight times and you get eight different source lists. The brands mostly hold. The pages cited change almost every run. Commercial GEO tools deal with this by sampling a prompt many times and aggregating. This skill does the same with logs you capture yourself, in any LLM you can open in a browser.

Built by [Meriem Aousaji](https://www.linkedin.com/in/meriemaousaji/) at [Algomizer](https://algomizer.com).

## What you get

An Excel workbook in the layout GEO tools export:

| Tab | Holds |
|---|---|
| All LLMs | Every cited page across all runs and models |
| ChatGPT, Claude, Perplexity... | One tab per model |
| Prompts | Runs per prompt and model (only with 2 or more prompts) |
| Answers | Every full answer, one row per run. The citation tabs link here. |

Citation tab columns: Rank, Page URL, Domain, Title, Source, Type, Citations, Citation %, Appearance rate, Cited in runs, Kind, Models, `<Brand>` mentioned, Competitors mentioned.

Highlights: yellow when a page names one of your competitors, orange when the domain belongs to a competitor, blue when the page or domain is yours.

Plus a chat summary: brand mention rate per model, who gets named first, top domains, content types, pages seen in one run only, run-to-run stability, and warnings when the run count is too low to trust a figure.

See `examples/sample-output.xlsx` for a report built from the logs in `examples/logs/`.

## Install

1. Download `geo-prompt-sampler.skill` from the latest release.
2. In Claude, drop the file into a chat and click **Save skill**, or upload it under Settings > Skills.

The skill runs in Claude web, desktop and Cowork. It needs the code execution feature on.

## Capture a run

1. Open a fresh chat in the LLM you are testing, with memory and personalization off. Use temporary or incognito chat where the product has one.
2. Ask your prompt. Nothing added, nothing changed.
3. Send the contents of `CAPTURE-PROMPT.txt` as the next message, with your brand and competitors filled in at the top.
4. Save the file it returns. ChatGPT and Claude give a download. Perplexity and Gemini return a code block; save it as `.md`.
5. Repeat. Aim for 8 runs per prompt per LLM. Seven is the floor for brand figures, eight for source figures.

For Claude, the capture prompt returns `citations: none`, since Claude only sees the text of its previous answer. Open the Web search panel above the answer and paste the pages under a `sources_retrieved:` section. See `skill/geo-prompt-sampler/references/capture-prompt.md` for per-model notes.

## Build the report

Drop the log files into a Claude chat and say what you want:

> Here are 8 runs on ChatGPT and 8 on Perplexity. Brand is Remote, competitors are Deel, Rippling, Papaya Global and Oyster. Build the citation analysis.

Claude parses the logs, opens the cited pages to classify them and check who they name, builds the workbook and writes the summary.

## How the numbers work

Every figure is a rate across runs with the run count behind it. Brand mention rate carries a Wilson 95% range. Domain citation share carries a bootstrap range from 8 runs up. Stability is the mean Jaccard overlap between runs. Run-count floors come from Schulte, Bleeker and Kaufmann, "Don't Measure Once" (arXiv 2604.07585); the uncertainty method from Sielinski, "Quantifying Uncertainty in AI Visibility" (arXiv 2603.08924). Details in `skill/geo-prompt-sampler/references/metrics.md`.

## Repo layout

```
CAPTURE-PROMPT.txt        the prompt to send after each answer
examples/
  config.json             brand and competitor setup used for the sample
  logs/                   5 real captures on one payroll prompt (4 ChatGPT, 1 Claude)
  sample-output.xlsx      the report built from them
skill/geo-prompt-sampler/
  SKILL.md                the workflow Claude follows
  references/             capture prompt, log format, page classification, metrics
  scripts/                parse_logs.py, build_sheet.py
```

The example logs were captured with an earlier version of the prompt and normalised to the current format. Three came out of TextEdit as RTF; the parser converts those, so plain text is a convenience rather than a requirement.

## Roadmap

- Claude capture for Cowork: read the Web search panel and write the log entry without the manual step
- Google AI Overview and AI Mode capture
- Tracking over time: rolling 2 to 4 week windows on the same prompt set

## License

MIT
