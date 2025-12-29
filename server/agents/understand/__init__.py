"""
Understand Agent for Knowledge Forge.

Implements the Socratic tutoring system using the Claude Agent SDK.
"""

from .agent import UnderstandAgent
from .phases import UnderstandPhase, UnderstandPhaseContext, UNDERSTAND_TRANSITIONS

__all__ = [
    "UnderstandAgent",
    "UnderstandPhase",
    "UnderstandPhaseContext",
    "UNDERSTAND_TRANSITIONS",
]
