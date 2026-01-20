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
interface ResearchSpec {
  topic: string;
  intent?: string;
  audience?: string;
  depth?: string;
  format?: string;
  stance?: string;
  angle?: string;
  word_count?: number;
}

interface ResearchJob {
  id: string;
  status: "pending" | "running" | "complete" | "failed";
  result?: string;
  error?: string;
  startedAt: Date;
  interactionId?: string;
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
    // Build research query
    const query = `${spec.topic}. Focus: ${spec.depth || "detailed"} analysis for ${spec.audience || "general public"}. Stance: ${spec.stance || "balanced"}.`;

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

        job.result = report;
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
  const wordCount = spec.word_count || 2000;
  const format = spec.format || "blog";

  const prompt = `Based on the following research, write a ${format} article of approximately ${wordCount} words.

Research:
${research}

Requirements:
- Target audience: ${spec.audience || "general public"}
- Tone: ${spec.stance || "balanced"}
- Focus angle: ${spec.angle || "general"}
- Format: ${format}

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
      description: "Start an async deep research job on a topic",
      inputSchema: {
        type: "object",
        properties: {
          spec: {
            type: "object",
            description: "Research specification from clarification phase",
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
        const jobId = generateId();

        // Create job
        const job: ResearchJob = {
          id: jobId,
          status: "running",
          startedAt: new Date(),
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

        // Generate each image
        for (const imagePrompt of prompts) {
          try {
            console.error(`Generating image: ${imagePrompt.filename}`);

            const response = await client.models.generateImages({
              model: config.gemini.models.image,
              prompt: imagePrompt.prompt,
              config: {
                numberOfImages: 1,
              },
            });

            if (response.generatedImages && response.generatedImages.length > 0) {
              const imgBytes = response.generatedImages[0].image.imageBytes;
              const buffer = Buffer.from(imgBytes, "base64");
              const filepath = `${outputDir}/${imagePrompt.filename}`;
              writeFileSync(filepath, buffer);
              generatedImages.push(filepath);
              console.error(`Saved image to: ${filepath}`);
            }
          } catch (error) {
            console.error(`Failed to generate ${imagePrompt.filename}:`, error);
            // Continue with other images even if one fails
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
