# Deep Research Articles Plugin

Generate high-quality research-based articles using a multi-model AI pipeline with Claude and Gemini.

## Features

- **Intelligent Clarification**: Claude asks layered questions to understand exactly what you need
- **Deep Research**: Gemini performs comprehensive web research
- **Multi-Model Article Generation**: Parallel generation with Gemini Pro and Flash
- **AI Synthesis**: Claude Opus combines the best parts of both articles
- **Automated Image Generation**: Gemini Pro Image creates relevant visuals
- **Humanization**: Removes AI writing patterns for natural-sounding output

## Quick Start

```bash
# Ensure you have a Gemini API key configured
export GOOGLE_API_KEY="your-key"

# Run a research article
/deep-research-articles:research-article AI agents in 2025
```

## Requirements

- Python 3.11+
- Gemini API key with access to:
  - Gemini Pro / Flash
  - Gemini Pro Image (Nano Banana Pro)

## Pipeline

1. **Clarification** (Claude Sonnet) - Gathers requirements
2. **Deep Research** (Gemini) - Comprehensive research
3. **Article Generation** (Gemini Pro + Flash) - Parallel drafts
4. **Synthesis** (Claude Opus) - Combines best elements
5. **Image Generation** (Gemini Pro Image) - Creates visuals
6. **Assembly** - Final markdown with images
7. **Humanization** - Removes AI patterns

## Output Location

```
{instance_path}/research/{topic-slug}/{timestamp}/
├── spec.json                    # Requirements (Clarifier)
├── 01-research.md               # Research report (Gemini Deep Research)
├── 02a-gemini-pro-draft.md      # Gemini Pro draft
├── 02b-gemini-flash-draft.md    # Gemini Flash draft
├── 03-opus-synthesis.md         # Synthesized draft (Opus)
├── image-prompts.json           # Image prompts
├── 04-images/                   # Generated images (Imagen)
├── 05-assembled.md              # Assembled article (Gemini Pro)
└── 06-humanized.md              # Final humanized article
```

## Configuration

Edit `config/default.yaml` to customize:
- Model selection
- Timeouts
- Output preferences

## License

MIT
