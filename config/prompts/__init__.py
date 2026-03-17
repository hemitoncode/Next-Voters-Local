"""Agent system prompts."""

from config.prompts.legislation_finder import legislation_finder_sys_prompt
from config.prompts.note_taker import note_taker_sys_prompt
from config.prompts.reliability_judgment import reliability_judgment_prompt
from config.prompts.reflection import reflection_prompt
from config.prompts.writer import writer_sys_prompt
from config.prompts.political_commentary import political_commentry_sys_prompt

__all__ = [
    "legislation_finder_sys_prompt",
    "note_taker_sys_prompt",
    "reliability_judgment_prompt",
    "reflection_prompt",
    "writer_sys_prompt",
    "political_commentry_sys_prompt",
]
