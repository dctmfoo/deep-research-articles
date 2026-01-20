# Deep Research Articles Plugin

Generate high-quality research-based articles using a 7-phase AI pipeline combining Claude and Gemini.

## Overview

This plugin enables **comprehensive research and article generation** through intelligent orchestration of multiple AI models and specialized agents. The main Claude agent orchestrates the entire pipeline, invoking skills, subagents, and MCP tools as needed.

### Key Features

- **Intelligent Clarification**: WebSearch-informed layered questioning to build precise research briefs
- **Deep Research**: Gemini Deep Research performs comprehensive multi-faceted investigation
- **Dual Article Generation**: Parallel drafts (Gemini Pro for depth, Flash for clarity)
- **Smart Synthesis**: Specialized subagent combines best elements from both drafts
- **Visual Generation**: Gemini Imagen creates contextual images
- **Humanization**: Removes AI writing patterns for natural-sounding output

## How It Works

### Architecture

```
User Request (/research-article topic)
    ↓
Main Claude Agent (Orchestrator)
    ├─ Invokes skills (clarifier, imagen-prompting, humanizer)
    ├─ Launches subagents (synthesizer)
    └─ Uses MCP tools (Deep Research, Article Generation, Images)
    ↓
Final Article (research/topic-slug/timestamp/05-final.md)
```

### Component Roles

| Component | Type | Role |
|-----------|------|------|
| **Main Claude Agent** | Orchestrator | Makes decisions, routes work, writes all files |
| **clarifier skill** | Skill | Asks questions, builds research_brief |
| **synthesizer agent** | Subagent | Combines Pro + Flash drafts |
| **humanizer skill** | Skill | Removes AI writing patterns |
| **imagen-prompting skill** | Skill | Creates effective image prompts |
| **MCP Tools** | External | Gemini API (research, articles, images) |

### The 7-Phase Pipeline

#### Phase 1: Clarification
**Actor:** Main agent invokes `clarifier` skill

**What happens:**
1. Skill performs WebSearch to understand the domain
2. Asks Layer 1 questions (topic, motivation, core questions)
3. WebSearch again for dimensions and perspectives
4. Asks Layer 2 questions (dimensions, perspectives)
5. WebSearch for evidence types and contexts
6. Asks Layer 3 questions (timeframes, evidence, scope)
7. Asks Layer 4 questions (article specs: format, audience, length)
8. Validates understanding with user
9. Writes `spec.json` with two sections:
   - `research_brief` (for Deep Research)
   - `article_specs` (for article generation)

**Output:** `spec.json`

#### Phase 2: Deep Research
**Actor:** Main agent uses MCP tools

**What happens:**
1. Agent reads `research_brief` from spec.json
2. Constructs comprehensive research query:
   - Core questions to investigate
   - Required perspectives (experts, practitioners, critics)
   - Key dimensions (technical, economic, social, ethical)
   - Evidence priorities (studies, data, case studies)
   - Critical contexts
   - Adjacent topics
   - Controversies and debates
   - Timeframe analysis
3. Calls `start_deep_research` MCP tool (Gemini Deep Research)
4. Polls `check_research_status` every 30 seconds
5. Retrieves comprehensive research report
6. Writes `01-research.md`

**Output:** `01-research.md` (comprehensive research report)

**Critical:** Article constraints (format, word count, stance) are NOT sent to Deep Research. Only the research brief goes to Gemini.

#### Phase 3: Article Generation
**Actor:** Main agent uses MCP tools

**What happens:**
1. Agent reads research report
2. Agent reads `article_specs` from spec.json
3. Calls `generate_articles` MCP tool
4. Gemini Pro generates depth-focused draft (in parallel)
5. Gemini Flash generates clarity-focused draft (in parallel)
6. Agent receives both drafts
7. Agent writes `02a-gemini-pro-draft.md`
8. Agent writes `02b-gemini-flash-draft.md`

**Output:** Two draft files with different strengths

#### Phase 4: Synthesis
**Actor:** Main agent invokes `synthesizer` subagent

**What happens:**
1. Main agent launches synthesizer subagent
2. Subagent reads both draft files
3. Subagent reads article_specs
4. Subagent extracts best elements:
   - From Pro: depth, nuance, comprehensive coverage
   - From Flash: clarity, punchiness, accessibility
5. Subagent combines into coherent article
6. Subagent ensures smooth transitions and consistent voice
7. Subagent returns result to main agent
8. Main agent writes `03-synthesis.md`

**Output:** `03-synthesis.md` (combined article)

#### Phase 5: Image Generation
**Actor:** Main agent invokes `imagen-prompting` skill + MCP tools

**What happens:**
1. Agent invokes imagen-prompting skill
2. Skill analyzes article structure
3. Skill identifies 3-5 strategic image locations
4. Skill creates effective prompts for each
5. Skill returns prompt array to agent
6. Agent calls `generate_images` MCP tool
7. Gemini Imagen generates each image
8. MCP returns image file paths

**Output:** 3-5 `.jpg` files in `images/` directory

#### Phase 6: Assembly
**Actor:** Main agent uses MCP tools

**What happens:**
1. Agent reads synthesis file
2. Agent calls `assemble_markdown` MCP tool
3. MCP inserts hero image at top
4. MCP distributes remaining images at section breaks
5. Agent receives assembled markdown
6. Agent writes `04-assembled.md`

