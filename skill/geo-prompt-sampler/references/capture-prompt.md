# Capture prompt

The operator asks the test question in a fresh chat, waits for the answer, then sends this as the next message in the same chat. The test question itself goes in unmodified, because any added instruction changes the answer being measured.

Give the operator the block below with `brand` and `competitors` already filled in when you know them.

```
Create a downloadable markdown (.md) file containing a log entry for your previous answer. Give me the download link. Follow these rules:
- Do not run a new search.
- Do not change, improve or add to your previous answer.
- Report only what your previous answer contained.
- Name the file: geo-log_<llm>_<YYYYMMDD-HHMMSS>.md
- If you cannot create downloadable files, return the full entry inside one code block and nothing else.

Operator fields (copy them into the entry as written):
brand: [company name]
competitors: [competitor 1; competitor 2; competitor 3]

The file holds this block, filled in:

=== GEO LOG ENTRY ===
brand: <copy from the operator fields>
competitors: <copy from the operator fields>
timestamp: <current date and time with timezone, in the form YYYY-MM-DD HH:MM:SS TZ. If you have no access to the current time, write UNKNOWN>
llm: <the product you are: ChatGPT, Perplexity, Gemini, Claude, Copilot, other>
provider: <the company that runs you>
model: <your exact model name and version. If you do not know it, write UNKNOWN>
mode: <any mode active for the previous answer: web search, deep research, thinking, pro, none>
prompt: <copy the exact question I asked before this message>
web_search_used: <yes or no>
brands_mentioned: <each company or product named as an option in your previous answer, listed once, in order of first appearance, separated by ; . Leave out generic terms and sites that appear only as sources>
citations:
<one line per source cited in your previous answer, in order of first appearance, in this form:>
<number>. <full URL> | <page title> | <times cited in the answer> | <which names from the brand and competitors fields that page mentions, separated by ; . Write none if it mentions none of them. Write unknown if you did not see the page content>
<if the answer cited no sources, write: none>
answer:
<<<
<your previous answer, copied word for word, with every link kept exactly as it appeared>
>>>
=== END ===
```

## Operator rules

1. Open a new chat for every run, with memory and personalization off (temporary or incognito chat where the product has one). A second run in the same chat reads the first answer and repeats it.
2. Run each prompt at least 7 times per LLM, 8 when sources matter.
3. Compare the citation count in the entry with the sources shown on screen. Models drop or invent URLs when asked to list their own sources.
4. Compare the `model` line with the model picker on screen. Models misreport their own version.
5. Save entries as plain text. TextEdit saves RTF by default (Format > Make Plain Text fixes it). The parser converts RTF, so this is a convenience.

## Per-LLM notes

- **ChatGPT**: returns the entry as a file or a code block. Inline links survive the copy. Works as written.
- **Claude**: creates the file, and writes `citations: none`. Claude sees only the text of its previous answer, and its sources live in the "Web search" panel of the interface. For Claude, open that panel and add the pages under a `sources_retrieved:` section (see log-format.md), or capture with Claude in Chrome / Cowork reading the panel.
- **Perplexity, Gemini**: return the code block. Save it under the same file name.
- **Google AI Overview / AI Mode**: no follow-up box in AI Overview. Copy the answer and the source links by hand into the same block.
