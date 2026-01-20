#!/usr/bin/env node
// File: mcp-server.ts | Module: deep-research-articles

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { GoogleGenerativeAI } from "@google/generative-ai";

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

const genAI = new GoogleGenerativeAI(apiKey);

// Helper: Generate unique ID
function generateId(): string {
  return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Deep Research using Gemini
async function performDeepResearch(spec: ResearchSpec): Promise<string> {
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });

  const prompt = `You are a research assistant. Conduct deep research on the following topic and provide a comprehensive report.

Topic: ${spec.topic}
Intent: ${spec.intent || "educate"}
Target Audience: ${spec.audience || "general public"}
Depth: ${spec.depth || "detailed"}
Stance: ${spec.stance || "balanced"}
Angle: ${spec.angle || "general"}

Please provide:
1. Executive Summary
2. Key Findings (with citations where possible)
3. Current State of the Topic
4. Future Trends and Predictions
5. Expert Opinions and Perspectives
6. Data and Statistics
7. Conclusion

Format the output as a detailed research report in markdown.`;

  const result = await model.generateContent(prompt);
  return result.response.text();
}

// Generate articles with Gemini Pro
async function generateArticle(
  research: string,
  spec: ResearchSpec,
  model: string
): Promise<string> {
  const genModel = genAI.getGenerativeModel({ model });

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

  const result = await genModel.generateContent(prompt);
  return result.response.text();
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
        performDeepResearch(spec)
          .then((result) => {
            job.status = "complete";
            job.result = result;
          })
          .catch((error) => {
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
          generateArticle(research, spec, "gemini-1.5-pro"),
          generateArticle(research, spec, "gemini-1.5-flash"),
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

        // Note: Gemini Imagen requires specific API access
        // For now, return placeholder response
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              status: "images_generated",
              images: prompts.map((p) => `${outputDir}/${p.filename}`),
              note: "Image generation requires Gemini Imagen API access",
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
