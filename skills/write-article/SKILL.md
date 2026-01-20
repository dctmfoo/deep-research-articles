---
name: write-article
description: "Generate research-based articles using a multi-model AI pipeline. Combines Claude for clarification and synthesis with Gemini for deep research, article generation, and image creation."
---

# Write Article Skill

This skill orchestrates the deep research article pipeline.

## Usage

Invoke the orchestrator agent to create a research-based article:

```
/deep-research-articles:research-article <topic>
```

## Pipeline Overview

1. **Clarification** (Claude Sonnet) - Gathers requirements via layered questions
2. **Deep Research** (Gemini Deep Research) - Comprehensive web research
3. **Article Generation** (Gemini Pro + Flash) - Parallel drafts
4. **Synthesis** (Claude Opus) - Combines best elements
5. **Image Generation** (Gemini Pro Image) - Creates visuals
6. **Assembly** (Gemini Pro) - Final markdown with images
7. **Humanization** - Removes AI patterns

## Output Location

```
{instance_path}/research/{topic-slug}/{timestamp}/
├── spec.json                    # Requirements (Clarifier)
├── 01-research.md               # Research report (Gemini Deep Research)
├── 02a-gemini-pro-draft.md      # Gemini Pro draft
├── 02b-gemini-flash-draft.md    # Gemini Flash draft
├── 03-opus-synthesis.md         # Synthesized draft (Opus)
├── image-prompts.json           # Image prompts (Opus)
├── 04-images/                   # Generated images (Imagen)
├── 05-assembled.md              # Assembled article (Gemini Pro)
└── 06-humanized.md              # Final humanized article
```

## Requirements

- `GOOGLE_API_KEY` with Gemini API access
- Python 3.11+ for MCP server
