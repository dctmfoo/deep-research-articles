---
description: Generate a research-based article using deep research and multi-model AI pipeline
allowed-tools: [Task, Read, Write, Bash, Glob, AskUserQuestion, WebSearch, mcp__gemini-research__start_deep_research, mcp__gemini-research__check_research_status, mcp__gemini-research__get_research_result, mcp__gemini-research__generate_articles, mcp__gemini-research__generate_images, mcp__gemini-research__assemble_markdown]
argument-hint: <topic>
---

# Deep Research Article Pipeline

Generate research-based articles using Claude + Gemini multi-model pipeline.

## Pipeline Overview

```
[1. Clarify] → [2. Research] → [3. Generate] → [4. Synthesize] → [5. Images] → [6. Assemble] → [7. Humanize]
   Claude        Gemini DR      Gemini Pro      Claude           Gemini        Gemini Pro      Claude
   (main)                       + Flash         (main)           Imagen                        (main)
```

## Starting Point

Topic from user: $ARGUMENTS

If no topic provided, ask: "What topic do you want to research and write about?"

---

## Phase 1: Clarification

**Invoke the clarifier skill** to gather requirements and create spec.json:

```
Use the Skill tool:
- skill: "deep-research-articles:clarifier"
- args: "$ARGUMENTS"
```

The clarifier will:
1. Ask layered questions (5 layers) using AskUserQuestion tool
2. Perform WebSearch before each layer to understand the domain
3. Gather comprehensive research brief (topic, questions, dimensions, perspectives, timeframes, evidence types)
4. Gather article specs (intent, audience, format, word count, stance, angle)
5. Save spec.json to: `instance/research/{topic-slug}/{timestamp}/spec.json`
6. Return the path to spec.json

**Wait for the clarifier to complete** before proceeding to Phase 2.

After clarification completes, read the spec.json to get the research parameters.

---

## Phase 2: Deep Research

Call MCP tool:

```
mcp__gemini-research__start_deep_research({
  "query": "<topic>",
  "spec": <spec object>
})
```

Returns `job_id`. Poll every 30 seconds:

```
mcp__gemini-research__check_research_status({
  "job_id": "<job_id>"
})
```

When status is "complete", get results:

```
mcp__gemini-research__get_research_result({
  "job_id": "<job_id>"
})
```

Save to: `instance/research/{topic-slug}/{timestamp}/01-research.md`

---

## Phase 3: Article Generation (Parallel Drafts)

Call MCP tool:

```
mcp__gemini-research__generate_articles({
  "research": "<research content>",
  "spec": <spec object>
})
```

This runs Gemini Pro and Flash in parallel.

Save outputs:
- `instance/research/{topic-slug}/{timestamp}/02a-gemini-pro-draft.md`
- `instance/research/{topic-slug}/{timestamp}/02b-gemini-flash-draft.md`

---

## Phase 4: Synthesis (You do this)

Read both drafts and synthesize:

1. Extract best elements from each:
   - Pro: depth, nuance, comprehensive coverage
   - Flash: clarity, punchiness, accessibility
2. Combine into single coherent article
3. Match format/word count from spec
4. Ensure smooth transitions and consistent voice

Save to: `instance/research/{topic-slug}/{timestamp}/03-opus-synthesis.md`

---

## Phase 5: Image Generation

Create 3-5 image prompts based on article sections.

**Prompt guidelines:**
- Be specific and detailed (composition, lighting, style)
- Avoid text in images
- Match article tone (photorealistic vs illustration)

Call MCP tool:

```
mcp__gemini-research__generate_images({
  "prompts": [
    {"prompt": "...", "filename": "hero.png"},
    {"prompt": "...", "filename": "section1.png"}
  ],
  "output_dir": "instance/research/{topic-slug}/{timestamp}/04-images"
})
```

---

## Phase 6: Assembly

Call MCP tool:

```
mcp__gemini-research__assemble_markdown({
  "article": "<synthesized article>",
  "images_dir": "instance/research/{topic-slug}/{timestamp}/04-images",
  "format": "<format from spec>"
})
```

Save to: `instance/research/{topic-slug}/{timestamp}/05-assembled.md`

---

## Phase 7: Humanization (You do this)

Remove AI writing patterns:

**Checklist:**
- [ ] Remove em-dashes (—) → use commas or periods
- [ ] Cut filler: "arguably", "notably", "certainly", "frankly"
- [ ] Remove promotional: "game-changing", "revolutionary", "cutting-edge"
- [ ] Fix forced metaphors
- [ ] Vary sentence structure
- [ ] Add specific examples where vague
- [ ] Remove "In conclusion" → just conclude naturally

Save final to: `instance/research/{topic-slug}/{timestamp}/06-humanized.md`

---

## Output

Tell user:

> "Article complete!"
>
> **Final output:** `instance/research/{topic-slug}/{timestamp}/06-humanized.md`
>
> **Word count:** X words
> **Reading time:** ~X minutes
> **Images:** X generated

Provide links to all intermediate files.

---

## Error Handling

- Research job fails → Retry once, then ask user
- Image generation fails → Continue without images, note in output
- MCP tool unavailable → Check if gemini-research MCP server is configured
