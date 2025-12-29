"""
Research Agent for Knowledge Forge.

Implements the deep research pipeline:
DECOMPOSE → ANSWER → RISE_ABOVE → EXPAND → COMPLETE
"""

from .agent import ResearchAgent
from .phases import ResearchPhase, ResearchPhaseContext

__all__ = [
    "ResearchAgent",
    "ResearchPhase",
    "ResearchPhaseContext",
]
