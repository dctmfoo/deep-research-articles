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

## Phase 1: Clarification (REQUIRED - Use AskUserQuestion)

You MUST use the AskUserQuestion tool for all questions. This runs in main thread.

### Layer 1 - Intent Discovery

```json
{
  "questions": [
    {
      "question": "What's your primary goal with this article?",
      "header": "Goal",
      "options": [
        {"label": "Educate", "description": "Help readers understand the topic deeply"},
        {"label": "Persuade", "description": "Convince readers of a specific viewpoint"},
        {"label": "Inform", "description": "Share recent news and developments"},
        {"label": "Entertain", "description": "Engage readers while teaching"}
      ],
      "multiSelect": false
    },
    {
      "question": "Who is your target audience?",
      "header": "Audience",
      "options": [
        {"label": "Decision makers", "description": "Executives, managers, budget holders"},
        {"label": "Practitioners", "description": "Hands-on professionals implementing this"},
        {"label": "General public", "description": "Curious readers, no special expertise"},
        {"label": "Technical specialists", "description": "Deep domain experts"}
      ],
      "multiSelect": false
    },
    {
      "question": "What should readers do after reading?",
      "header": "Action",
      "options": [
        {"label": "Implement something", "description": "Apply specific techniques or tools"},
        {"label": "Change perspective", "description": "Think differently about the topic"},
        {"label": "Stay informed", "description": "Be up-to-date on developments"},
        {"label": "Share with others", "description": "Spread the knowledge"}
      ],
      "multiSelect": false
    }
  ]
}
```

### Layer 2 - Scope

```json
{
  "questions": [
    {
      "question": "How deep should the article go?",
      "header": "Depth",
      "options": [
        {"label": "Overview", "description": "Broad, surface-level introduction"},
        {"label": "Detailed", "description": "Specific aspects with examples"},
        {"label": "Comprehensive", "description": "Exhaustive, authoritative reference"}
      ],
      "multiSelect": false
    },
    {
      "question": "What format do you prefer?",
      "header": "Format",
      "options": [
        {"label": "Blog post (2000+ words)", "description": "Long-form with sections and narrative"},
        {"label": "X Article (~600 words)", "description": "Punchy, shareable, Twitter-style"},
        {"label": "LinkedIn post", "description": "Professional tone, career-focused"}
      ],
      "multiSelect": false
    }
  ]
}
```

### Layer 3 - Angle

```json
{
  "questions": [
    {
      "question": "What stance should the article take?",
      "header": "Stance",
      "options": [
        {"label": "Neutral", "description": "Just the facts, no opinion"},
        {"label": "Optimistic", "description": "Focus on opportunities and benefits"},
        {"label": "Critical", "description": "Highlight challenges and risks"},
        {"label": "Balanced", "description": "Present both sides fairly"}
      ],
      "multiSelect": false
    },
    {
      "question": "What angle should we emphasize?",
      "header": "Angle",
      "options": [
        {"label": "Economic impact", "description": "Business, money, ROI"},
        {"label": "Social implications", "description": "Society, culture, people"},
        {"label": "Technical feasibility", "description": "How it works, implementation"},
        {"label": "Personal relevance", "description": "Career, daily life impact"}
      ],
      "multiSelect": false
    }
  ]
}
```

### After Clarification

Build spec object from answers:

```json
{
  "topic": "<from $ARGUMENTS>",
  "intent": "<from Goal answer>",
  "audience": "<from Audience answer>",
  "desired_action": "<from Action answer>",
  "depth": "<from Depth answer>",
  "format": "<from Format answer>",
  "word_count": 2000,
  "stance": "<from Stance answer>",
  "angle": "<from Angle answer>"
}
```

Save to: `instance/research/{topic-slug}/{timestamp}/spec.json`

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
