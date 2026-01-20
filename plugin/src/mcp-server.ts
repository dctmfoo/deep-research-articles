#!/usr/bin/env node
// File: mcp-server.ts | Module: deep-research-articles

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { GoogleGenAI } from "@google/genai";
import { readFileSync, writeFileSync, mkdirSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import yaml from "js-yaml";

// Get config path - handle both ESM and bundled CJS
declare const __dirname: string; // CJS global
const getDirname = (): string => {
  // In CJS bundle, __dirname is available
  if (typeof __dirname !== 'undefined') {
    return __dirname;
  }
  // In ESM, use import.meta.url
  const __filename = fileURLToPath(import.meta.url);
  return dirname(__filename);
};
const configPath = join(getDirname(), "../config/default.yaml");

// Load config
interface Config {
  gemini: {
    models: {
      deep_research: string;
      pro: string;
      flash: string;
      image: string;
    };
    research: {
      timeout_seconds: number;
      poll_interval_seconds: number;
    };
  };
}

let config: Config;
try {
  config = yaml.load(readFileSync(configPath, "utf8")) as Config;
} catch (e) {
  console.error("Failed to load config:", e);
  process.exit(1);
}

// Types
interface ResearchBrief {
  topic: string;
  core_questions: string[];
  dimensions: string[];
  perspectives: string[];
  timeframes: string[];
  evidence_types: string[];
  contexts?: string[];
  related_topics?: string[];
  controversies?: string[];
  geographic_focus?: string;
}

interface ArticleSpecs {
  intent: string;
  audience: string;
  desired_action?: string;
  format: string;
  word_count: number;
  stance?: string;
  angle?: string;
  tone?: string;
}

interface ResearchSpec {
  research_brief: ResearchBrief;
  article_specs: ArticleSpecs;
  metadata?: {
    created_at?: string;
    topic_slug?: string;
    clarification_notes?: string;
  };
}

interface ResearchJob {
  id: string;
  status: "pending" | "running" | "complete" | "failed";
  result?: string;
  error?: string;
  startedAt: Date;
  interactionId?: string;
  outputPath?: string;
}

interface ImagePrompt {
  prompt: string;
  filename: string;
}

// In-memory job storage
const jobs = new Map<string, ResearchJob>();

// Initialize Gemini
const apiKey = process.env.GOOGLE_API_KEY;
if (!apiKey) {
  console.error("GOOGLE_API_KEY environment variable is required");
  process.exit(1);
}

const client = new GoogleGenAI({ apiKey });

// Helper: Generate unique ID
function generateId(): string {
  return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Deep Research using Interactions API
async function performDeepResearch(spec: ResearchSpec, job: ResearchJob): Promise<void> {
  try {
    const brief = spec.research_brief;

    // Build comprehensive research query (NO article constraints)
    let query = `Research Brief: ${brief.topic}\n\n`;

    // Core questions
    if (brief.core_questions && brief.core_questions.length > 0) {
      query += `Core Investigation:\n`;
      brief.core_questions.forEach((q, i) => {
        query += `${i + 1}. ${q}\n`;
      });
      query += `\n`;
    }

    // Perspectives
    if (brief.perspectives && brief.perspectives.length > 0) {
      query += `Required Perspectives:\n`;
      brief.perspectives.forEach(p => query += `- ${p}\n`);
      query += `\n`;
    }

    // Dimensions to explore
    if (brief.dimensions && brief.dimensions.length > 0) {
      query += `Key Dimensions to Explore:\n`;
      brief.dimensions.forEach((d, i) => query += `${i + 1}. ${d}\n`);
      query += `\n`;
    }

    // Evidence priorities
    if (brief.evidence_types && brief.evidence_types.length > 0) {
      query += `Evidence Priorities:\n`;
      brief.evidence_types.forEach(e => query += `- ${e}\n`);
      query += `\n`;
    }

    // Contexts
    if (brief.contexts && brief.contexts.length > 0) {
      query += `Critical Contexts:\n`;
      brief.contexts.forEach(c => query += `- ${c}\n`);
      query += `\n`;
    }

    // Related topics
    if (brief.related_topics && brief.related_topics.length > 0) {
      query += `Adjacent Topics for Complete Picture:\n`;
      brief.related_topics.forEach(t => query += `- ${t}\n`);
      query += `\n`;
    }

    // Controversies
    if (brief.controversies && brief.controversies.length > 0) {
      query += `Key Controversies and Debates:\n`;
      brief.controversies.forEach(c => query += `- ${c}\n`);
      query += `\n`;
    }

    // Timeframes
    if (brief.timeframes && brief.timeframes.length > 0) {
      query += `Timeframe Analysis:\n`;
      brief.timeframes.forEach(t => query += `- ${t}\n`);
      query += `\n`;
    }

    // Geographic focus
    if (brief.geographic_focus) {
      query += `Geographic Focus: ${brief.geographic_focus}\n\n`;
    }

    query += `Please provide comprehensive research covering all dimensions with specific examples, data, and contrasting viewpoints.`;

    console.error(`Deep Research Query:\n${query}`);

    // Start interaction
    const interaction = await client.interactions.create({
      input: [{ type: 'text', text: query }],
      agent: config.gemini.models.deep_research,
      background: true,
    });

    job.interactionId = interaction.id;
    console.error(`Research started: ${interaction.id}`);

    // Poll for completion
    const maxPolls = config.gemini.research.timeout_seconds / config.gemini.research.poll_interval_seconds;
    let pollCount = 0;

    while (pollCount < maxPolls) {
      await new Promise(resolve => setTimeout(resolve, config.gemini.research.poll_interval_seconds * 1000));
      pollCount++;

      // Check status
      const result = await client.interactions.get(interaction.id);

      if (result.status === "completed") {
        // Extract report from outputs
        const report = result.outputs && result.outputs.length > 0
          ? result.outputs[result.outputs.length - 1].text
          : "";

        // Write to disk if output_path provided
        if (job.outputPath) {
          const outputDir = dirname(job.outputPath);
          mkdirSync(outputDir, { recursive: true });
          writeFileSync(job.outputPath, report);
          console.error(`Research written to: ${job.outputPath}`);
          job.result = undefined; // Free memory - result is on disk
        } else {
          job.result = report;
        }
        job.status = "complete";
        console.error(`Research completed: ${report.length} chars`);
        return;
      } else if (result.status === "failed") {
        throw new Error(`Research failed: ${result.error || "Unknown error"}`);
      }

      console.error(`Poll ${pollCount}/${maxPolls}: status=${result.status}`);
    }

    throw new Error("Research timed out");
  } catch (error) {
    job.status = "failed";
    job.error = error instanceof Error ? error.message : String(error);
    console.error(`Research error: ${job.error}`);
    throw error;
  }
}

// Generate articles with Gemini Pro/Flash
async function generateArticle(
  research: string,
  spec: ResearchSpec,
  modelName: string
): Promise<string> {
  const articleSpecs = spec.article_specs;
  const wordCount = articleSpecs.word_count || 2000;
  const format = articleSpecs.format || "blog";

  const prompt = `Based on the following research, write a ${format} article of approximately ${wordCount} words.

Research:
${research}

Requirements:
- Target audience: ${articleSpecs.audience}
- Intent: ${articleSpecs.intent}
- Tone: ${articleSpecs.tone || "conversational"}
- Stance: ${articleSpecs.stance || "balanced"}
- Focus angle: ${articleSpecs.angle || "general"}
- Format: ${format}
${articleSpecs.desired_action ? `- Desired reader action: ${articleSpecs.desired_action}` : ''}

Write an engaging, well-structured article. Use headers, bullet points where appropriate. Include a compelling introduction and conclusion.`;

  const result = await client.models.generateContent({
    model: modelName,
    contents: prompt,
  });

  return result.text || "";
}

// Create MCP Server
const server = new Server(
  { name: "gemini-research", version: "1.0.1" },
  { capabilities: { tools: {} } }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "start_deep_research",
      description: "Start an async deep research job on a topic. If output_path is provided, writes result directly to disk when complete.",
      inputSchema: {
        type: "object",
        properties: {
          spec: {
            type: "object",
            description: "Research specification from clarification phase",
          },
          output_path: {
            type: "string",
            description: "File path to write result directly to disk when research completes",
          },
        },
        required: ["spec"],
      },
    },
    {
      name: "check_research_status",
      description: "Check the status of a running research job",
      inputSchema: {
        type: "object",
        properties: {
          job_id: { type: "string", description: "Job ID from start_deep_research" },
        },
        required: ["job_id"],
      },
    },
    {
      name: "get_research_result",
      description: "Get the result of a completed research job",
      inputSchema: {
        type: "object",
        properties: {
          job_id: { type: "string" },
        },
        required: ["job_id"],
      },
    },
    {
      name: "generate_articles",
      description: "Generate articles using Gemini Pro and Flash in parallel",
      inputSchema: {
        type: "object",
        properties: {
          research: { type: "string", description: "Research report content" },
          spec: { type: "object", description: "Research specification" },
        },
        required: ["research", "spec"],
      },
    },
    {
      name: "generate_images",
      description: "Generate images from prompts using Gemini Imagen",
      inputSchema: {
        type: "object",
        properties: {
          prompts: {
            type: "array",
            items: { type: "object" },
            description: "Array of image prompts with filename",
          },
          output_dir: { type: "string", description: "Directory to save images" },
        },
        required: ["prompts", "output_dir"],
      },
    },
    {
      name: "assemble_markdown",
      description: "Create final markdown with embedded images",
      inputSchema: {
        type: "object",
        properties: {
          draft: { type: "string", description: "Article draft content" },
          images: {
            type: "array",
            items: { type: "string" },
            description: "Image file paths",
          },
          format: {
            type: "string",
            enum: ["blog", "x_article", "linkedin"],
            description: "Target platform format",
          },
        },
        required: ["draft", "images"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "start_deep_research": {
        const spec = args?.spec as ResearchSpec;
        const outputPath = args?.output_path as string | undefined;
        const jobId = generateId();

        // Create job
        const job: ResearchJob = {
          id: jobId,
          status: "running",
          startedAt: new Date(),
          outputPath,
        };
        jobs.set(jobId, job);

        // Run research async
        performDeepResearch(spec, job).catch((error) => {
          job.status = "failed";
          job.error = error.message;
        });

        return {
          content: [{ type: "text", text: JSON.stringify({ job_id: jobId, status: "running" }) }],
        };
      }

      case "check_research_status": {
        const jobId = args?.job_id as string;
        const job = jobs.get(jobId);

        if (!job) {
          return {
            content: [{ type: "text", text: JSON.stringify({ error: "Job not found" }) }],
          };
        }

        const result: { job_id: string; status: string; error?: string } = {
          job_id: jobId,
          status: job.status
        };
        if (job.error) {
          result.error = job.error;
        }

        return {
          content: [{ type: "text", text: JSON.stringify(result) }],
        };
      }

      case "get_research_result": {
        const jobId = args?.job_id as string;
        const job = jobs.get(jobId);

        if (!job) {
          return {
            content: [{ type: "text", text: JSON.stringify({ error: "Job not found" }) }],
          };
        }

        if (job.status !== "complete") {
          return {
            content: [{ type: "text", text: JSON.stringify({ error: "Job not complete", status: job.status }) }],
          };
        }

        // If output_path was provided, result is on disk
        if (job.outputPath) {
          return {
            content: [{ type: "text", text: JSON.stringify({ saved_to: job.outputPath }) }],
          };
        }

        return {
          content: [{ type: "text", text: JSON.stringify({ result: job.result }) }],
        };
      }

      case "generate_articles": {
        const research = args?.research as string;
        const spec = args?.spec as ResearchSpec;

        // Generate with Pro and Flash in parallel
        const [proArticle, flashArticle] = await Promise.all([
          generateArticle(research, spec, config.gemini.models.pro),
          generateArticle(research, spec, config.gemini.models.flash),
        ]);

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              pro_article: proArticle,
              flash_article: flashArticle,
            }),
          }],
        };
      }

      case "generate_images": {
        const prompts = args?.prompts as ImagePrompt[];
        const outputDir = args?.output_dir as string;

        // Create output directory if it doesn't exist
        try {
          mkdirSync(outputDir, { recursive: true });
        } catch (e) {
          console.error(`Failed to create directory ${outputDir}:`, e);
        }

        const generatedImages: string[] = [];
        const errors: Array<{filename: string, error: string}> = [];

        // Generate each image
        for (const imagePrompt of prompts) {
          try {
            console.error(`Generating image: ${imagePrompt.filename}`);

            const contents = [{ text: imagePrompt.prompt }];

            const response = await client.models.generateContent({
              model: config.gemini.models.image,
              contents: contents,
              config: {
                responseModalities: ['TEXT', 'IMAGE'],
                imageConfig: {
                  aspectRatio: '16:9',
                  imageSize: '2K',
                },
              },
            });

            // Extract image from response parts
            if (response.candidates && response.candidates.length > 0) {
              for (const part of response.candidates[0].content.parts) {
                if (part.inlineData) {
                  const imageData = part.inlineData.data;
                  const buffer = Buffer.from(imageData, "base64");
                  const filepath = `${outputDir}/${imagePrompt.filename}`;
                  writeFileSync(filepath, buffer);
                  generatedImages.push(filepath);
                  console.error(`Saved image to: ${filepath}`);
                  break; // Only save first image
                }
              }
            }
          } catch (error: any) {
            const errorMsg = error?.message || String(error);
            console.error(`Failed to generate ${imagePrompt.filename}:`, errorMsg);
            errors.push({ filename: imagePrompt.filename, error: errorMsg });
          }
        }

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              status: "images_generated",
              images: generatedImages,
              total: prompts.length,
              successful: generatedImages.length,
              failed: errors.length,
              errors: errors,
            }),
          }],
        };
      }

      case "assemble_markdown": {
        const draft = args?.draft as string;
        const images = args?.images as string[];
        const format = (args?.format as string) || "blog";

        // Insert image references into markdown
        let assembled = draft;

        if (images.length > 0) {
          // Add hero image at top
          assembled = `![Hero Image](${images[0]})\n\n${assembled}`;

          // Add other images at section breaks
          const sections = assembled.split(/\n##\s/);
          if (sections.length > 1 && images.length > 1) {
            for (let i = 1; i < Math.min(sections.length, images.length); i++) {
              sections[i] = `![Section ${i}](${images[i]})\n\n## ${sections[i]}`;
            }
            assembled = sections.join("\n");
          }
        }

        return {
          content: [{
            type: "text",
            text: JSON.stringify({ assembled_markdown: assembled, format }),
          }],
        };
      }

      default:
        return {
          content: [{ type: "text", text: JSON.stringify({ error: `Unknown tool: ${name}` }) }],
        };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return {
      content: [{ type: "text", text: JSON.stringify({ error: message }) }],
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Deep Research Articles MCP server running on stdio");
}

main().catch(console.error);
