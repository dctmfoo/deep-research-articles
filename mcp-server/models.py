# File: models.py | Module: mcp-server
"""Type definitions for the Deep Research Articles MCP server."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResearchStatus(str, Enum):
    """Status of a research job."""
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Scope(BaseModel):
    """Research scope configuration."""
    breadth: str = Field(default="moderate", description="narrow|moderate|broad")
    depth: str = Field(default="detailed", description="overview|detailed|comprehensive")


class Audience(BaseModel):
    """Target audience configuration."""
    expertise_level: str = Field(default="intermediate", description="beginner|intermediate|expert")
    context: str = Field(default="", description="Why they need this research")


class OutputPreferences(BaseModel):
    """Output format preferences."""
    format: str = Field(default="blog", description="blog|x_article|linkedin")
    word_count: int = Field(default=2000, ge=500, le=5000)
    include_sources: bool = True
    include_images: bool = True


class Constraints(BaseModel):
    """Research constraints."""
    recency: str = Field(default="any", description="any|recent|last_year")
    geographic: str = Field(default="", description="Region if relevant")


class ResearchSpec(BaseModel):
    """Complete research specification from clarification phase."""
    research_goal: str = Field(..., description="Primary research objective")
    domain: str = Field(default="", description="Field/industry/topic area")
    scope: Scope = Field(default_factory=Scope)
    audience: Audience = Field(default_factory=Audience)
    focus_areas: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    constraints: Constraints = Field(default_factory=Constraints)
    output_preferences: OutputPreferences = Field(default_factory=OutputPreferences)
    clarification_notes: str = Field(default="", description="Additional context")


class ResearchJobInfo(BaseModel):
    """Information about a running research job."""
    job_id: str
    interaction_id: str
    started_at: datetime
    spec: ResearchSpec


class ResearchStartResponse(BaseModel):
    """Response from starting deep research."""
    job_id: str
    status: str = "started"
    estimated_time_seconds: int = 600


class ResearchStatusResponse(BaseModel):
    """Response from checking research status."""
    status: ResearchStatus
    progress: int = Field(ge=0, le=100)
    message: str = ""


class ResearchResultSource(BaseModel):
    """A source from the research."""
    title: str
    url: str


class ResearchResultMetadata(BaseModel):
    """Metadata about the research result."""
    duration_seconds: float
    sources_analyzed: int


class ResearchResult(BaseModel):
    """Complete research result."""
    report: str
    sources: list[ResearchResultSource] = Field(default_factory=list)
    metadata: ResearchResultMetadata


class ArticleGenerationResult(BaseModel):
    """Result from parallel article generation."""
    pro: str = Field(..., description="Article from Gemini Pro")
    flash: str = Field(..., description="Article from Gemini Flash")


class ImagePrompt(BaseModel):
    """A prompt for image generation."""
    description: str = Field(..., description="Full descriptive prompt")
    style: str = Field(default="photorealistic", description="Art style")
    quality_modifiers: list[str] = Field(default_factory=lambda: ["high-quality", "detailed"])
    aspect_ratio: str = Field(default="16:9")
    purpose: str = Field(default="visual", description="header|diagram|visual|infographic")


class ImageGenerationResult(BaseModel):
    """Result from image generation."""
    paths: list[str] = Field(default_factory=list, description="Paths to generated images")


class MarkdownMetadata(BaseModel):
    """Metadata for the assembled markdown."""
    title: str
    description: str
    word_count: int
    tags: list[str] = Field(default_factory=list)


class MarkdownAssemblyResult(BaseModel):
    """Result from markdown assembly."""
    markdown: str
    metadata: MarkdownMetadata