**Output:** `04-assembled.md` (article with image references)

#### Phase 7: Humanization
**Actor:** Main agent invokes `humanizer` skill

**What happens:**
1. Agent invokes humanizer skill
2. Skill reads assembled markdown
3. Skill scans for AI writing patterns:
   - Em dash overuse
   - AI vocabulary (crucial, key, landscape, pivotal)
   - Promotional language (ultimate, premium, game-changing)
   - Inflated symbolism (testament to, stands as)
   - Negative parallelisms (It's not just X, it's Y)
4. Skill rewrites problematic sections
5. Skill returns humanized content
6. Agent writes `05-final.md`

**Output:** `05-final.md` (publication-ready article)

## Installation

### Prerequisites

- Node.js 18+
- Claude Code CLI
- Google API key with access to:
  - Deep Research Pro Preview
  - Gemini 3 Pro Preview
  - Gemini 3 Flash Preview
  - Gemini 3 Pro Image Preview (Imagen)

### Setup

```bash
# Set your Google API key
export GOOGLE_API_KEY="your-api-key-here"

# Install plugin from custom marketplace
claude plugin add-marketplace https://github.com/dctmfoo/deep-research-articles
claude plugin install deep-research-articles@deep-research-articles
```

## Usage

### Basic Usage

```bash
/research-article AI and human collaboration in 2026
```

The main Claude agent will:
1. Invoke clarifier skill (asks questions)
2. Run Deep Research via MCP
3. Generate articles via MCP
4. Invoke synthesizer subagent
5. Generate images via MCP
6. Assemble article via MCP
7. Invoke humanizer skill
8. Save final article

### Advanced Usage

```bash
# Just clarification (get spec.json)
/clarify Topic name

# Full pipeline with custom config
/research-article Topic name
# Answer clarification questions...
# Pipeline runs automatically
```

## Output Structure

```
instance/research/{topic-slug}/{timestamp}/
├── spec.json                       # Research brief + article specs
├── 01-research.md                  # Deep Research report (with sources)
├── 02a-gemini-pro-draft.md         # Pro draft (depth & nuance)
├── 02b-gemini-flash-draft.md       # Flash draft (clarity & punch)
├── 03-synthesis.md                 # Combined best elements
├── images/                         # Generated images
│   ├── hero-image.jpg
│   ├── section-1.jpg
│   └── ...
├── 04-assembled.md                 # Article with image refs
└── 05-final.md                     # Humanized (publication-ready)
```

## Configuration

Edit `plugin/config/default.yaml`:

```yaml
gemini:
  models:
    deep_research: deep-research-pro-preview-12-2025
    pro: gemini-3-pro-preview
    flash: gemini-3-flash-preview
    image: gemini-3-pro-image-preview
  research:
    timeout_seconds: 1800      # 30 min max
    poll_interval_seconds: 30  # Status check frequency
```

## Key Principles

### 1. Main Agent Orchestrates
- Main Claude agent makes ALL decisions
- Main agent writes ALL files
- Skills/subagents/MCP provide capabilities and return data

### 2. Separation of Concerns
- `research_brief` → Deep Research (comprehensive, no article constraints)
- `article_specs` → Article generation (format, audience, length)
- Deep Research never sees article format constraints

### 3. Progressive Disclosure
- Clarifier does WebSearch before each question layer
- Questions become smarter based on domain understanding
- User is never overwhelmed with all questions at once

### 4. Multi-Model Strength
- Gemini Deep Research: comprehensive investigation
- Gemini Pro: depth and nuance
- Gemini Flash: clarity and accessibility
- Claude: orchestration, synthesis, humanization

## Troubleshooting

### MCP Server Not Connected

```bash
# Check MCP server status
claude mcp list

# Restart if needed
claude restart
```

### Images Not Generating

Ensure your API key has access to Gemini 3 Pro Image Preview (Imagen). Check error messages in MCP response.

### Clarifier Questions Seem Generic

The clarifier does WebSearch before each layer. If questions seem off, the topic might need more specificity.

## Development

```bash
# Clone repo
git clone https://github.com/dctmfoo/deep-research-articles
cd deep-research-articles/plugin

# Install dependencies
npm install

# Build MCP server
npm run build

# Test locally
npm run dev
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│              User Request via Command                │
│              /research-article <topic>               │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│           Main Claude Agent (Orchestrator)           │
│  - Decides what to do and when                      │
│  - Invokes skills, subagents, MCP tools             │
│  - Writes all output files                          │
└──┬──────────┬──────────┬──────────┬─────────────────┘
   │          │          │          │
   ↓          ↓          ↓          ↓
┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐
│Skills│  │Sub   │  │ MCP  │  │ Hooks    │
│      │  │agents│  │Tools │  │(PostTool)│
└──┬───┘  └──┬───┘  └──┬───┘  └────┬─────┘
   │         │         │           │
   ↓         ↓         ↓           ↓
Return    Return    Return     Auto-run
data      data      data       after writes
```

## Credits

Built with:
- [Claude Code](https://code.claude.com) - Plugin framework
- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk) - Agent orchestration
- [Google Gemini API](https://ai.google.dev/) - Research, articles, images

## License

MIT

## Links

- [GitHub Repository](https://github.com/dctmfoo/deep-research-articles)
- [Plugin Documentation](./docs/)
- [Issue Tracker](https://github.com/dctmfoo/deep-research-articles/issues)
