"""Shared Pydantic models used to structure LLM responses."""

from typing import Optional

from pydantic import BaseModel, Field


class ReflectionEntry(BaseModel):
    """Structured reflection produced by the reflection tool."""

    reflection: Optional[str] = Field(
        default=None,
        description="Based on the current conversation that you have had, build a complete, but succinct reflection to create enriched context for agent",
    )
    gaps_identified: list[str] = Field(
        default_factory=list,
        description="Information gaps or missing context that needs to be addressed",
    )
    next_action: Optional[str] = Field(
        default=None,
        description="Specific action planned for the next iteration (e.g., search query, tool to use)",
    )


class LegislativeEvent(BaseModel):
    """A legislative event extracted from search results."""

    title: str = Field(description="Event title (e.g. 'City Council Meeting — Zoning Vote')")
    description: Optional[str] = Field(
        default=None, description="Brief description of what will happen at this event"
    )
    start_date: str = Field(
        description="Start date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)"
    )
    end_date: Optional[str] = Field(
        default=None, description="End date/time in ISO 8601 format"
    )
    location: Optional[str] = Field(
        default=None, description="Physical or virtual location of the event"
    )
    source_url: Optional[str] = Field(
        default=None, description="URL where this event was found"
    )


class WriterOutput(BaseModel):
    """Structured reflection output produced by the reflection tool."""

    title: Optional[str] = Field(
        default=None, description="Title of the written content"
    )
    body: Optional[str] = Field(
        default=None,
        description="Main written content. They should be in bullet-point format.",
    )
    summary: Optional[str] = Field(
        default=None, description="Brief summary of the content"
    )
