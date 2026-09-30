# Amendment 1 to protocol_llm1.md - made BEFORE any model run

## Reason (reported by the runner)
- LMArena's Side by Side / Direct Chat lists are often a generation or more behind the newest models.
- Battle mode reveals names only after answering. Its models are random, so no model is guaranteed to answer all 8 batches, and some revealed names are codenames of unreleased models.
- From Iraq, the runner can reach these flagship-level models:
  - Claude and Gemini, through the runner's subscriptions;
  - DeepSeek and Qwen, which are free.
- OpenAI's flagship needs a subscription the runner does not have.

No model has been run and no answer has been seen when this amendment is written. The sealed files (instructions, prompts, tools, protocol_llm1.md) are unchanged.

## Changes to section 2 (models)
1. **Families and interfaces.** Four scored models:
   - Anthropic: the claude.ai app;
   - Google: the Gemini app or Google AI Studio, whichever offers the stronger model;
   - DeepSeek: its official chat;
   - Qwen: its official chat.

   For each, use the most capable model offered to the runner in that interface on the first run day, in its normal chat mode.
   - A reasoning or "thinking" option of that model is allowed and recorded.
   - Agent, deep-research and multi-step research modes are not allowed.
2. **OpenAI** is not scored: its flagship is not accessible.
   - Optionally, the free ChatGPT model may be run as SUPPLEMENTARY data. It is labelled non-flagship and excluded from the verdict and the overall result.
3. **LMArena** is no longer required. Battle-mode runs, if any, are SUPPLEMENTARY only. The same holds for any model that did not answer all 8 batches.
4. **Settings for every scored run:**
   - Open a new conversation per batch.
   - Turn off memory and personalization (use a temporary or incognito chat where offered).
   - Do not use web search.
   - Turn off code execution where the interface allows it; otherwise record whether the reply shows that code was run.
   - Record the interface, the model name as shown, any reasoning option, and the tool status in meta.json.

## Unchanged
- The run procedure (section 3), except the interface.
- The parsing rules, the scoring, the verdict rules and the interpretation.
- The overall result is computed over the four scored models.

## Added limitation
- No OpenAI flagship is tested, so the result says nothing about it.
- Official apps may add hidden system prompts or tools, which may differ between vendors.
